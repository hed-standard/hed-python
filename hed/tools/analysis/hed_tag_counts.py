""" Counts of HED tags in a file's annotations. """

import copy


class HedTagCount:
    def __init__(self, hed_tag, file_name):
        """ Counts for a particular HedTag in particular file.

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

    def get_info(self, verbose=False):
        if verbose:
            files = [name for name in self.files]
        else:
            files = len(self.files)
        return {'tag': self.tag, 'events': self.events, 'files': files}
    
    def get_summary(self):
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
    """ Counts of HED tags for a tabular file.
    
    Parameters:
        name (str):  An identifier for these counts (usually the filename of the tabular file)
        total_events (int):  The total number of events in the tabular file.


    """

    def __init__(self, name, total_events=0):
        self.tag_dict = {}
        self.name = name
        self.files = {}
        self.total_events = total_events
     
    def update_event_counts(self, hed_string_obj, file_name, definitions=None):
        """ Update the tag counts based on a hed string object. 
        
        Parameters:
            hed_string_obj (HedString): The HED string whose tags should be counted.
            file_name (str): The name of the file corresponding to these counts.
            definitions (dict): The definitions associated with the HED string.
            
        """
        if file_name not in self.files:
            self.files[file_name] = ""
        tag_list = hed_string_obj.get_all_tags()
        tag_dict = {}
        for tag in tag_list:
            str_tag = tag.short_base_tag.lower()
            if str_tag not in tag_dict:
                tag_dict[str_tag] = HedTagCount(tag, file_name)
            else:
                tag_dict[str_tag].set_value(tag)

        self.merge_tag_dicts(tag_dict)

    def organize_tags(self, tag_template):
        template = self.create_template(tag_template)
        unmatched = []
        for key, tag_count in self.tag_dict.items():
            matched = False
            for tag in reversed(tag_count.tag_terms):
                if tag in template:
                    template[tag].append(tag_count)
                    matched = True
                    break
            if not matched:
                unmatched.append(tag_count)
        return template, unmatched

    def merge_tag_dicts(self, other_dict):
        for tag, count in other_dict.items():
            if tag not in self.tag_dict:
                self.tag_dict[tag] = count.get_empty()
            self.tag_dict[tag].events = self.tag_dict[tag].events + count.events
            value_dict = self.tag_dict[tag].value_dict
            for value, val_count in count.value_dict.items():
                if value in value_dict:
                    value_dict[value] = value_dict[value] + val_count
                else:
                    value_dict[value] = val_count
            for file in count.files:
                self.tag_dict[tag].files[file] = ''

    def get_summary(self):
        details = {}
        for tag, count in self.tag_dict.items():
            details[tag] = count.get_summary()
        return {'name': str(self.name), 'type_tag': self.type_tag, 'files': list(self.files.keys()),
                'total_events': self.total_events, 'details': details}

    @staticmethod
    def create_template(tags):
        template_dict = {}
        for key, key_list in tags.items():
            for element in key_list:
                template_dict[element.lower()] = []
        return template_dict
