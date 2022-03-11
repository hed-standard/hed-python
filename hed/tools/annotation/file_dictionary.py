import os
from hed.errors.exceptions import HedFileError
from hed.util.data_util import get_new_dataframe
from hed.tools.annotation.annotation_util import generate_sidecar_entry


class FileDictionary:
    """Holds a dictionary of path names keyed by specified entity pairs. """

    def __init__(self, file_list, name_indices=(0, 2), separator='_'):
        """ Create a dictionary with keys that are simplified file names and values that are full paths

        This function is used for cross listing BIDS style files for different studies.

        Args:
            file_list (list):      List containing full paths of files of interest
            name_indices (tuple):  List of indices into base file names of pieces to assemble for the key
            separator (str):       Character used to separate pieces of key name
        """
        if name_indices:
            self.file_dict = self.make_file_dict(file_list, name_indices=name_indices, separator=separator)
        else:
            self.file_dict = {}

    @property
    def key_list(self):
        return list(self.file_dict.keys())

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

    def print_files(self, title=None):
        if title:
            print(f"{title} ({len(self.key_list)} files)")
        for key, value in self.file_dict.items():
            print(f"{key}: {os.path.basename(value)}")

    @staticmethod
    def make_file_dict(file_list, name_indices=(0, 2), separator='_'):
        file_dict = {}
        for the_file in file_list:
            the_file = os.path.realpath(the_file)
            base = os.path.basename(the_file)
            key = FileDictionary.make_key(base, indices=name_indices, separator=separator)
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
