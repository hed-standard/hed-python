from hed.errors.exceptions import HedFileError
from hed.tools import BidsFile
from hed.tools.annotation.file_dictionary import FileDictionary


class BidsFileDictionary(FileDictionary):
    """ Holds a dictionary of path names keyed by specified entity pairs. """

    def __init__(self, collection_name, file_list=None, entities=('sub', 'ses', 'task', 'run')):
        """ Create a dictionary with keys that are simplified file names and values that are full paths

        This function is used for cross listing BIDS style files for different studies.

        Args:
            collection_name (str): Name of this collection
            file_list (list, None):      List containing full paths of files of interest
            entities (tuple:  List of indices into base file names of pieces to assemble for the key
        """
        super().__init__(collection_name, None, None, separator='_')
        self.entities = entities
        if file_list:
            self.file_dict = self.make_bids_file_dict(file_list, entities)

    @property
    def key_list(self):
        return list(self.file_dict.keys())

    @property
    def file_list(self):
        return list(self.file_dict.values())

    def get_file_path(self, key):
        if key in self.file_dict.keys():
            return self.file_dict[key].file_path
        return None

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

    def make_query(self, query_dict={'sub': '*', 'run': ['*']}):
        response_dict = {}
        for key, file in self.file_dict.items():
            if self.match_query(query_dict, file.entity_dict):
                response_dict[key] = file
        return response_dict

    def _create_dict_obj(self, collection_name, file_dict):
        dict_obj = BidsFileDictionary(collection_name, file_list=None, entities=self.entities)
        dict_obj.file_dict = file_dict
        return dict_obj

    def create_split_dict(self, entity):
        split_dict, leftovers = self.split_dict_by_entity(self.file_dict, entity)
        for entity_value, entity_dict in split_dict.items():
            split_dict[entity_value] = \
                self._create_dict_obj(self.name + "_" + str(entity_value), split_dict[entity_value])
        if leftovers:
            leftover_dict = self._create_dict_obj(self.name + "_left_overs", leftovers)
        else:
            leftover_dict = None
        return split_dict, leftover_dict

    @staticmethod
    def split_dict_by_entity(file_dict, entity):
        """ Split a dict of BidsFile into multiple dicts based on an entity

        """
        split_dict = {}
        leftovers = {}
        for key, file in file_dict.items():
            if entity not in file.entity_dict:
                leftovers[key] = file
                continue
            entity_value = file.entity_dict[entity]
            entity_dict = split_dict.get(entity_value, {})
            entity_dict[key] = file
            split_dict[entity_value] = entity_dict
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
                    key_list.append(f"{entity}-{entity_dict[entity]}")
            key = '_'.join(key_list)
            if key in file_dict:
                raise HedFileError("NonUniqueFileKeys",
                                   f"dictionary key {key} is associated with {the_file} and {file_dict[key]}", "")
            file_dict[key] = the_file
        return file_dict

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
