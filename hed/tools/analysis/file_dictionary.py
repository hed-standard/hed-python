""" A file dictionary keyed by entity indices. """
import os
from hed.errors.exceptions import HedFileError


class FileDictionary:
    """ A file dictionary keyed by entity pair indices.

    Notes:
        - The entities are identified as 0, 1, ... depending on order in the base filename.
        - The entity key-value pairs are assumed separated by '_' unless a separator is provided.

    """

    def __init__(self, collection_name, file_list, key_indices=(0, 2), separator='_'):
        """ Create a dictionary with full paths as values.


        Parameters:
            collection_name (str): Name of the file collection for reference.
            file_list (list, None):      List containing full paths of files of interest.
            key_indices (tuple, None):   List of order of key-value pieces to assemble for the key.
            separator (str):             Character used to separate pieces of key name.


        Notes:
            - This dictionary is used for cross listing BIDS style files for different studies.
            -

        Examples:
            If key_indices is (0, 2), the key generated for /tmp/sub-001_task-FaceCheck_run-01_events.tsv is
            sub_001_run-01.

        """
        self.collection_name = collection_name
        self._file_dict = {}
        self.create_file_dict(file_list, key_indices, separator)

    @property
    def name(self):
        """ Name of this dictionary. """
        return self.collection_name

    @property
    def key_list(self):
        """ Keys in this dictionary. """
        return list(self._file_dict.keys())

    @property
    def file_dict(self):
        """ Dictionary of path values in this dictionary. """
        return self._file_dict

    @property
    def file_list(self):
        """ List of path values in this dictionary. """
        return list(self._file_dict.values())

    def create_file_dict(self, file_list, key_indices, separator):
        """ Create new dict based on key indices.

        Parameters:
            file_list (list): Paths of the files to include.
            key_indices (tuple): A tuple of integers representing order of entities for key.
            separator (str): The separator used between entities to form the key.

        """
        if key_indices:
            self._file_dict = self.make_file_dict(file_list, key_indices=key_indices, separator=separator)

    def get_file_path(self, key):
        """ Return file path corresponding to key.

        Parameters:
            key (str): Key used to retrieve the file path.

        Returns:
            str: File path.

        """
        return self._file_dict.get(key, None)

    def iter_files(self):
        """ Iterator over the files in this dictionary.

        Yields:
            - str: Key into the dictionary.
            - file: File path.

        """
        for key, file in self._file_dict.items():
            yield key, file

    def key_diffs(self, other_dict):
        """ Return symmetric key difference with another dict.

        Parameters:
            other_dict (FileDictionary)  A file dictionary object.

        Returns:
            list: The symmetric difference of the keys in this dictionary and the other one.

        """
        diffs = set(self._file_dict.keys()).symmetric_difference(set(other_dict.file_dict.keys()))
        return list(diffs)

    def output_files(self, title=None, logger=None):
        """ Return a string with the output of the list.

        Parameters:
            title (None, str):    Optional title.
            logger (HedLogger):   Optional HED logger for recording.

        Returns:
            str: The dictionary in string form.

        Notes:
            - The logger is updated if available.

        """
        output_list = []
        if title:
            output_list.append(f"{title} ({len(self.key_list)} files)")
        for key, value in self._file_dict.items():
            basename = os.path.basename(self.get_file_path(key))
            output_list.append(f"{key}: {basename}")
            if logger:
                logger.add(key, f"{self.name}: {basename}")
        return "\n".join(output_list)

    @staticmethod
    def make_file_dict(file_list, key_indices=(0, 2), separator='_'):
        """ Return a dictionary of files using entity keys.

        Parameters:
            file_list (list):    Paths to files to use.
            key_indices (tuple): Positions of entities to use for key.
            separator (str):  Separator character used to construct key.

        Returns:
            dict: Key is based on key indices and value is a full path.

        """
        file_dict = {}
        for the_file in file_list:
            the_file = os.path.realpath(the_file)
            base = os.path.basename(the_file)
            key = FileDictionary.make_key(base, indices=key_indices, separator=separator)
            if key in file_dict:
                raise HedFileError("NonUniqueFileKeys",
                                   f"dictionary key {key} is associated with {the_file} and {file_dict[key]}", "")
            file_dict[key] = the_file
        return file_dict

    @staticmethod
    def make_key(key_string, indices=(0, 2), separator='_'):
        """ Create a key from specified entities.

        Parameters:
            key_string (str): The string from which to extract the key (usually a filename or path).
            indices (tuple):  Positions of entity pairs to use as key.
            separator (str):  Separator between entity pairs in the created key.

        Returns:
            str:  The created key.

        """
        key_value = ''
        pieces = key_string.split(separator)
        for index in list(indices):
            key_value += pieces[index] + separator
        return key_value[:-1]
