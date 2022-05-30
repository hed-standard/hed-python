from hed.util.data_util import get_new_dataframe
from hed.tools.bids.bids_file_dictionary import BidsFileDictionary
from hed.errors.exceptions import HedFileError
from hed.tools.bids.bids_file import BidsFile
from hed.tools.bids.bids_tabular_file import BidsTabularFile


class BidsTabularDictionary(BidsFileDictionary):
    """ A key tabular-file dictionary for tabular files.

    Attributes:
        column_dict (dict): Dictionary with an entity key and a list of column names for the file as the value.
        rowcount_dict (dict): Dictionary with an entity key and a count of number of rows for the file as the value.

    """

    def __init__(self, collection_name, files, entities=('sub', 'ses', 'task', 'run')):
        """ Create a dictionary of full paths.

        Args:
            collection_name (str):   Name of the collection.
            files (list, dict):      Contains the full paths or BidsFile representation of files of interest.
            entities (tuple):        List of indices into base file names of pieces to assemble for the key.

        Notes:
            - Used for cross listing BIDS style files for different studies.

        """

        super().__init__(collection_name, files, entities=entities)
        self.column_dict = {}
        self.rowcount_dict = {}
        self._info_set = False

    def correct_file(self, the_file):
        """ Transform to BidsTabularFile if needed.

        Args:
            the_file (str or BidsFile): If a str, create a new BidsTabularFile object,
                                        otherwise pass the original on.
        Returns:
            BidsTabularFile:  Either the original file or a newly created BidsTabularFile.

        Raises:
            HedFileError: If the_file isn't str or BidsTabularFile.

        """
        if isinstance(the_file, str):
            the_file = BidsTabularFile(the_file)
        elif not isinstance(the_file, BidsFile):
            HedFileError("BadArgument", f"correct_file needs file path or BidsFile type but found {str(the_file)}", [])
        elif not isinstance(the_file, BidsTabularFile):
            the_file = BidsTabularFile(the_file.file_path)
        return the_file

    def count_diffs(self, other_dict):
        """ Return keys in which the number of rows differ.

        Args:
            other_dict (FileDictionary):  A file dictionary object.

        Returns:
            list: A list containing 3-element tuples.

        Notes:
            - The returned tuples consist of
                - str:  The key representing the file.
                - int:  Number of rows in the file in this dictionary.
                - int:  Number of rows in the file in the other dictionary.

        """
        self._set_tsv_info()
        diff_list = []
        for key in self.file_dict.keys():
            if self.rowcount_dict[key] != other_dict.rowcount_dict[key]:
                diff_list.append((key, self.rowcount_dict[key], other_dict.rowcount_dict[key]))
        return diff_list

    def get_info(self, key):
        """ Return a dict with key, row count, and column count.

        Args:
            key (str): The key for file whose information is to be returned.

        Returns:
            dict: A dictionary with key, row_count, and columns entries.

        """

        if not self._info_set:
            self._set_tsv_info()
        return {"key": key,
                "row_count": self.rowcount_dict.get(key, None),
                "columns": self.column_dict.get(key, None)}

    def get_new_dict(self, name, files):
        """ Create a new BidsTabularDictionary.

        Args:
            name (str):            Name of the new object.
            files (list, dict):    List or dictionary specifying the files to include.

        Returns:
            BidsTabularDictionary: The object contains just the specified files.

        Notes:
            - The created object uses the entities from this object

        """
        return BidsTabularDictionary(name, files, entities=self.entities)

    def iter_files(self):
        """ Iterator over the files in this dictionary.

         Yields:
             tuple:
                - str: The next key.
                - BidsTabularFile:   The next object.
                - int:  Number of rows
                - list:  List of column names

        """
        self._set_tsv_info()
        for key, file in self.file_dict.items():
            yield key, file, self.rowcount_dict[key], self.column_dict[key]

    def make_new(self, name, files):
        """ Create a dictionary with these files.

        Args:
            name (str):  Name of this dictionary
            files (list or dict):  List or dictionary of files. These could be paths or objects.

        Returns:
            BidsTabularDictionary:  The newly created dictionary.

        """
        return BidsTabularDictionary(name, files, entities=self.entities)

    def _set_tsv_info(self):
        if self._info_set:
            return

        for key, file in self.file_dict.items():
            df = get_new_dataframe(file.file_path)
            self.rowcount_dict[key] = len(df.index)
            self.column_dict[key] = list(df.columns.values)
        self.info_set = True
