from hed.models.hed_string import HedString
from hed.models.def_dict import DefDict
from hed.models.model_constants import DefTagNames
from hed.errors.error_types import ValidationErrors
from hed.errors.error_reporter import ErrorHandler


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
        self._def_tag_name = DefTagNames.DEFINITION_KEY
        self._label_tag_name = DefTagNames.DEF_KEY

        if def_dicts:
            self.add_definitions(def_dicts)

    def get_def_entry(self, def_name):
        return self._gathered_defs.get(def_name.lower())

    def clear_temporary_definitions(self):
        """
            Removes any previously added temporary definitions

        Returns
        -------

        """
        for def_name in self._temporary_def_names:
            del self._gathered_defs[def_name]
        self._temporary_def_names = set()

    def add_definitions_from_string_as_temp(self, hed_string_obj):
        """
            Checks the given string and adds any definitions found to this mapper as temp.

        Parameters
        ----------
        hed_string_obj : HedString

        Returns
        -------
        issues_list: [{}]
            A list of issues related to definitions found
        """
        this_string_def_dict = DefDict()
        validation_issues = this_string_def_dict.check_for_definitions(hed_string_obj)
        self.add_definitions(this_string_def_dict, add_as_temp=True)
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

    def expand_def_tags(self, hed_string_obj, expand_defs=True):
        """Takes a given string and returns the hed string with all definitions removed, and all labels replaced

        Parameters
        ----------
        hed_string_obj : HedString
            The hed string to modify.
        expand_defs: bool
            If True, this will fully remove all definitions found and expand all def tags to def-expand tags
        Returns
        -------
        def_issues: []
            Issues found related to expanding definitions.  Usually mismatched placeholders, or a missing definition.
        """
        # First see if the word definition or dLabel is found at all.  Just move on if not.
        hed_string_lower = hed_string_obj.lower()
        if self._label_tag_name not in hed_string_lower:
            return []

        def_issues = []
        # We need to check for labels to expand in ALL groups
        for tag_group, is_top_level in hed_string_obj.get_all_groups(also_return_depth=True):
            def_tags_found = []
            for tag in tag_group.tags():
                if tag.short_base_tag.lower() == DefTagNames.DEF_KEY:
                    def_tags_found.append(tag)

            for def_tag in def_tags_found:
                def_tag_name, def_contents = self._get_def_expand_tag(def_tag, def_issues)
                if def_tag_name and expand_defs:
                    def_tag.short_base_tag = def_tag_name
                    tag_group.replace_tag(def_tag, def_contents)

        return def_issues

    def expand_and_remove_definitions(self, hed_string_obj, check_for_definitions=False, expand_defs=True):
        """
            Validate any def tags and remove any definitions found in the given hed string.

        Parameters
        ----------
        hed_string_obj : HedString
            The string to validate.
        check_for_definitions : bool
            If True, this will first check the hed string for any definitions.  This mostly applies to validate
                hed strings individually, not as part of a file.
        expand_defs : bool
            If true, convert all located def tags to def-expand tags, and plug in the definitions.

        Returns
        -------
        def_issues: [{}]
            The issues found with def tags.
        """
        def_issues = []
        if check_for_definitions:
            def_issues += self.add_definitions_from_string_as_temp(hed_string_obj)
        def_issues += self.expand_def_tags(hed_string_obj, expand_defs=expand_defs)
        def_issues += hed_string_obj.remove_definitions()
        if check_for_definitions:
            self.clear_temporary_definitions()

        return def_issues

    def _get_def_expand_tag(self, original_tag, def_issues):
        """
            Checks for issues with expanding a tag from def to def-expand, and returns the expanded tag.

        Parameters
        ----------
        original_tag : HedTag
            Source hed tag that may be a Def tag.
        def_issues : [{}]
            List of issues to append any new issues to

        Returns
        -------
        def_tag_name: str
            The def-expand tag matching this def tag, if any
        def_contents: [HedTag or HedGroup]
            The contents to replace the previous def-tag with.
        """
        if original_tag.short_base_tag.lower() == DefTagNames.DEF_KEY:
            is_label_tag = original_tag.extension_or_value_portion
            placeholder = None
            found_slash = is_label_tag.find("/")
            if found_slash != -1:
                placeholder = is_label_tag[found_slash + 1:]
                is_label_tag = is_label_tag[:found_slash]

            label_tag_lower = is_label_tag.lower()
            def_entry = self._gathered_defs.get(label_tag_lower)
            if def_entry is None:
                def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_UNMATCHED, tag=original_tag)
            else:
                def_tag_name, def_contents = def_entry.get_definition(original_tag, placeholder_value=placeholder)
                if def_tag_name:
                    return DefTagNames.DEF_EXPAND_ORG_KEY, def_contents
                elif def_entry.takes_value:
                    def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_VALUE_MISSING, tag=original_tag)
                else:
                    def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_VALUE_EXTRA, tag=original_tag)
        return None, None

    def __get_string_ops__(self, **kwargs):
        string_validators = []
        expand_defs = kwargs.get("expand_defs")
        check_for_definitions = kwargs.get("check_for_definitions")
        from functools import partial
        string_validators.append(partial(self.expand_and_remove_definitions,
                                         check_for_definitions=check_for_definitions,
                                         expand_defs=expand_defs))
        return string_validators

    def __get_tag_ops__(self, **kwargs):
        return []
