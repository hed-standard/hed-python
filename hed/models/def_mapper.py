from hed.models.hed_string import HedString
from hed.models.hed_tag import HedTag
from hed.models.def_dict import DefDict
from hed.models.model_constants import DefTagNames
from hed.errors.error_types import ValidationErrors
from hed.errors.error_reporter import ErrorHandler
from hed.models.hed_ops import HedOps


class DefinitionMapper(HedOps):
    """ Class for handling definitions in hed strings.

    Notes:
       The class provides string funcs but no tag funcs when extending HedOps.
       The class is responsible for gathering and removing definitions.
       The class also replaces labels in hed strings with the gathered definitions.

    """

    def __init__(self, def_dicts=None):
        """ Initialize mapper for definitions in hed strings to fill them in with their values.

        Args:
            def_dicts (list): DefDicts containing the definitions this mapper should initialize with.

        Notes:
            More definitions can be added later.

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
        """ Get the definition entry for the definition name.

        Args:
            def_name (str):  Name of the definition to retrieve.

        Returns:
            DefEntry:  Definition entry for the requested definition.

        """

        return self._gathered_defs.get(def_name.lower())

    def clear_temporary_definitions(self):
        """ Remove any previously added temporary definitions. """
        for def_name in self._temporary_def_names:
            del self._gathered_defs[def_name]
        self._temporary_def_names = set()

    def add_definitions_from_string_as_temp(self, hed_string_obj):
        """ Add any definitions found in the hed string to this mapper as temporary definitions.

        Args:
            hed_string_obj (HedString):  Hed string object to search for definitions

        Returns:
            list:  List of issues due to invalid definitions found in this string. Each issue is a dictionary.

        """
        this_string_def_dict = DefDict()
        validation_issues = this_string_def_dict.check_for_definitions(hed_string_obj)
        self.add_definitions(this_string_def_dict, add_as_temp=True)
        return validation_issues

    def add_definitions(self, def_dicts, add_as_temp=False):
        """ Add the definitions found in the given definition dictionaries to this mapper.

        Args:
            def_dicts (list or DefDict): DefDict or list of DefDicts whose definitions should be added.
            add_as_temp (bool):          If true, mark these new definitions as temporary (easily purged).

        """
        if not isinstance(def_dicts, list):
            def_dicts = [def_dicts]
        for def_dict in def_dicts:
            if isinstance(def_dict, DefDict):
                self._add_definitions_from_dict(def_dict, add_as_temp)
            else:
                print(f"Invalid input type '{type(def_dict)} passed to DefinitionMapper.  Skipping.")

    def _add_definitions_from_dict(self, def_dict, add_as_temp=False):
        """ Add the definitions found in the given definition dictionary to this mapper.

         Args:
             def_dict (DefDict): DefDict whose definitions should be added.
             add_as_temp (bool): If true, mark these new definitions as temporary (easily purged).

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
        """ Validate Def and Def-expand tags, and optionally expands or shrinks them.

        Args:
            hed_string_obj (HedString): The hed string to process.
            expand_defs (bool): If true, convert def tags to def-expand tag groups that include definition content.
            shrink_defs (bool): If True, replace all def-expand groups with corresponding def tags.

        Returns:
            list: Issues found related to validating defs. Each issue is a dictionary.

        Notes:
            Usually issues are mismatched placeholders or a missing definition.
            The expand_defs and shrink_defs cannot both be True.

        """

        # First see if the "def" is found at all.  This covers def and def-expand.
        hed_string_lower = hed_string_obj.lower()
        if self._label_tag_name not in hed_string_lower:
            return []

        def_issues = []
        # We need to check for labels to expand in ALL groups
        for def_tag, def_expand_group, def_group in hed_string_obj.find_def_tags(recursive=True):
            def_contents = self._get_definition_contents(def_tag, def_expand_group, def_issues)
            if def_expand_group is def_tag:
                if def_contents is not None and expand_defs:
                    def_tag.short_base_tag = DefTagNames.DEF_EXPAND_ORG_KEY
                    def_group.replace_tag(def_tag, def_contents)
            else:
                if def_contents is not None and shrink_defs:
                    def_tag.short_base_tag = DefTagNames.DEF_ORG_KEY
                    def_group.replace_tag(def_expand_group, def_tag)

        return def_issues

    def expand_and_remove_definitions(self, hed_string_obj, check_for_definitions=False, expand_defs=True,
                                      shrink_defs=False, remove_definitions=True):
        """ Validate any Definition tags and remove any definitions found in the given hed string.

        Args:
            hed_string_obj (HedString): The string to search for definitions.
            check_for_definitions  (bool): If True, this will first check the hed string for any definitions.
            expand_defs (bool):        If True, replace Def tags to Def-expand tag groups.
            shrink_defs (bool):        If True, replace Def-expand groups with Def tags.
            remove_definitions (bool): If true, this will remove all Definition tag groups.

        Returns:
            def_issues (list): A list of issues for definition-related tags in this string. Each issue is a dictionary.

        Notes:
            The check_for_definitions is mainly used for individual HedStrings in isolation.

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

    def _get_definition_contents(self, def_tag, def_expand_group, def_issues):
        """ Check for issues with expanding a tag from Def to a Def-expand tag group and return the expanded tag group.

        Args:
            def_tag (HedTag): Source hed tag that may be a Def or Def-expand tag.
            def_expand_group (HedGroup or HedTag):
            Source group for this def-expand tag.  Same as def_tag if this is not a def-expand tag.
        def_issues : [{}]
            List of issues to append any new issues to

        Returns:
            def_contents: [HedTag or HedGroup]
            The contents to replace the previous def-tag with.
        """
        # todo: This check could be removed for optimizing
        if def_tag.short_base_tag.lower() == DefTagNames.DEF_EXPAND_KEY or \
                def_tag.short_base_tag.lower() == DefTagNames.DEF_KEY:
            is_label_tag = def_tag.extension_or_value_portion
            placeholder = None
            found_slash = is_label_tag.find("/")
            if found_slash != -1:
                placeholder = is_label_tag[found_slash + 1:]
                is_label_tag = is_label_tag[:found_slash]

            label_tag_lower = is_label_tag.lower()
            def_entry = self._gathered_defs.get(label_tag_lower)
            if def_entry is None:
                def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_UNMATCHED, tag=def_tag)
            else:
                def_tag_name, def_contents = def_entry.get_definition(def_tag, placeholder_value=placeholder)
                if def_tag_name:
                    if def_expand_group is not def_tag and def_expand_group != def_contents:
                        def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_EXPAND_INVALID,
                                                                tag=def_tag, actual_def=def_contents,
                                                                found_def=def_expand_group)
                        return None
                    return def_contents
                elif def_entry.takes_value:
                    def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_VALUE_MISSING, tag=def_tag)
                else:
                    def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_VALUE_EXTRA, tag=def_tag)
            pass
        else:
            raise ValueError("Internal error in DefinitionMapper")
        return None

    def __get_string_funcs__(self, **kwargs):
        """ String funcs for processing definitions. """
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
