from hed.models.model_constants import DefTagNames
from hed.models.hed_group import HedGroup
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import OnsetErrors


class OnsetValidator:
    """ Validates onset/offset pairs. """

    def __init__(self):
        self._onsets = {}

    def validate_temporal_relations(self, hed_string_obj):
        """ Validate onset/offset/inset tag relations

        Parameters:
            hed_string_obj (HedString): The hed string to check.

        Returns:
            list: A list of issues found in validating onsets (i.e., out of order onsets, unknown def names).
        """
        onset_issues = []
        used_def_names = set()
        for temporal_tag, temporal_group in self._find_temporal_tags(hed_string_obj):
            if not temporal_tag:
                return []

            def_tags = temporal_group.find_def_tags(include_groups=0)
            if not def_tags:
                continue

            def_tag = def_tags[0]
            def_name = def_tag.extension
            if def_name.lower() in used_def_names:
                onset_issues += ErrorHandler.format_error(OnsetErrors.ONSET_SAME_DEFS_ONE_ROW, tag=temporal_tag,
                                                          def_name=def_name)
                continue

            used_def_names.add(def_tag.extension.lower())

            # At this point we have either an onset or offset tag and it's name
            onset_issues += self._handle_onset_or_offset(def_tag, temporal_tag)

        return onset_issues

    def _find_temporal_tags(self, hed_string_obj):
        return hed_string_obj.find_top_level_tags(anchor_tags=DefTagNames.TEMPORAL_KEYS)

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
                    return ErrorHandler.format_error(OnsetErrors.OFFSET_BEFORE_ONSET, tag=def_tag)
                else:
                    return ErrorHandler.format_error(OnsetErrors.INSET_BEFORE_ONSET, tag=def_tag)
            elif is_offset:
                del self._onsets[full_def_name.lower()]

        return []
