from hed.util.data_util import get_new_dataframe
from hed.tools.bids.bids_file_dictionary import BidsFileDictionary


class BidsTsvDictionary(BidsFileDictionary):
    """ Holds a key-file dictionary, but also reads each tsv file and keeps track of number of rows and column names."""

    def __init__(self, collection_name, file_list=None, entities=('sub', 'ses', 'task', 'run')):
        """ Create a dictionary with keys that are simplified file names and values that are full paths

        This function is used for cross listing BIDS style files for different studies.

        Args:
            collection_name (str):   Name of the collection
            file_list (list, None):  List containing full paths of files of interest
            entities (tuple):        List of indices into base file names of pieces to assemble for the key
        """

        super().__init__(collection_name, file_list=file_list, entities=entities)
        self.column_dict = {}
        self.rowcount_dict = {}
        self._set_tsv_info()

    def get_info(self, key):
        """ Returns a dictionary with key, row count, and column count

        Args:
            key (str)  key for file

        Returns: dict

        """

        return {"key": key,
                "row_count": self.rowcount_dict.get(key, None),
                "columns": self.column_dict.get(key, None)}

    def _set_tsv_info(self):
        for key, file in self.file_dict.items():
            df = get_new_dataframe(file.file_path)
            self.rowcount_dict[key] = len(df.index)
            self.column_dict[key] = list(df.columns.values)

    def iter_tsv_info(self):
        for key, file in self.file_dict.items():
            yield key, file, self.rowcount_dict[key], self.column_dict[key]

    def count_diffs(self, other_dict):
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

    def _create_dict_obj(self, collection_name, file_dict):
        dict_obj = BidsTsvDictionary(collection_name, file_list=None, entities=self.entities)
        dict_obj.file_dict = file_dict
        dict_obj._set_tsv_info()
        return dict_obj
