from hed.errors.exceptions import HedFileError
from hed.tools.bids.bids_file import BidsFile
from hed.tools.analysis.file_dictionary import FileDictionary


class BidsFileDictionary(FileDictionary):
    """ Class representing a dictionary of path names keyed by specified entity pairs. """

    def __init__(self, collection_name, files, entities=('sub', 'ses', 'task', 'run')):
        """ Create a dictionary object with keys that are simplified file names and values that are full paths.

        Args:
            collection_name (str):      Name of this collection.
            files (list or dict):   List containing full paths of files of interest or entity dict.
            entities (tuple:  List of indices into base file names of pieces to assemble for the key.

        Notes:
            This function is used for cross listing BIDS style files for different studies.

        Examples:
            If entities is ('sub', 'ses', 'task', 'run'), a typical key might be sub-001_ses-01_task-memory_run-01.

        Raises:
            HedFileError: If files has inappropriate values.

        """
        super().__init__(collection_name, None, None, separator='_')
        self.entities = entities
        self.file_dict = self.make_dict(files, entities)

    @property
    def key_list(self):
        return list(self.file_dict.keys())

    @property
    def file_list(self):
        """ Return a list of the files contained in this dictionary. """

        return list(self.file_dict.values())

    def get_file_path(self, key):
        """ Return the file path corresponding to the specified key or None if not in this dictionary.

        Args:
            key (str):  The key to use to look up the file in this dictionary.

        Returns:
            str:  The real path of the file being looked up.

        """
        if key in self.file_dict.keys():
            return self.file_dict[key].file_path
        return None

    def iter_files(self):
        """ Iterator over the files in this dictionary.

        Yields:
            str:              The next key.
            BidsFile:         The next object.

        """
        for key, file in self.file_dict.items():
            yield key, file

    def key_diffs(self, other_dict):
        """Return a list containing the symmetric difference of the keys in the two dictionaries.

        Args:
            other_dict (FileDictionary)  A file dictionary object

        Returns:
            list: A list of the symmetric difference of the keys in this dictionary and the other one.

        """
        diffs = set(self.file_dict.keys()).symmetric_difference(set(other_dict.file_dict.keys()))
        return list(diffs)

    def get_new_dict(self, name, files):
        """ Create a new object of the same type with the specified files using entities of this dictionary.

        Args:
            name (str):  Name of this dictionary
            files (list or dict):  List or dictionary of files. These could be paths or objects.

        Returns:
            BidsFileDictionary:  The newly created dictionary.

        """
        return BidsFileDictionary(name, files, entities=self.entities)

    def make_query(self, query_dict={'sub': '*'}):
        """ Return a dictionary with all of the files whose entity keys match the query.

        Args:
            query_dict (dict): A dictionary whose keys are entities and whose values are entity values to match.

        Returns:
            dict: A dictionary entries in this dictionary that match the query.

        Notes:
            A query dictionary key a valid BIDS entity name such as sub or task.
            A query dictionary value may be a string or a list.
            A query value string should contain a specific value of the entity or a '*' indicating any value matches.
            A query value list should be a list of valid values for the corresponding entity.

        """
        response_dict = {}
        for key, file in self.file_dict.items():
            if self.match_query(query_dict, file.entity_dict):
                response_dict[key] = file
        return response_dict

    def split_by_entity(self, entity):
        """ Split this dictionary object into two dictionaries -- one with the entity and the other not containing it.

        Args:
            entity (str):  Entity name (for example task).

        Returns:
            dict: A dictionary whose keys are the unique values of entity and whose values are BidsFileDictionary objs.
            dict: A BidsFileDictionary containing the files that don't have entity in their names.

        Notes:
            This function is used for analysis where a single subject or single type of task is being analyzed.

        """
        split_dict, leftovers = self._split_dict_by_entity(self.file_dict, entity)
        for entity_value, entity_dict in split_dict.items():
            split_dict[entity_value] = self.get_new_dict(f"{self.name}_{entity_value}", entity_dict)
        if leftovers:
            leftover_dict = self.get_new_dict(self.name + "_left_overs", leftovers)
        else:
            leftover_dict = None
        return split_dict, leftover_dict

    @staticmethod
    def _split_dict_by_entity(file_dict, entity):
        """ Split a dict of BidsFile into two dictionaries based on an entity.

        Args:
            file_dict (dict): Dictionary of BidsFile keyed by entity keys.
            entity (str):     String

        Returns:
            dict: Dictionary of dictionaries with first-level keys constructed from the unique values of entities.
            dict: Dictionary of BidsFile that do not have the entity.

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

    def make_dict(self, files, entities):
        """ Make a dictionary of appropriate file objects from a list of files or a dict of files.

        Args:
            files (list or dict):  Full paths (or the file objects) of the files to be values in the dictionary.
            entities (list):       List of entity names to use as keys, for example ['sub', 'run'].

        Returns:
            dict:  A dictionary whose keys are entity keys and values are BidsFile objects.

        Raises:
            HedFileError: If incorrect format is passed or something not recognizable as a Bids file.

        """
        file_dict = {}

        if isinstance(files, dict):
            files = files.values()
        elif not isinstance(files, list):
            raise HedFileError("BadArgument", "make_bids_file_dict expects a list or dict", [])
        for the_file in files:
            the_file = self.correct_file(the_file)
            key = the_file.get_key(entities)
            if key in file_dict:
                raise HedFileError("NonUniqueFileKeys",
                                   f"dictionary key {key} is associated with {the_file} and {file_dict[key]}", "")
            file_dict[key] = the_file
        return file_dict

    def correct_file(self, the_file):
        """ Takes a BidsFile object or a string representing a path and creates a new object if needed.

        Args:
            the_file (str or BidsFile): If a str, create a new BidsFile object, otherwise pass the original on.

        Raises:
            HedFileError: If the_file isn't str or BidsFile.

        """
        if isinstance(the_file, str):
            the_file = BidsFile(the_file)
        elif not isinstance(the_file, BidsFile):
            HedFileError("BadArgument", f"correct_file expects file path or BidsFile but found {str(the_file)}", [])
        return the_file

    @staticmethod
    def match_query(query_dict, entity_dict):
        """ Return True if the query, represented by the a dictionary has a match in the entity dictionary.

        Args:
            query_dict (dict): A dictionary representing a query about entities.
            entity_dict (dict): A dictionary containing the entity representation for a BIDS file.

        Returns:
            bool:  True if the query matches the entities representing the file.

        """
        for query, query_value in query_dict.items():
            if query not in entity_dict:
                return False
            elif isinstance(query_value, str) and query_value != '*':
                return False
            elif isinstance(query_value, list) and (entity_dict[query] not in query_value):
                return False
        return True
