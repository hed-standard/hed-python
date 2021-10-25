from hed.models.model_constants import DefTagNames
from hed.models.hed_group import HedTag, HedGroup
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import OnsetErrors


class OnsetMapper:
    """
        Validator responsible for matching onset offset pairs up
    """

    def __init__(self, def_mapper):
        self._def_mapper = def_mapper
        self._onsets = {}

    def check_for_onset_offset(self, hed_string_obj):
        """
            Checks for an onset or offset tag in the given string and adds it to the current context if found.
        Parameters
        ----------
        hed_string_obj : HedString
            The hed string to check.  Finds a maximum of one onset tag.

        Returns
        -------
        onset_issues: [{}]
            Issues found validating onsets.  Out of order onsets, unknown def names, etc.
        """
        onset_issues = []
        for found_onset, found_group in self._find_onset_tags(hed_string_obj):
            if not found_onset:
                return []

            def_tags, def_groups = self._find_def_tags(found_group)
            if not def_tags:
                onset_issues += ErrorHandler.format_error(OnsetErrors.ONSET_NO_DEF_TAG_FOUND, found_onset)
                continue

            if len(def_tags) > 1:
                onset_issues += ErrorHandler.format_error(OnsetErrors.ONSET_TOO_MANY_DEFS,
                                                          tag=def_tags[0],
                                                          tag_list=[tag for tag in def_tags[1:]])
                continue

            def_tag = def_tags[0]
            def_group = def_groups[0]
            children = [child for child in found_group.get_direct_children() if
                        def_group != child and found_onset != child]
            max_children = 1
            if found_onset.short_base_tag.lower() == DefTagNames.OFFSET_KEY:
                max_children = 0
            if len(children) > max_children:
                onset_issues += ErrorHandler.format_error(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS,
                                                          def_tag,
                                                          found_group.get_direct_children())
                continue

            if children:
                # Make this a loop if max_children can be > 1
                child = children[0]
                if not isinstance(child, HedGroup):
                    onset_issues += ErrorHandler.format_error(OnsetErrors.ONSET_TAG_OUTSIDE_OF_GROUP,
                                                              child,
                                                              def_tag)

            # At this point we have either an onset or offset tag and it's name
            onset_issues += self._handle_onset_or_offset(def_tag, found_onset)

        return onset_issues

    def _find_onset_tags(self, hed_string_obj):
        for group in hed_string_obj.groups():
            for tag in group.tags():
                if tag.short_base_tag.lower() == DefTagNames.ONSET_KEY \
                        or tag.short_base_tag.lower() == DefTagNames.OFFSET_KEY \
                        and not tag.extension_or_value_portion:
                    yield tag, group
                    # only return one onset tag per group
                    break

    def _find_def_tags(self, onset_group):
        def_tags = []
        def_groups = []
        for child in onset_group.get_direct_children():
            if isinstance(child, HedTag):
                if child.short_base_tag.lower() == DefTagNames.DEF_KEY:
                    def_tags.append(child)
                    def_groups.append(child)
            else:
                for tag in child.tags():
                    if tag.short_base_tag.lower() == DefTagNames.DEF_EXPAND_KEY:
                        def_tags.append(tag)
                        def_groups.append(child)

        return def_tags, def_groups

    def _handle_onset_or_offset(self, def_tag, onset_offset_tag):
        is_onset = onset_offset_tag.short_base_tag.lower() == DefTagNames.ONSET_KEY
        full_def_name = def_name = def_tag.extension_or_value_portion
        placeholder = None
        found_slash = def_name.find("/")
        if found_slash != -1:
            placeholder = def_name[found_slash + 1:]
            def_name = def_name[:found_slash]

        def_entry = self._def_mapper.get_def_entry(def_name)
        if def_entry is None:
            return ErrorHandler.format_error(OnsetErrors.ONSET_DEF_UNMATCHED, tag=def_tag)
        if bool(def_entry.takes_value) != bool(placeholder):
            return ErrorHandler.format_error(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=def_tag,
                                             has_placeholder=bool(def_entry.takes_value))

        if is_onset:
            # onset can never fail as it implies an offset
            self._onsets[full_def_name.lower()] = full_def_name
        else:
            if full_def_name.lower() not in self._onsets:
                return ErrorHandler.format_error(OnsetErrors.OFFSET_BEFORE_ONSET, tag=def_tag)
            else:
                del self._onsets[full_def_name.lower()]

        return []

    def __get_string_ops__(self, **kwargs):
        string_validators = []
        string_validators.append(self.check_for_onset_offset)
        return string_validators

    def __get_tag_ops__(self, **kwargs):
        return []
