from hed.util.hed_string_util import split_hed_string
from hed.util.hed_string_delimiter import HedStringDelimiter
from hed.util.base_file_input import BaseFileInput
from hed.util.column_def_group import ColumnDefGroup

class DefinitionMapper:
    """Class responsible for gathering/removing definitions from hed strings,
        and also replacing labels in hed strings with the gathered definitions."""
    DLABEL_ORG_KEY = 'Label-def'
    ELABEL_ORG_KEY = 'Label-exp'
    DLABEL_KEY = DLABEL_ORG_KEY.lower()
    ELABEL_KEY = ELABEL_ORG_KEY.lower()

    DEF_KEY = "definition"
    ORG_KEY = "organizational"

    def __init__(self, hed_inputs=None, hed_dictionary=None):
        self._defs = {}
        self._hed_dictionary = hed_dictionary

        if hed_dictionary:
            self._def_tag_versions = hed_dictionary.get_all_forms_of_tag(self.DEF_KEY)
            self._org_tag_versions = hed_dictionary.get_all_forms_of_tag(self.ORG_KEY)
            self._label_tag_versions = hed_dictionary.get_all_forms_of_tag(self.DLABEL_KEY)
            if not self._label_tag_versions:
                self._label_tag_versions = [self.DLABEL_KEY + "/"]
        else:
            self._def_tag_versions = [self.DEF_KEY + "/"]
            self._org_tag_versions = [self.ORG_KEY + "/"]
            self._label_tag_versions = [self.DLABEL_KEY + "/"]

        if hed_inputs:
            self.add_definitions(hed_inputs)

    def add_definitions(self, hed_inputs):
        """ Adds all definitions found in hed strings in the given input

        Parameters
        ----------
        hed_inputs : list or str or BaseFileInput or ColumnDefGroup
            List input doesn't need to all be the same type.
        """
        if not isinstance(hed_inputs, list):
            hed_inputs = [hed_inputs]
        for hed_input in hed_inputs:
            if isinstance(hed_input, str):
                self._check_for_definitions(hed_input)
            elif isinstance(hed_input, BaseFileInput):
                for row_number, row_hed_string, column_to_hed_tags_dictionary in hed_input.iter_raw():
                    self._check_for_definitions(row_hed_string)
            elif isinstance(hed_input, ColumnDefGroup):
                for hed_string in hed_input.hed_string_iter():
                    self._check_for_definitions(hed_string)
            else:
                print(f"Invalid input type '{type(hed_input)} passed to DefinitionMapper.  Skipping.")
                # add error here

    def replace_and_remove_tags(self, hed_string):
        """Takes a given string and returns the hed string with all definitions removed, and all labels replaced

        Parameters
        ----------
        hed_string : str
            The hed string to modify.
        Returns
        -------
            str: the string with replacements
        """
        """"""
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
        #print(f"Original String: {final_string}")
        # Do this in reverse order so we don't need to update string indexes
        for tag_index, label_tag, full_label_tag in reversed(indexes_to_change):
            replace_with = ""
            if full_label_tag:
                to_remove = full_label_tag
                replace_with = self._defs[label_tag.lower()]
            else:
                extents = self._find_tag_group_extent(final_string, tag_index, remove_comma=True)
                to_remove = hed_string[extents[0]:extents[1]]
                #print(f"To remove: '{to_remove}'")
            final_string = final_string.replace(to_remove, replace_with)
        #print(final_string)
        return final_string

    @staticmethod
    def _check_tag_starts_with(hed_tag, possible_starts_with_list):
        """ Check if a given tag starts with a given string

        Parameters
        ----------
        hed_tag : str
            A single input tag
        possible_starts_with_list : list
            A list of strings to check as the prefix.
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

    def _check_for_definitions(self, hed_string):
        """Check a given hed string to see if there is a definition in it.

        Parameters
        ----------
        hed_string :

        Returns
        -------

        """
        if self.DEF_KEY not in hed_string.lower():
            return False

        def_tag_versions = self._def_tag_versions
        org_tag_versions = self._org_tag_versions

        # This could eventually be replaced with another method as we only care about portions of the tags
        string_split = HedStringDelimiter(hed_string)
        for tag_group in string_split.tag_groups:
            org_tags = []
            def_tags = []
            group_tags = []
            for tag in tag_group:
                new_def_tag = DefinitionMapper._check_tag_starts_with(tag, def_tag_versions)
                if new_def_tag:
                    def_tags.append(new_def_tag)
                    continue

                new_org_tag = DefinitionMapper._check_tag_starts_with(tag, org_tag_versions)
                if new_org_tag:
                    org_tags.append(tag)
                    continue

                group_tags.append(tag)

            # Now validate to see if we have a definition.  We want 1 definition, and the other parts are optional.
            if not def_tags:
                # If we don't have at least one valid definition tag, just move on.  This is probably a tag with
                # the word definition somewhere else in the text.
                continue

            if len(def_tags) > 1:
                print(f"Too many def tags found in definition for {def_tags[0]}.  Also found: {def_tags[1:]}")
                continue
            def_tag = def_tags[0]
            if len(org_tags) > 1:
                print(f"Too many org tags found in definition for {def_tag}.  Also found: {org_tags}")
                continue
            if len(group_tags) > 1:
                print(f"Too many org tags found in definition for {def_tag}.  Also found: {group_tags}")
                continue

            org_tag = org_tags[0] if org_tags else None
            group_tag = group_tags[0] if group_tags else None

            if def_tag in self._defs:
                print(f"Duplicate definition found for '{def_tag}'.")
            if self._hed_dictionary and self._hed_dictionary.tag_exists(def_tag):
                print(f"Tag '{def_tag}' already in base schema.")

            self._defs[def_tag.lower()] = f"({self.ELABEL_ORG_KEY}/{def_tag}, {org_tag}, {group_tag})"

    @staticmethod
    def _find_tag_group_extent(hed_string, starting_tag_index, remove_comma=True):
        """Returns the starting/ending index into the string of the given tag group.

        eg (tag1, tag2, (tag3, tag4)) will return (0, 13) if 0 <= starting_tag_index < 13 and
                will return (13, 24) if 13 <= starting_tag_index < 24
                will return (0, 24) if starting_tag_index == 24

        Parameters
        ----------
        hed_string : str
        starting_tag_index : int
            index into the string to gather extents from
        remove_comma : bool
            If True, extents will include the now extraneous comma (between tag2 and tag3
                above if removing tag3 in above example)

        Returns
        -------

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
            #First check if a comma is before the string.
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
                        found_comma = True
                    elif hed_string[i] != ' ':
                        break
                    end_index = i + 1

        return start_index, end_index


if __name__ == '__main__':
    import os
    from hed.util.hed_file_input import HedFileInput
    from hed.util.hed_dictionary import HedDictionary

    local_xml_file = "examples/data/HED8.0.0-alpha.1.xml"
    hed_dictionary = HedDictionary(local_xml_file)
    def_string = "(Attribute/Informational/Definition/XXX, Attribute/Organizational/YYY, (Tag1, Tag2))," \
                 "(Attribute/Informational/Definition/XXX, Attribute/Organizational/YYY, (Tag1, Tag2))"
    mapper = DefinitionMapper(def_string, hed_dictionary=hed_dictionary)
    def_removed = mapper.replace_and_remove_tags(def_string)

    def_string = "(Attribute/Informational/Definition/XXX, ()), (Attribute/Informational/Definition/XXX2, ())"
    DefinitionMapper(def_string, hed_dictionary=hed_dictionary)

    def_string_3level = "(Tag1, tag2, (tag3, tag4), (Attribute/Informational/Definition/XXX, Attribute/Organizational/YYY, (Tag5, Tag6)))"
    mapper = DefinitionMapper(def_string_3level, hed_dictionary=hed_dictionary)
    def_removed = mapper.replace_and_remove_tags(def_string_3level)
    print(f"after Def Removed: {def_removed}")

    def_string_3level = "(Tag1, tag2, (Label-def/XXX, tag4), (Attribute/Informational/Definition/XXX, Attribute/Organizational/YYY, (Tag5, Tag6)))"
    mapper = DefinitionMapper(def_string_3level, hed_dictionary=hed_dictionary)
    def_removed = mapper.replace_and_remove_tags(def_string_3level)
    print(f"after Def Removed: {def_removed}")

    example_data_path = 'examples/data'  # path to example data
    multiple_sheet_xlsx_file = os.path.join(example_data_path, 'ExcelMultipleSheets.xlsx')

    prefixed_needed_tag_columns = {2: 'Event/Label/', 3: 'Event/Description/'}
    # Example 3a: XLSX file with multiple sheets - first sheet has no issues with 7.1.1
    input_file = HedFileInput(multiple_sheet_xlsx_file, tag_columns=[4],
                              column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='LKT Events')

    DefinitionMapper(input_file, hed_dictionary=hed_dictionary)
