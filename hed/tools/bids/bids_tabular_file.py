import os
from hed.models.tabular_input import TabularInput
from hed.tools.bids.bids_file import BidsFile


class BidsTabularFile(BidsFile):
    """ A BIDS tabular file including its associated sidecar. """

    def __init__(self, file_path):
        """ Constructor for a BIDS tabular file.

        Args:
            file_path (str):  Path of the tabular file.
        """
        super().__init__(file_path)

    def set_contents(self, content_info=None, no_overwrite=True):
        """ Set the contents of this tabular file.

        Args:
            content_info (str or None):   If string should be the contents of a merged JSON sidecar.
                If None, read in from the file_path.
            no_overwrite:  If True do not overwrite existing contents if any.

        """
        if self.contents and no_overwrite:
            return
        if self.sidecar:
            x = TabularInput(file=self.file_path, sidecar=self.sidecar.contents, name=os.path.realpath(self.file_path))
        else:
            x = TabularInput(file=self.file_path, name=os.path.realpath(self.file_path))
        BidsFile.set_contents(self, content_info=x)
