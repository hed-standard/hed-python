"""BidsTsvFile class."""
import os
from pandas import DataFrame
from hed.tools.bids.bids_file import BidsFile
from hed.util.data_util import get_new_dataframe


class BidsTsvFile(BidsFile):
    """ Represents a BIDS TSV file, possibly without its contents. """

    def __init__(self, file_path):
        """ Constructor for a BIDS tsv file.

        Args:
            file_path (str):  The full path to the file.

        """
        super().__init__(file_path)

    def set_contents(self):
        self.contents = get_new_dataframe(self.file_path)

    def __str__(self):
        """ Return a string summary of the tsv file."""

        if isinstance(self.contents, DataFrame):
            return super().__str__() + f"\n\tColumns: [{str(self.contents.columns.values.tolist())}\n\t" + \
                              f"Rows: {len(self.contents.index)}"
        else:
            return super().__str__()
