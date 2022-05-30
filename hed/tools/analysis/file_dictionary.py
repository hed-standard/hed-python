import os
from hed.errors.exceptions import HedFileError


class FileDictionary:
    """ A file dictionary keyed by entity pair indices. """

    def __init__(self, collection_name, file_list, key_indices=(0, 2), separator='_'):
        """ Create a dictionary with keys that are simplified file names and values that are full paths

        This function is used for cross listing BIDS style files for different studies.

        Args:
            collection_name (str): Name of the file collection for reference
            file_list (list, None):      List containing full paths of files of interest
            key_indices (tuple, None):   List of indices into base file names of pieces to assemble for the key
            separator (str):       Character used to separate pieces of key name

        """
        self.collection_name = collection_name
        self.file_dict = {}
        self.create_file_dict(file_list, key_indices, separator)

    @property
    def name(self):
        return self.collection_name

    @property
    def key_list(self):
        return list(self.file_dict.keys())

    @property
    def file_list(self):
        return list(self.file_dict.values())

    def create_file_dict(self, file_list, key_indices, separator):
        if key_indices:
            self.file_dict = self.make_file_dict(file_list, key_indices=key_indices, separator=separator)

    def get_file_path(self, key):
        return self.file_dict.get(key, None)

    def iter_files(self):
        for key, file in self.file_dict.items():
            yield key, file

    def key_diffs(self, other_dict):
        """ Return a list containing the symmetric difference of the keys in the two dictionaries

        Args:
            other_dict (FileDictionary)  A file dictionary object

        Returns: list
            A list of the symmetric difference of the keys in this dictionary and the other one.

        """
        diffs = set(self.file_dict.keys()).symmetric_difference(set(other_dict.file_dict.keys()))
        return list(diffs)

    def output_files(self, title=None, logger=None):
        """ Return a str with the output of the list.
        Args:
            title (None, str)    Optional title.
            logger (HedLogger)   Optional HED logger for recording.

        Returns: (str)
            Output the dictionary in string form. The logger is updated if available.

        """
        output_list = []
        if title:
            output_list.append(f"{title} ({len(self.key_list)} files)")
        for key, value in self.file_dict.items():
            basename = os.path.basename(self.get_file_path(key))
            output_list.append(f"{key}: {basename}")
            if logger:
                logger.add(key, f"{self.name}: {basename}")
        return "\n".join(output_list)

    @staticmethod
    def make_file_dict(file_list, key_indices=(0, 2), separator='_'):

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
        key_value = ''
        pieces = key_string.split(separator)
        for index in list(indices):
            key_value += pieces[index] + separator
        return key_value[:-1]
