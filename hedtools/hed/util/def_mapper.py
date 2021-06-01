from hed.util.hed_string import HedString
from hed.util.def_dict import DefDict, DefTagNames
from hed.util.error_types import ValidationErrors

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

        self._def_tag_name = DefTagNames.DEF_KEY.lower()
        self._label_tag_name = DefTagNames.DLABEL_KEY.lower()

        if def_dicts:
            self.add_definitions(def_dicts)

    def add_definitions(self, def_dicts):
        """
        Adds all definitions found in hed strings in the given input

        Parameters
        ----------
        def_dicts : [] or DefDict

        """
        if not isinstance(def_dicts, list):
            def_dicts = [def_dicts]
        for def_dict in def_dicts:
            if isinstance(def_dict, DefDict):
                self._add_definitions_from_group(def_dict)
            else:
                print(f"Invalid input type '{type(def_dict)} passed to DefinitionMapper.  Skipping.")

    def _add_definitions_from_group(self, def_dict):
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
                # This is a warning.  Errors from a duplicate definition in a single source will be reported
                # by DefDict
                print(f"WARNING: Duplicate definition found for '{def_tag}'.")
                continue
            self._gathered_defs[def_tag] = def_value

    def replace_and_remove_tags(self, hed_string_obj, expand_defs=True):
        """Takes a given string and returns the hed string with all definitions removed, and all labels replaced

        Parameters
        ----------
        hed_string_obj : HedString
            The hed string to modify.
        expand_defs: bool
            If False, this will still remove all definition/ tags, but will not expand label tags.
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
        def_issues = []
        for tag_group in hed_string_obj.get_all_groups():
            for tag in tag_group.tags():
                tag_as_string = str(tag)
                # This case should be fairly rare compared to expanding definitions.
                is_def_tag = DefinitionMapper._check_tag_starts_with(tag_as_string, DefTagNames.DEF_KEY)
                if is_def_tag:
                    remove_groups.append(tag_group)
                    break

                is_label_tag = DefinitionMapper._check_tag_starts_with(tag_as_string, DefTagNames.DLABEL_KEY)
                if is_label_tag:
                    placeholder = None
                    found_slash = is_label_tag.find("/")
                    if found_slash != -1:
                        placeholder = is_label_tag[found_slash + 1:]
                        is_label_tag = is_label_tag[:found_slash]

                    label_tag_lower = is_label_tag.lower()
                    def_entry = self._gathered_defs.get(label_tag_lower)
                    if def_entry is None:
                        def_issues += [{"error_type": ValidationErrors.HED_DEFINITION_UNMATCHED,
                                       "tag": is_label_tag}]
                        continue

                    def_contents = def_entry.get_definition(placeholder_value=placeholder)
                    if def_contents is None:
                        if def_entry.takes_value:
                            def_issues += [{"error_type": ValidationErrors.HED_DEFINITION_VALUE_MISSING,
                                           "tag": tag}]
                        else:
                            def_issues += [{"error_type": ValidationErrors.HED_DEFINITION_VALUE_EXTRA,
                                            "tag": tag}]
                        continue
                    if not expand_defs:
                       continue
                    tag_group.replace_tag(tag, def_contents)
                    continue

        if remove_groups:
            hed_string_obj.remove_groups(remove_groups)

        return def_issues

    @staticmethod
    def _check_tag_starts_with(hed_tag, target_tag_short_name):
        """ Check if a given tag starts with a given string, and returns the tag with the prefix removed if it does.

        Parameters
        ----------
        hed_tag : str
            A single input tag
        target_tag_short_name : str
            The string to match eg find target_tag_short_name in hed_tag
        Returns
        -------
            str: the tag without the removed prefix, or None
        """
        hed_tag_lower = hed_tag.lower()
        found_index = hed_tag_lower.find(target_tag_short_name)

        if found_index == -1:
            return None

        if found_index == 0 or hed_tag_lower[found_index - 1] == "/":
            return hed_tag[found_index + len(target_tag_short_name):]
        return None