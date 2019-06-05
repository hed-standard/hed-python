'''
This module is used to split tags in a HED string .

Created on Nov 15, 2017

@author: Jeremy Cockfield

'''


import copy;


class HedStringDelimiter:
    DELIMITER = ',';
    DOUBLE_QUOTE_CHARACTER = '"';
    OPENING_GROUP_CHARACTER = '(';
    CLOSING_GROUP_CHARACTER = ')';
    TILDE = '~';

    def __init__(self, hed_string):
        """Constructor for the HedStringDelimiter class.

        Parameters
        ----------
        hed_string
            A HED string consisting of tags and tag groups.
        Returns
        -------
        HedStringDelimiter object
            A HedStringDelimiter object.

        """
        self.hed_string = hed_string;
        self._split_hed_string_list = HedStringDelimiter.split_hed_string_into_list(hed_string);
        self.tags = [];
        self.tag_groups = [];
        self.top_level_tags = self._find_top_level_tags();
        self._find_group_tags(self._split_hed_string_list);
        self.tags = HedStringDelimiter.format_hed_tags_in_list(self.tags, True);
        self.top_level_tags = HedStringDelimiter.format_hed_tags_in_list(self.top_level_tags, True);
        self.tag_groups = HedStringDelimiter.format_hed_tags_in_list(self.tag_groups, True);
        self.formatted_tags = HedStringDelimiter.format_hed_tags_in_list(self.tags);
        self.formatted_top_level_tags = HedStringDelimiter.format_hed_tags_in_list(self.top_level_tags);
        self.formatted_tag_groups = HedStringDelimiter.format_hed_tags_in_list(self.tag_groups);

    def get_split_hed_string_list(self):
        """Gets the split_hed_string_list field.

        Parameters
        ----------
        Returns
        -------
        list
            A list containing the individual tags and tag groups in the HED string. Nested tag groups are not split.

        """
        return self._split_hed_string_list;

    def get_hed_string(self):
        """Gets the hed_string field.

        Parameters
        ----------
        Returns
        -------
        string
            The hed string associated with the object.

        """
        return self.hed_string;

    def get_tags(self):
        """Gets the tags field.

        Parameters
        ----------
        Returns
        -------
        list
            A list containing the individual tags in the HED string.

        """
        return self.tags;

    def get_formatted_tag_groups(self):
        """Gets the formatted_tag_groups field.

        Parameters
        ----------
        Returns
        -------
        list
            A list containing all of the groups with formatted tags.

        """
        return self.formatted_tag_groups;

    def get_formatted_tags(self):
        """Gets the formatted_tags field.

        Parameters
        ----------
        Returns
        -------
        list
            A list containing the individual formatted tags in the HED string.

        """
        return self.formatted_tags;

    def get_top_level_tags(self):
        """Gets the top_level_tags field.

        Parameters
        ----------
        Returns
        -------
        list
            A list containing the top-level tags in a HED string.

        """
        return self.top_level_tags;

    def get_formatted_top_level_tags(self):
        """Gets the formatted_top_level_tags field.

        Parameters
        ----------
        Returns
        -------
        list
            A list containing the top-level formatted tags in a HED string.

        """
        return self.formatted_top_level_tags;

    def get_tag_groups(self):
        """Gets the tag_groups field.

        Parameters
        ----------
        Returns
        -------
        list
            A list of a lists containing all of the tag groups in a HED string. Each list is a tag group.

        """
        return self.tag_groups;

    def _find_group_tags(self, tag_group_list):
        """Finds the tags that are in groups and put them in a set. The groups themselves are also put into a list.

        Parameters
        ----------
        tag_group_list: list
            A list containing the group tags.
        Returns
        -------

        """
        for tag_or_group in tag_group_list:
            if HedStringDelimiter.hed_string_is_a_group(tag_or_group):
                tag_group_string = HedStringDelimiter.remove_group_parentheses(tag_or_group);
                nested_group_tag_list = HedStringDelimiter.split_hed_string_into_list(tag_group_string);
                self._find_group_tags(nested_group_tag_list);
                self.tag_groups.append(nested_group_tag_list);
            elif tag_or_group not in self.tags:
                self.tags.append(tag_or_group);

    def _find_top_level_tags(self):
        """Finds all of the tags at the top-level in a HED string. All group tags will be removed.

        Parameters
        ----------
        Returns
        -------
        list
            A list containing the top-level tags.

        """
        top_level_tags = copy.copy(self._split_hed_string_list);
        for tag_or_group in self._split_hed_string_list:
            if HedStringDelimiter.hed_string_is_a_group(tag_or_group):
                top_level_tags.remove(tag_or_group);
            elif tag_or_group not in self.tags:
                self.tags.append(tag_or_group);
        return top_level_tags;

    @staticmethod
    def format_hed_tag(hed_tag, only_remove_new_line=False):
        """Format a single HED tag. Slashes and double quotes in the beginning and end are removed and the tag is
           converted to lowercase.

        Parameters
        ----------
        hed_tag: string
            A HED tag
        Returns
        -------
        string
            The formatted version of the HED tag.

        """
        hed_tag = hed_tag.replace('\n', ' ');
        if only_remove_new_line:
            return hed_tag;
        hed_tag = hed_tag.strip();
        if hed_tag.startswith('"'):
            hed_tag = hed_tag[1:];
        if hed_tag.endswith('"'):
            hed_tag = hed_tag[:-1];
        if hed_tag.startswith('/'):
            hed_tag = hed_tag[1:];
        if hed_tag.endswith('/'):
            hed_tag = hed_tag[:-1];
        return hed_tag.lower();

    @staticmethod
    def format_hed_tags_in_list(hed_tags_list, only_remove_new_line=False):
        """Format the HED tags in a list. The list can be nested. Groups are represented as lists themselves.

        Parameters
        ----------
        hed_tags_list: list
            A list containing HED tags. Groups are lists inside of the list.
        Returns
        -------
        list
            A list with the HED tags formatted.

        """
        formatted_hed_tags_list = list();
        for hed_tag_or_hed_tag_group in hed_tags_list:
            if isinstance(hed_tag_or_hed_tag_group, list):
                formatted_tag_group_list = HedStringDelimiter.format_hed_tags_in_list(hed_tag_or_hed_tag_group,
                                                                                      only_remove_new_line);
                formatted_hed_tags_list.append(formatted_tag_group_list);
            else:
                formatted_hed_tag = HedStringDelimiter.format_hed_tag(hed_tag_or_hed_tag_group,
                                                                      only_remove_new_line);
                formatted_hed_tags_list.append(formatted_hed_tag);
        return formatted_hed_tags_list;

    @staticmethod
    def format_hed_tags_in_set(hed_tags_set):
        """Format the HED tags in a set.

        Parameters
        ----------
        hed_tags_set: set
            A set containing HED tags.
        Returns
        -------
        string
            The formatted version of the HED tag.

        """
        formatted_hed_tags_set = set();
        for hed_tag in hed_tags_set:
            formatted_hed_tag = HedStringDelimiter.format_hed_tag(hed_tag);
            formatted_hed_tags_set.add(formatted_hed_tag);
        return formatted_hed_tags_set;

    @staticmethod
    def split_hed_string_into_list(hed_string):
        """Splits the tags and non-nested groups in a HED string based on a delimiter. The default delimiter is a comma.

        Parameters
        ----------
        hed_string
            A hed string consisting of tags and tag groups.
        Returns
        -------
        list
            A list containing the individual tags and tag groups in the HED string. Nested tag groups are not split.

        """
        split_hed_string = [];
        number_of_opening_parentheses = 0;
        number_of_closing_parentheses = 0;
        current_tag = '';
        for character in hed_string:
            if character == HedStringDelimiter.DOUBLE_QUOTE_CHARACTER:
                pass;
            if character == HedStringDelimiter.OPENING_GROUP_CHARACTER:
                number_of_opening_parentheses += 1;
            if character == HedStringDelimiter.CLOSING_GROUP_CHARACTER:
                number_of_closing_parentheses += 1;
            if number_of_opening_parentheses == number_of_closing_parentheses and character == HedStringDelimiter.TILDE:
                if not HedStringDelimiter.string_is_space_or_empty(current_tag):
                    split_hed_string.append(current_tag.strip());
                split_hed_string.append(HedStringDelimiter.TILDE);
                current_tag = '';
            elif number_of_opening_parentheses == number_of_closing_parentheses and character == \
                    HedStringDelimiter.DELIMITER:
                if not HedStringDelimiter.string_is_space_or_empty(current_tag):
                    split_hed_string.append(current_tag.strip());
                current_tag = '';
            else:
                current_tag += character;
        if not HedStringDelimiter.string_is_space_or_empty(current_tag):
            split_hed_string.append(current_tag.strip());
        return split_hed_string;

    @staticmethod
    def string_is_space_or_empty(string):
        """Checks to see if the string contains all spaces or is empty.

        Parameters
        ----------
        string
            A string.
        Returns
        -------
        boolean
            True if the string contains all spaces or is empty. False, if otherwise.

        """
        if string.isspace() or not string:
            return True;
        return False;

    @staticmethod
    def hed_string_is_a_group(hed_string):
        """Returns true if the HED string is a group.

        Parameters
        ----------
        hed_string
            A HED string consisting of tags and tag groups.
        Returns
        -------
        boolean
            True if the HED string is a group. False, if not a group.

        """
        hed_string = hed_string.strip();
        if hed_string.startswith(HedStringDelimiter.OPENING_GROUP_CHARACTER) and \
                hed_string.endswith(HedStringDelimiter.CLOSING_GROUP_CHARACTER):
            return True;
        return False;

    @staticmethod
    def remove_group_parentheses(tag_group):
        return tag_group[1:-1];