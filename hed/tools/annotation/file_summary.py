import os



class FileSummary:
    """ Creates a dictionary of files of a particular type."""

    def __init__(self, file_list, name_indices=(0, 2), separator='_'):
        """ Class that stores a file list by key.

        Args:
            file_list (list):      List containing full paths of files of interest
            name_indices (tuple):  List of indices into base file names of pieces to assemble for the key
            separator (str):       Character used to separate pieces of key name

        """
        self.name_indices = name_indices
        self.separator = separator
        self.file_dict = self._make_file_dict(file_list)
        self.column_dict = {}
        self.event_dict

    def _make_file_dict(self, file_list):
        """ Return a dictionary with keys that are simplified file names and values that are full paths

        This function is used for cross listing BIDS style files for different studies.

        Args:
            file_list (list):      List containing full paths of files of interest
            name_indices (tuple):  List of indices into base file names of pieces to assemble for the key
            separator (str):       Character used to separate pieces of key name
        Returns:
            dict:  A dictionary of simplified, path-independent key names and full paths values.
        """
        file_dict = {}
        for the_file in file_list:
            the_file = os.path.abspath(the_file)
            base = os.path.basename(the_file)
            key = self.make_key(base, indices=self.name_indices, separator=self.separator)
            file_dict[key] = the_file
        return file_dict

    @staticmethod
    def make_key(key_string, indices=(0, 2), separator='_'):
        key_value = ''
        pieces = key_string.split(separator)
        for index in list(indices):
            key_value += pieces[index] + separator
        return key_value[:-1]
