from hed.models.hed_string import HedString
from hed.models.def_dict import DefDict, DefTagNames
from hed.errors.error_types import ValidationErrors


class DefinitionMapper:
    """Class responsible for gathering/removing definitions from hed strings,
        and also replacing labels in hed strings with the gathered definitions."""

    def __init__(self, def_dicts=None):
        """
        Class to handle mapping definitions from hed strings to fill them in with their values.

        Parameters
        ----------
        def_dicts: [DefDict]
            DefDicts containing all the definitions this mapper should initialize with.  More can be added later.
        """
        self._gathered_defs = {}
        # List of def names we want to be able to quickly purge.
        self._temporary_def_names = set()
        self._def_tag_name = DefTagNames.DEFINITION_KEY.lower()
        self._label_tag_name = DefTagNames.DEF_KEY.lower()

        if def_dicts:
            self.add_definitions(def_dicts)

    def clear_temporary_definitions(self):
        """
            Removes any previously added temporary definitions

        Returns
        -------

        """
        for def_name in self._temporary_def_names:
            del self._gathered_defs[def_name]
        self._temporary_def_names = set()

    def add_definitions_from_string_as_temp(self, hed_string_obj, error_handler):
        """
            Checks the given string and adds any definitions found to this mapper as temp.

        Parameters
        ----------
        hed_string_obj : HedString
        error_handler : ErrorHandler

        Returns
        -------
        issues_list: [{}]
            A list of issues related to definitions found
        """
        this_string_def_dict = DefDict()
        this_string_def_dict.check_for_definitions(hed_string_obj, error_handler)
        self.add_definitions(this_string_def_dict, add_as_temp=True)
        validation_issues = this_string_def_dict.get_definition_issues()
        return validation_issues

    def add_definitions(self, def_dicts, add_as_temp=False):
        """
        Adds all definitions found in hed strings in the given input

        Parameters
        ----------
        def_dicts : [] or DefDict
        add_as_temp: bool
            If true, mark these new definitions as temporary(easily purged)
        """
        if not isinstance(def_dicts, list):
            def_dicts = [def_dicts]
        for def_dict in def_dicts:
            if isinstance(def_dict, DefDict):
                self._add_definitions_from_dict(def_dict, add_as_temp)
            else:
                print(f"Invalid input type '{type(def_dict)} passed to DefinitionMapper.  Skipping.")

    def _add_definitions_from_dict(self, def_dict, add_as_temp=False):
        """
            Gather definitions from a single def group and add it to the mapper

        Parameters
        ----------
        def_dict : DefDict

        Returns
        -------
        """
        for def_tag, def_value in def_dict:
            if def_tag in self._gathered_defs:
                # todo: add detection here possibly.  Right now the first definition found is used.
                # This is a warning.  Errors from a duplicate definition in a single source will be reported
                # by DefDict
                print(f"WARNING: Duplicate definition found for '{def_tag}'.")
                continue
            self._gathered_defs[def_tag] = def_value
            if add_as_temp:
                self._temporary_def_names.add(def_tag)

    def replace_and_remove_tags(self, hed_string_obj, expand_defs=True, error_handler=None):
        """Takes a given string and returns the hed string with all definitions removed, and all labels replaced

        Parameters
        ----------
        hed_string_obj : HedString
            The hed string to modify.
        expand_defs: bool
            If True, this will fully remove all definitions found and expand all def tags to def-expand tags
        error_handler : ErrorHandler or None
            If one is passed, will format the issues list using it.
        Returns
        -------
        def_issues: []
            Issues found related to expanding definitions.  Usually mismatched placeholders, or a missing definition.
        """
        # First see if the word definition or dLabel is found at all.  Just move on if not.
        hed_string_lower = hed_string_obj.lower()
        if self._def_tag_name not in hed_string_lower and \
                self._label_tag_name not in hed_string_lower:
            return []

        remove_groups = []
        def_issue_params = []
        # We need to check for definitions to remove in ONLY the top level groups.
        # We need to check for labels to expand in ALL groups
        for tag_group, is_top_level in hed_string_obj.get_all_groups(also_return_depth=True):
            for tag in tag_group.tags():
                tag_as_string = str(tag)
                if is_top_level:
                    # This case should be fairly rare compared to expanding definitions.
                    is_def_tag = DefDict._check_tag_starts_with(tag_as_string, DefTagNames.DEFINITION_KEY)
                    if is_def_tag:
                        remove_groups.append(tag_group)
                        break

                is_label_tag = DefDict._check_tag_starts_with(tag_as_string, DefTagNames.DEF_KEY)
                if is_label_tag:
                    placeholder = None
                    found_slash = is_label_tag.find("/")
                    if found_slash != -1:
                        placeholder = is_label_tag[found_slash + 1:]
                        is_label_tag = is_label_tag[:found_slash]

                    label_tag_lower = is_label_tag.lower()
                    def_entry = self._gathered_defs.get(label_tag_lower)
                    if def_entry is None:
                        def_issue_params += [{"error_type": ValidationErrors.HED_DEF_UNMATCHED,
                                             "tag": tag}]
                        continue

                    def_tag_name, def_contents = def_entry.get_definition(tag, placeholder_value=placeholder)
                    if def_tag_name is None:
                        if def_entry.takes_value:
                            def_issue_params += [{"error_type": ValidationErrors.HED_DEF_VALUE_MISSING,
                                                 "tag": tag}]
                        else:
                            def_issue_params += [{"error_type": ValidationErrors.HED_DEF_VALUE_EXTRA,
                                                 "tag": tag}]
                        continue
                    if not expand_defs:
                        continue

                    tag.tag = def_tag_name
                    tag_group.replace_tag(tag, def_contents)
                    continue

        if remove_groups:
            if expand_defs:
                hed_string_obj.remove_groups(remove_groups)
            else:
                for group in remove_groups:
                    group.replace_placeholder("PLACEHOLDER_PLACEHOLDER")

        if error_handler:
            return error_handler.format_error_list(def_issue_params)

        return def_issue_params
