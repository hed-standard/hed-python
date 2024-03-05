from hed.models.model_constants import DefTagNames
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import TemporalErrors


class OnsetValidator:
    """ Validates onset/offset pairs. """

    def __init__(self):
        self._onsets = {}

    def validate_temporal_relations(self, hed_string_obj):
        """ Validate onset/offset/inset tag relations

        Parameters:
            hed_string_obj (HedString): The hed string to check.

        Returns:
            list: A list of issues found in validating onsets (i.e., out of order onsets, repeated def names).
        """
        onset_issues = []
        used_def_names = set()
        for temporal_tag, temporal_group in hed_string_obj.find_top_level_tags(anchor_tags=DefTagNames.TEMPORAL_KEYS):
            if not temporal_tag:
                return []

            def_tags = temporal_group.find_def_tags(include_groups=0)
            if not def_tags:
                continue

            def_tag = def_tags[0]
            def_name = def_tag.extension
            if def_name.lower() in used_def_names:
                onset_issues += ErrorHandler.format_error(TemporalErrors.ONSET_SAME_DEFS_ONE_ROW, tag=temporal_tag,
                                                          def_name=def_name)
                continue

            used_def_names.add(def_tag.extension.lower())

            # At this point we have either an onset or offset tag and it's name
            onset_issues += self._handle_onset_or_offset(def_tag, temporal_tag)

        return onset_issues

    def validate_duration_tags(self, hed_string_obj):
        """ Validate Duration/Delay tag groups

        Parameters:
            hed_string_obj (HedString): The hed string to check.

        Returns:
            list: A list of issues found in validating durations (i.e., extra tags or groups present, or a group missing)
        """
        duration_issues = []
        for tags, group in hed_string_obj.find_top_level_tags_grouped(anchor_tags=DefTagNames.DURATION_KEYS):
            # This implicitly validates the duration/delay tag, as they're the only two allowed in the same group
            # It should be impossible to have > 2 tags, but it's a good stopgap.
            if len(tags) != len(group.tags()) or len(group.tags()) > 2:
                for tag in group.tags():
                    if tag not in tags:
                        duration_issues += ErrorHandler.format_error(TemporalErrors.DURATION_HAS_OTHER_TAGS, tag=tag)
                continue
            if len(group.groups()) != 1:
                duration_issues += ErrorHandler.format_error(TemporalErrors.DURATION_WRONG_NUMBER_GROUPS,
                                                             tags[0],
                                                             hed_string_obj.groups())
                continue

        # Does anything else need verification here?
        #     That duration is positive?
        return duration_issues

    def _handle_onset_or_offset(self, def_tag, onset_offset_tag):
        is_onset = onset_offset_tag.short_base_tag == DefTagNames.ONSET_ORG_KEY
        full_def_name = def_tag.extension
        if is_onset:
            # onset can never fail as it implies an offset
            self._onsets[full_def_name.lower()] = full_def_name
        else:
            is_offset = onset_offset_tag.short_base_tag == DefTagNames.OFFSET_ORG_KEY
            if full_def_name.lower() not in self._onsets:
                if is_offset:
                    return ErrorHandler.format_error(TemporalErrors.OFFSET_BEFORE_ONSET, tag=def_tag)
                else:
                    return ErrorHandler.format_error(TemporalErrors.INSET_BEFORE_ONSET, tag=def_tag)
            elif is_offset:
                del self._onsets[full_def_name.lower()]

        return []

    @staticmethod
    def check_for_banned_tags(hed_string):
        """ Returns an issue for every tag found from the banned list

        Parameters:
            hed_string(HedString): the string to check

        Returns:
            list: The validation issues associated with the characters. Each issue is dictionary.
        """
        banned_tag_list = DefTagNames.ALL_TIME_KEYS
        issues = []
        for tag in hed_string.get_all_tags():
            if tag.short_base_tag.lower() in banned_tag_list:
                issues += ErrorHandler.format_error(TemporalErrors.HED_ONSET_WITH_NO_COLUMN, tag)
        return issues
