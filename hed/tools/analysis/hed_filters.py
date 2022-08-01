from hed.models import HedOps


class HedFilter(HedOps):
    def __init__(self, filter_name):
        super().__init__()
        self.filter_name = filter_name


class RemoveFilter(HedFilter):

    def __init__(self, tag_name, remove_group=True):
        super().__init__("remove_filter")
        self.tag_name = tag_name
        self.remove_group = remove_group

    def __get_string_funcs__(self, **kwargs):
        string_funcs = []
        string_funcs.append(self.remove_tags)
        return string_funcs

    def __get_tag_funcs__(self, **kwargs):
        return []

    def remove_tags(self, hed_string):
        remove_tuples = hed_string.find_tags([self.tag_name], recursive=True, include_groups=2)
        if self.remove_group:
            remove_list = [tuple[1] for tuple in remove_tuples]
        else:
            remove_list = [tuple[0] for tuple in remove_tuples]
        hed_string.remove(remove_list)


class HedFilters(HedOps):

    def __init__(self, filters):
        super().__init__()
        self._filters = filters
        self._onsets = {}

    def __get_tag_funcs__(self, **kwargs):
        tag_funcs = []
        # allow_placeholders = kwargs.get("allow_placeholders")
        # check_for_warnings = kwargs.get("check_for_warnings")
        # string_funcs.append(self._tag_validator.run_hed_string_validators)
        # string_funcs.append(
        #     partial(HedString.convert_to_canonical_forms, hed_schema=self._hed_schema))
        # string_funcs.append(partial(self._validate_individual_tags_in_hed_string,
        #                             allow_placeholders=allow_placeholders,
        #                             check_for_warnings=check_for_warnings))
        return tag_funcs

    def __get_string_funcs__(self, **kwargs):
        string_funcs = []
        string_funcs.append
        # check_for_warnings = kwargs.get("check_for_warnings")
        # string_funcs = [partial(self._validate_tags_in_hed_string, check_for_warnings=check_for_warnings),
        #                 self._validate_groups_in_hed_string]
        return string_funcs
