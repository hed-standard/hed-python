""" Classes for managing counts of HED tags for columnar files. """

import copy


class HedTagCount:
    """ Counts for a particular HedTag in particular file."""

    def __init__(self, hed_tag, file_name):
        """
        Parameters:
            hed_tag (HedTag):  The HedTag to keep track of.
            file_name (str):   Name of the file associated with the tag.

        """

        self.tag = hed_tag.short_base_tag
        self.tag_terms = hed_tag.tag_terms
        self.events = 1
        self.files = {file_name: ''}
        self.value_dict = {}
        self.set_value(hed_tag)

    def set_value(self, hed_tag):
        """ Update the tag term value counts for a HedTag.

        Parameters:
            hed_tag (HedTag or None):  Item to use to update the value counts.

        """
        if not hed_tag:
            return
        value = hed_tag.extension
        if not value:
            value = None
        if value in self.value_dict:
            self.value_dict[value] = self.value_dict[value] + 1
        else:
            self.value_dict[value] = 1

    def get_info(self, verbose=False) -> dict:
        """ Return counts for this tag.

        Parameters:
            verbose (bool): If False (the default) only number of files included, otherwise a list of files.

        Returns:
              dict:  Keys are 'tag', 'events', and 'files'.
        """
        if verbose:
            files = [name for name in self.files]
        else:
            files = len(self.files)
        return {'tag': self.tag, 'events': self.events, 'files': files}

    def get_summary(self) -> dict:
        """ Return a dictionary summary of the events and files for this tag.

        Returns:
            dict:  dictionary summary of events and files that contain this tag.

        """
        return {'tag': self.tag, 'events': self.events, 'files': [name for name in self.files]}

    def get_empty(self):
        empty = copy.copy(self)
        empty.events = 0
        empty.files = {}
        empty.value_dict = {}
        return empty


class HedTagCounts:
    """ Counts of HED tags for a group of columnar files.

    Parameters:
        name (str):  An identifier for these counts (usually the filename of the tabular file).
        total_events (int):  The total number of events in the columnar file.

    """

    def __init__(self, name, total_events=0):
        self.tag_dict = {}
        self.name = name
        self.files = {}
        self.total_events = total_events

    def update_tag_counts(self, hed_string_obj, file_name):
        """ Update the tag counts based on a HedString object.

        Parameters:
            hed_string_obj (HedString): The HED string whose tags should be counted.
            file_name (str): The name of the file corresponding to these counts.

        """
        if file_name not in self.files:
            self.files[file_name] = ""
        if not hed_string_obj:
            return
        tag_list = hed_string_obj.get_all_tags()
        tag_dict = {}
        for tag in tag_list:
            str_tag = tag.short_base_tag.casefold()
            if str_tag not in tag_dict:
                tag_dict[str_tag] = HedTagCount(tag, file_name)
            else:
                tag_dict[str_tag].set_value(tag)

        self.merge_tag_dicts(tag_dict)

    def organize_tags(self, tag_template) -> tuple:
        """ Organize tags into categories as specified by the tag_template.

        Parameters:
            tag_template (dict): A dictionary whose keys are titles and values are lists of HED tags (str).

        Returns:
            [tuple[dict, list]]: A tuple containing two elements.
            - dict: Keys are tags (strings) and values are list of HedTagCount for items fitting template.
            - list: HedTagCount objects corresponding to tags that don't fit the template.

        """
        template = self.create_template(tag_template)
        unmatched = []
        for tag_count in self.tag_dict.values():
            self._update_template(tag_count, template, unmatched)
        return template, unmatched

    def merge_tag_dicts(self, other_dict):
        """ Merge the information from another dictionary with this object's tag dictionary.

        Parameters:
            other_dict (dict):  Dictionary of tag, HedTagCount to merge.

        """
        for tag, count in other_dict.items():
            if tag not in self.tag_dict:
                self.tag_dict[tag] = count.get_empty()
            self.tag_dict[tag].events = self.tag_dict[tag].events + count.events
            for file in count.files:
                self.tag_dict[tag].files[file] = ''
            if not self.tag_dict[tag].value_dict:
                continue
            for value, val_count in count.value_dict.items():
                if value in self.tag_dict[tag].value_dict:
                    self.tag_dict[tag].value_dict[value] = self.tag_dict[tag].value_dict + val_count
                else:
                    self.tag_dict[tag].value_dict[value] = val_count

    def get_summary(self) -> dict:
        """ Return a summary object containing the tag count information of this summary.

        Returns:
            dict: Keys are 'name', 'files', 'total_events', and 'details'.
        """
        details = {}
        for tag, count in self.tag_dict.items():
            details[tag] = count.get_summary()
        return {'name': str(self.name), 'files': list(self.files.keys()),
                'total_events': self.total_events, 'details': details}

    @staticmethod
    def create_template(tags) -> dict:
        """ Creates a dictionary with keys based on list of keys in tags dictionary.

        Parameters:
            tags (dict):  dictionary of tags and key lists.

        Returns:
            dict:  Dictionary with keys in key lists and values are empty lists.

        Note: This class is used to organize the results of the tags based on a template for display.

        """
        template_dict = {}
        for key, key_list in tags.items():
            for element in key_list:
                template_dict[element.casefold()] = []
        return template_dict

    @staticmethod
    def _update_template(tag_count, template, unmatched):
        """ Update the template or unmatched with info in the tag_count.

        Parameters:
            tag_count (HedTagCount): Information for a particular tag.
            template (dict):  The dictionary to match.
            unmatched (list): List of tag counts not matched so far.

        """
        tag_list = reversed(list(tag_count.tag_terms))
        for tag_key in tag_list:
            if tag_key in template.keys():
                template[tag_key].append(tag_count)
                return
        unmatched.append(tag_count)
