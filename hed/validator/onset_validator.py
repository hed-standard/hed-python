""" Validates the onset/offset conditions. """

from hed.models.model_constants import DefTagNames
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import TemporalErrors


class OnsetValidator:
    """ Validates onset/offset pairs. """

    def __init__(self):
        self._onsets = {}

    def validate_temporal_relations(self, hed_string_obj) -> list[dict]:
        """ Validate onset/offset/inset tag relations

        Parameters:
            hed_string_obj (HedString): The HED string to check.

        Returns:
            list[dict]: A list of issues found in validating onsets (i.e., out of order onsets, repeated def names).
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
            if def_name.casefold() in used_def_names:
                onset_issues += ErrorHandler.format_error(TemporalErrors.ONSET_SAME_DEFS_ONE_ROW, tag=temporal_tag,
                                                          def_name=def_name)
                continue

            used_def_names.add(def_tag.extension.casefold())

            # At this point we have either an onset or offset tag and it's name
            onset_issues += self._handle_onset_or_offset(def_tag, temporal_tag)

        return onset_issues

    def _handle_onset_or_offset(self, def_tag, onset_offset_tag):
        is_onset = onset_offset_tag.short_base_tag == DefTagNames.ONSET_KEY
        full_def_name = def_tag.extension
        if is_onset:
            # onset can never fail as it implies an offset
            self._onsets[full_def_name.casefold()] = full_def_name
        else:
            is_offset = onset_offset_tag.short_base_tag == DefTagNames.OFFSET_KEY
            if full_def_name.casefold() not in self._onsets:
                if is_offset:
                    return ErrorHandler.format_error(TemporalErrors.OFFSET_BEFORE_ONSET, tag=def_tag)
                else:
                    return ErrorHandler.format_error(TemporalErrors.INSET_BEFORE_ONSET, tag=def_tag)
            elif is_offset:
                del self._onsets[full_def_name.casefold()]

        return []

    @staticmethod
    def check_for_banned_tags(hed_string) -> list[dict]:
        """ Returns an issue for every tag found from the banned list (for files without onset column).

        Parameters:
            hed_string (HedString): The string to check.

        Returns:
            list[dict]: The validation issues associated with the characters. Each issue is dictionary.
        """
        banned_tag_list = DefTagNames.TIMELINE_KEYS
        issues = []
        for tag in hed_string.get_all_tags():
            if tag.short_base_tag in banned_tag_list:
                issues += ErrorHandler.format_error(TemporalErrors.TEMPORAL_TAG_NO_TIME, tag)
        return issues
