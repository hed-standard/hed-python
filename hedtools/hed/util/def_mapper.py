from hed.util.hed_string import HedString, HedGroup
from hed.util.def_dict import DefDict, DefTagNames


class DefinitionMapper:
    """Class responsible for gathering/removing definitions from hed strings,
        and also replacing labels in hed strings with the gathered definitions."""

    def __init__(self, def_dicts=None, hed_schema=None):
        """
        Class to handle mapping definitions from hed strings to fill them in with their values.

        Parameters
        ----------
        def_dicts: [DefDict]
            DefDicts containing all the definitions this mapper should initialize with.  More can be added later.
        hed_schema : HedSchema, optional
            Used to determine where definition tags are in the schema.  This is technically optional, but
            only short form definition tags will work if this is absent.
        """
        self._gathered_defs = {}

        if hed_schema:
            self._def_tag_versions = hed_schema.get_all_forms_of_tag(DefTagNames.DEF_KEY)
            self._label_tag_versions = hed_schema.get_all_forms_of_tag(DefTagNames.DLABEL_KEY)
            if not self._label_tag_versions:
                self._label_tag_versions = [DefTagNames.DLABEL_KEY + "/"]
        else:
            self._def_tag_versions = [DefTagNames.DEF_KEY + "/"]
            self._label_tag_versions = [DefTagNames.DLABEL_KEY + "/"]

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

    def replace_and_remove_tags(self, hed_string):
        """Takes a given string and returns the hed string with all definitions removed, and all labels replaced

        Parameters
        ----------
        hed_string : str
            The hed string to modify.
        Returns
        -------
        modified_hed_string: str
            hed_string with all definitions removed and definition tags replaced with the actual definition
        """
        # First see if the word definition or dLabel is found at all.  Just move on if not.
        hed_string_lower = hed_string.lower()
        if DefTagNames.DLABEL_KEY not in hed_string_lower and \
                DefTagNames.DEF_KEY not in hed_string_lower:
            return hed_string

        def_tag_versions = self._def_tag_versions
        label_tag_versions = self._label_tag_versions

        split_string = HedString(hed_string)
        remove_groups = []

        for tag_group in split_string.get_all_groups():
            for tag in tag_group.tags():
                # This case should be fairly rare compared to expanding definitions.
                is_def_tag = DefinitionMapper._check_tag_starts_with(str(tag), def_tag_versions)
                if is_def_tag:
                    remove_groups.append(tag_group)
                    break

                is_label_tag = DefinitionMapper._check_tag_starts_with(str(tag), label_tag_versions)
                if is_label_tag:
                    placeholder = None
                    found_slash = is_label_tag.find("/")
                    if found_slash != -1:
                        placeholder = is_label_tag[found_slash + 1:]
                        is_label_tag = is_label_tag[:found_slash]

                    label_tag_lower = is_label_tag.lower()
                    # Ignore label tags we can't identify.  Probably make this a warning?
                    if label_tag_lower not in self._gathered_defs:
                        continue

                    def_contents = self._gathered_defs[label_tag_lower].get_definition(placeholder_value=placeholder)

                    def_group = HedGroup(hed_string, startpos=tag.span[0], endpos=tag.span[1], contents=def_contents)
                    tag_group.replace_tag_object(tag, def_group)
                    continue

        if remove_groups:
            split_string.remove_groups(remove_groups)

        return str(split_string)

    @staticmethod
    def _check_tag_starts_with(hed_tag, possible_starts_with_list):
        """ Check if a given tag starts with a given string, and returns the tag with the prefix removed if it does.

        Parameters
        ----------
        hed_tag : str
            A single input tag
        possible_starts_with_list : list
            A list of strings to check as the prefix.
            Generally this will be all short/intermediate/long forms of a specific tag
            eg. ['definitional', 'informational/definitional', 'attribute/informational/definitional']
        Returns
        -------
            str: the tag without the removed prefix, or None
        """
        hed_tag_lower = hed_tag.lower()
        for start_with_version in possible_starts_with_list:
            if hed_tag_lower.startswith(start_with_version):
                found_tag = hed_tag[len(start_with_version):]
                return found_tag
        return None
