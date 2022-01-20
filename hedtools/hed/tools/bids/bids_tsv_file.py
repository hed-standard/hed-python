"""BidsTsvFile class."""
import os
from pandas import DataFrame
from hed.tools.bids.bids_file import BidsFile
from hed.util.data_util import get_new_dataframe


class BidsTsvFile(BidsFile):
    """Represents a bids tsv file with contents that are a dataframe.

    Parameters
    ----------
    file_path: str
        The full path to the file
    set_contents: bool
        If true then the file contents are read into a dataframe.

  """
    def __init__(self, file_path, set_contents=False):
        super().__init__(os.path.abspath(file_path))
        self.contents = None
        if set_contents:
            self.set_contents()

    def clear_contents(self):
        self.contents = None

    def set_contents(self):
        self.contents = get_new_dataframe(self.file_path)

    def __str__(self):
        """ Returns a string summary of the tsv file."""
        if isinstance(self.contents, DataFrame):
            return super().__str__() + f"\n\tColumns: [{str(self.contents.columns.values.tolist())}\n\t" + \
                              f"Rows: {len(self.contents.index)}"
        else:
            return super().__str__()
