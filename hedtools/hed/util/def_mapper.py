from hed.util.hed_string_util import split_hed_string
from hed.util.def_dict import DefDict


class DefinitionMapper:
    """Class responsible for gathering/removing definitions from hed strings,
        and also replacing labels in hed strings with the gathered definitions."""
    DLABEL_ORG_KEY = 'Label-def'
    ELABEL_ORG_KEY = 'Label-exp'
    DLABEL_KEY = DLABEL_ORG_KEY.lower()
    ELABEL_KEY = ELABEL_ORG_KEY.lower()

    DEF_KEY = "definition"
    ORG_KEY = "organizational"

    def __init__(self, def_dicts=None, hed_schema=None):
        """
        Class to handle mapping definitions from hed strings to fill them in with their vlaues.

        Parameters
        ----------
        def_dicts: [DefDict]
            DefDict's containing all the definitions this mapper should initialize with.  More can be added later.
        hed_schema : HedSchema, optional
            Used to determine where definition tags are in the schema.  This is technically optional, but
            only short form definition tags will work if this is absent.
        """
        self._gathered_defs = {}

        if hed_schema:
            self._def_tag_versions = hed_schema.get_all_forms_of_tag(self.DEF_KEY)
            self._label_tag_versions = hed_schema.get_all_forms_of_tag(self.DLABEL_KEY)
            if not self._label_tag_versions:
                self._label_tag_versions = [self.DLABEL_KEY + "/"]
        else:
            self._def_tag_versions = [self.DEF_KEY + "/"]
            self._label_tag_versions = [self.DLABEL_KEY + "/"]

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
        if self.DLABEL_KEY not in hed_string_lower and \
                self.DEF_KEY not in hed_string_lower:
            return hed_string

        def_tag_versions = self._def_tag_versions
        label_tag_versions = self._label_tag_versions

        hed_tags = split_hed_string(hed_string)

        indexes_to_change = []
        for is_hed_tag, (startpos, endpos) in hed_tags:
            tag = hed_string[startpos:endpos]
            if is_hed_tag:
                is_def_tag = DefinitionMapper._check_tag_starts_with(tag, def_tag_versions)
                if is_def_tag:
                    indexes_to_change.append((startpos, None, None))
                    continue

                is_label_tag = DefinitionMapper._check_tag_starts_with(tag, label_tag_versions)
                if is_label_tag:
                    indexes_to_change.append((startpos, is_label_tag, tag))
                    continue

        final_string = hed_string
        # print(f"Original String: {final_string}")
        # Do this in reverse order so we don't need to update string indexes
        for tag_index, label_tag, full_label_tag in reversed(indexes_to_change):
            replace_with = ""
            if full_label_tag:
                to_remove = full_label_tag
                label_tag_lower = label_tag.lower()
                # Just leave definitions in place if they aren't found.
                if label_tag_lower not in self._gathered_defs:
                    continue
                replace_with = self._gathered_defs[label_tag_lower]
            else:
                extents = self._find_tag_group_extent(final_string, tag_index, remove_comma=True)
                to_remove = hed_string[extents[0]:extents[1]]
                # print(f"To remove: '{to_remove}'")
            final_string = final_string.replace(to_remove, replace_with)
        # print(final_string)
        return final_string

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

    @staticmethod
    def _find_tag_group_extent(hed_string, starting_tag_index, remove_comma=True):
        """
        Returns the starting/ending index into the string of the tag group at starting_tag_index in hed_string

        eg (tag1, tag2, (tag3, tag4)) will return (0, 13) if 0 <= starting_tag_index < 13 and
                will return (13, 24) if 13 <= starting_tag_index < 24
                will return (0, 24) if starting_tag_index == 24

        Parameters
        ----------
        hed_string : str
            The hed string to gather the tag extents from
        starting_tag_index : int
            Index into the string to gather tag extents from
        remove_comma : bool
            If True, extents will include the now extraneous comma (between tag2 and tag3
                above if removing tag3 in above example)
        Returns
        -------
        start_index: int
            The first index of the full tag group
        end_index: int
            The last index of the full tag group
        """
        paren_counter = 0
        start_index_a = 0
        end_index_a = len(hed_string)
        start_index = start_index_a
        end_index = end_index_a
        for i in range(starting_tag_index, -1, -1):
            if hed_string[i] == ')':
                paren_counter += 1
            elif hed_string[i] == '(':
                if paren_counter == 0:
                    start_index = i
                    break
                paren_counter -= 1

        paren_counter = 0
        for i in range(starting_tag_index, end_index):
            if hed_string[i] == '(':
                paren_counter += 1
            elif hed_string[i] == ')':
                if paren_counter == 0:
                    end_index = i + 1
                    break
                paren_counter -= 1

        if remove_comma:
            found_comma = False
            # First check if a comma is before the string.
            if start_index > 0:
                for i in range(start_index - 1, -1, -1):
                    if hed_string[i] == ',':
                        found_comma = True
                    elif hed_string[i] != ' ':
                        break
                    start_index = i

            # Now check if one is at the end if we didn't already find one.
            if not found_comma and end_index < end_index_a:
                for i in range(end_index, end_index_a):
                    if hed_string[i] == ',':
                        continue
                    elif hed_string[i] != ' ':
                        break
                    end_index = i + 1

        return start_index, end_index
