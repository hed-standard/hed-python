from hed.models.hed_string import HedString
from hed.models.hed_tag import HedTag
from hed.models.def_dict import DefDict
from hed.models.model_constants import DefTagNames
from hed.errors.error_types import ValidationErrors
from hed.errors.error_reporter import ErrorHandler
from hed.models.hed_ops import HedOps


class DefinitionMapper(HedOps):
    """Class responsible removing definitions from hed strings,
        and also replacing labels in hed strings with the gathered definitions."""

    def __init__(self, def_dicts=None):
        """
        Class to handle mapping definitions from hed strings to fill them in with their values.

        Parameters
        ----------
        def_dicts: [DefDict]
            DefDicts containing all the definitions this mapper should initialize with.  More can be added later.
        """
        super().__init__()
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

    def expand_def_tags(self, hed_string_obj, expand_defs=True, shrink_defs=False):
        """Validates def and def-expand tags, and optionally expands or shrinks them.

        Parameters
        ----------
        hed_string_obj : HedString
            The hed string to modify.
        expand_defs: bool
            If true, convert all located def tags to def-expand tags, and plug in the definitions.
        shrink_defs: bool
            If True, this will shrink all def-expand groups to def tags
        Returns
        -------
        def_issues: []
            Issues found related to validating defs.  Usually mismatched placeholders, or a missing definition.
        """
        # First see if the "def" is found at all.  This covers def and def-expand.
        hed_string_lower = hed_string_obj.lower()
        if self._label_tag_name not in hed_string_lower:
            return []

        def_issues = []
        # We need to check for labels to expand in ALL groups
        for tag_group in hed_string_obj.get_all_groups():
            def_tags, def_expand_tags = self._find_def_tags(tag_group)

            for def_tag in def_tags:
                def_contents = self._get_definition_contents(def_tag, None, def_issues)
                if def_contents is not None and expand_defs:
                    def_tag.short_base_tag = DefTagNames.DEF_EXPAND_ORG_KEY
                    tag_group.replace_tag(def_tag, def_contents)
            for def_expand_tag, def_expand_group in def_expand_tags:
                def_contents = self._get_definition_contents(def_expand_tag, def_expand_group, def_issues)
                if def_contents is not None and shrink_defs:
                    def_expand_tag.short_base_tag = DefTagNames.DEF_ORG_KEY
                    tag_group.replace_tag(def_expand_group, def_expand_tag)

        return def_issues

    def _find_def_tags(self, group):
        def_tags = []
        def_expand_tags = []
        for child in group.get_direct_children():
            if isinstance(child, HedTag):
                if child.short_base_tag.lower() == DefTagNames.DEF_KEY:
                    def_tags.append(child)
            else:
                for tag in child.tags():
                    if tag.short_base_tag.lower() == DefTagNames.DEF_EXPAND_KEY:
                        def_expand_tags.append((tag, child))

        return def_tags, def_expand_tags

    def expand_and_remove_definitions(self, hed_string_obj, check_for_definitions=False, expand_defs=True,
                                      shrink_defs=False, remove_definitions=True):
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
        shrink_defs: bool
            If True, this will shrink all def-expand groups to def tags
        remove_definitions: bool
            If true, this will remove all definition tags found.
        Returns
        -------
        def_issues: [{}]
            The issues found with def tags.
        """
        def_issues = []
        if check_for_definitions:
            def_issues += self.add_definitions_from_string_as_temp(hed_string_obj)
        def_issues += self.expand_def_tags(hed_string_obj, expand_defs=expand_defs, shrink_defs=shrink_defs)
        if remove_definitions:
            def_issues += hed_string_obj.remove_definitions()
        if check_for_definitions:
            self.clear_temporary_definitions()

        return def_issues

    def _get_definition_contents(self, original_tag, def_expand_group, def_issues):
        """
            Checks for issues with expanding a tag from def to def-expand, and returns the expanded tag.

        Parameters
        ----------
        original_tag : HedTag
            Source hed tag that may be a Def-expand tag.
        def_expand_group: HedGroup or None
            Source group for this def-expand tag.  None if a def tag.
        def_issues : [{}]
            List of issues to append any new issues to

        Returns
        -------
        def_contents: [HedTag or HedGroup]
            The contents to replace the previous def-tag with.
        """
        # todo: This check could be removed for optimizing
        if original_tag.short_base_tag.lower() == DefTagNames.DEF_EXPAND_KEY or \
                original_tag.short_base_tag.lower() == DefTagNames.DEF_KEY:
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
                    if def_expand_group is not None and def_expand_group != def_contents:
                        def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_EXPAND_BAD,
                                                                tag=original_tag, actual_def=def_contents,
                                                                found_def=def_expand_group)
                        return None
                    return def_contents
                elif def_entry.takes_value:
                    def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_VALUE_MISSING, tag=original_tag)
                else:
                    def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_VALUE_EXTRA, tag=original_tag)
            pass
        else:
            raise ValueError("Internal error in DefinitionMapper")
        return None

    def __get_string_funcs__(self, **kwargs):
        string_funcs = []
        expand_defs = kwargs.get("expand_defs")
        shrink_defs = kwargs.get("shrink_defs")
        remove_definitions = kwargs.get("remove_definitions")
        check_for_definitions = kwargs.get("check_for_definitions")
        if shrink_defs and expand_defs:
            raise ValueError("Cannot pass both shrink_defs and expand_defs to DefinitionMapper")
        from functools import partial
        string_funcs.append(partial(self.expand_and_remove_definitions,
                                    check_for_definitions=check_for_definitions,
                                    expand_defs=expand_defs,
                                    shrink_defs=shrink_defs,
                                    remove_definitions=remove_definitions))
        return string_funcs

    def __get_tag_funcs__(self, **kwargs):
        return []
