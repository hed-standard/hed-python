from hed.util.data_util import get_new_dataframe
from hed.tools.annotation.file_dictionary import FileDictionary


class TsvFileDictionary(FileDictionary):
    """ Holds a key-file dictionary, but also reads each tsv file and keeps track of number of rows and column names."""

    def __init__(self, file_list, name_indices=(0, 2), separator='_'):
        """ Create a dictionary with keys that are simplified file names and values that are full paths

        This function is used for cross listing BIDS style files for different studies.

        Args:
            file_list (list):      List containing full paths of files of interest
            name_indices (tuple):  List of indices into base file names of pieces to assemble for the key
            separator (str):       Character used to separate pieces of key name
        """

        super().__init__(file_list, name_indices=name_indices, separator=separator)
        self.column_dict = {}
        self.rowcount_dict = {}
        self._set_event_info()

    def _set_event_info(self):
        for key, file in self.file_dict.items():
            df = get_new_dataframe(file)
            self.rowcount_dict[key] = len(df.index)
            self.column_dict[key] = list(df.columns.values)

    def iter_event_info(self):
        for key, file in self.file_dict.items():
            yield key, file, self.rowcount_dict[key], self.column_dict[key]

    def event_count_diffs(self, other_dict):
        """Returns a list containing the keys in which the number of events differ

        Args:
            other_dict (FileDictionary)  A file dictionary object

        Returns: list of tuple
            A list (key, count1, count2) tuples

        """
        diff_list = []
        for key in self.file_dict.keys():
            if self.rowcount_dict[key] != other_dict.rowcount_dict[key]:
                diff_list.append((key, self.rowcount_dict[key], other_dict.rowcount_dict[key]))
        return diff_list
