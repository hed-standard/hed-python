import os
from hed.errors.exceptions import HedFileError
from hed.tools import BidsFile
from hed.tools.annotation.file_dictionary import FileDictionary


class BidsFileDictionary(FileDictionary):
    """ Holds a dictionary of path names keyed by specified entity pairs. """

    def __init__(self, file_list=None, entities=('sub', 'ses', 'task', 'run')):
        """ Create a dictionary with keys that are simplified file names and values that are full paths

        This function is used for cross listing BIDS style files for different studies.

        Args:
            file_list (list):      List containing full paths of files of interest
            entities (tuple:  List of indices into base file names of pieces to assemble for the key
        """
        if file_list:
            self.file_dict = self.make_bids_file_dict(file_list, entities)
        else:
            self.file_dict = {}
        self.entities = entities

    @property
    def key_list(self):
        return list(self.file_dict.keys())

    @property
    def file_list(self):
        return list(self.file_dict.values())

    def iter_files(self):
        for key, file in self.file_dict.items():
            yield key, file

    def key_diffs(self, other_dict):
        """Returns a list containing the symmetric difference of the keys in the two dictionaries

        Args:
            other_dict (FileDictionary)  A file dictionary object

        Returns: list
            A list of the symmetric difference of the keys in this dictionary and the other one.

        """
        diffs = set(self.file_dict.keys()).symmetric_difference(set(other_dict.file_dict.keys()))
        return list(diffs)

    def make_query(self, query_dict={'sub':'*', 'run':['*']}):
        response_dict = {}
        for key, file in self.file_dict.items():
            if self.match_query(query_dict, file.entity_dict):
                response_dict[key] = file
        return response_dict

    def print_files(self, title=None):
        if title:
            print(f"{title} ({len(self.key_list)} files)")
        for key, value in self.file_dict.items():
            print(f"{key}: {os.path.basename(value.file_path)}")

    def split_by_entity(self, entity):
        split_dict = {}
        leftovers = {}
        for key, file in self.file_dict.items():
            if entity not in file.entity_dict:
                leftovers[key] = file
                continue
            entity_value = file.entity_dict[entity]
            entity_dict = split_dict.get(entity_value, {})
            entity_dict[key] = file
            split_dict[entity_value] = entity_dict

        for entity_value, entity_dict in split_dict.items():
            this_bids_dict = BidsFileDictionary(file_list=None, entities=self.entities)
            this_bids_dict.file_dict = split_dict[entity_value]
            split_dict[entity_value] = this_bids_dict
        return split_dict, leftovers

    @staticmethod
    def make_bids_file_dict(file_list, entities):
        file_dict = {}
        for the_file in file_list:
            the_file = BidsFile(the_file)
            entity_dict = the_file.entity_dict
            key_list = []
            for entity in entities:
                if entity in entity_dict:
                    key_list.append(f"{entity}_{entity_dict[entity]}")
            key = '_'.join(key_list)
            if key in file_dict:
                raise HedFileError("NonUniqueFileKeys",
                                   f"dictionary key {key} is associated with {the_file} and {file_dict[key]}", "")
            file_dict[key] = the_file
        return file_dict

    @staticmethod
    def make_key(key_string, indices=(0, 2), separator='_'):
        key_value = ''
        pieces = key_string.split(separator)
        for index in list(indices):
            key_value += pieces[index] + separator
        return key_value[:-1]

    @staticmethod
    def match_query(query_dict, entity_dict):

        for query, query_value in query_dict.items():
            if query not in entity_dict:
                return False
            elif isinstance(query_value, str) and query_value != '*':
                return False
            elif isinstance(query_value, list) and (entity_dict[query] not in query_value):
                return False
        return True
