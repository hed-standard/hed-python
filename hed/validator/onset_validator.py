from hed.models.model_constants import DefTagNames
from hed.models.hed_group import HedGroup
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import OnsetErrors


class OnsetValidator:
    """ Validates onset/offset pairs. """

    def __init__(self, def_dict, run_full_onset_checks=True):
        self._defs = def_dict
        self._onsets = {}
        self._run_full_onset_checks = run_full_onset_checks

    def validate_onset_offset(self, hed_string_obj):
        """ Validate onset/offset

        Parameters:
            hed_string_obj (HedString): The hed string to check.

        Returns:
            list: A list of issues found in validating onsets (i.e., out of order onsets, unknown def names).
        """
        onset_issues = []
        for found_onset, found_group in self._find_onset_tags(hed_string_obj):
            if not found_onset:
                return []

            def_tags = found_group.find_def_tags()
            if not def_tags:
                onset_issues += ErrorHandler.format_error(OnsetErrors.ONSET_NO_DEF_TAG_FOUND, found_onset)
                continue

            if len(def_tags) > 1:
                onset_issues += ErrorHandler.format_error(OnsetErrors.ONSET_TOO_MANY_DEFS,
                                                          tag=def_tags[0][0],
                                                          tag_list=[tag[0] for tag in def_tags[1:]])
                continue

            # Get all children but def group and onset/offset, then validate #/type of children.
            def_tag, def_group, _ = def_tags[0]
            if def_group is None:
                def_group = def_tag
            children = [child for child in found_group.children if
                        def_group is not child and found_onset is not child]
            max_children = 1
            if found_onset.short_base_tag == DefTagNames.OFFSET_ORG_KEY:
                max_children = 0
            if len(children) > max_children:
                onset_issues += ErrorHandler.format_error(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS,
                                                          def_tag,
                                                          found_group.children)
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
        return hed_string_obj.find_top_level_tags(anchor_tags=DefTagNames.TEMPORAL_KEYS)

    def _handle_onset_or_offset(self, def_tag, onset_offset_tag):
        is_onset = onset_offset_tag.short_base_tag == DefTagNames.ONSET_ORG_KEY
        full_def_name = def_name = def_tag.extension
        placeholder = None
        found_slash = def_name.find("/")
        if found_slash != -1:
            placeholder = def_name[found_slash + 1:]
            def_name = def_name[:found_slash]

        def_entry = self._defs.get(def_name)
        if def_entry is None:
            return ErrorHandler.format_error(OnsetErrors.ONSET_DEF_UNMATCHED, tag=def_tag)
        if bool(def_entry.takes_value) != bool(placeholder):
            return ErrorHandler.format_error(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=def_tag,
                                             has_placeholder=bool(def_entry.takes_value))

        if self._run_full_onset_checks:
            if is_onset:
                # onset can never fail as it implies an offset
                self._onsets[full_def_name.lower()] = full_def_name
            else:
                is_offset = onset_offset_tag.short_base_tag == DefTagNames.OFFSET_ORG_KEY
                if full_def_name.lower() not in self._onsets:
                    if is_offset:
                        return ErrorHandler.format_error(OnsetErrors.OFFSET_BEFORE_ONSET, tag=def_tag)
                    else:
                        return ErrorHandler.format_error(OnsetErrors.INSET_BEFORE_ONSET, tag=def_tag)
                elif is_offset:
                    del self._onsets[full_def_name.lower()]

        return []
