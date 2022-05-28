import os
from hed.models.tabular_input import TabularInput
from hed.tools.bids.bids_file import BidsFile


class BidsTabularFile(BidsFile):
    """ Class representing a BIDS tabular file including its associated sidecar. """

    def __init__(self, file_path):
        """ Constructor for a BIDS tabular file.

        Args:
            file_path (str):  Path of the tabular file.
        """
        super().__init__(file_path)

    def set_contents(self, content_info=None, no_overwrite=True):
        if self.contents and no_overwrite:
            return
        if self.sidecar:
            x = TabularInput(file=self.file_path, sidecar=self.sidecar.contents, name=os.path.realpath(self.file_path))
        else:
            x = TabularInput(file=self.file_path, name=os.path.realpath(self.file_path))
        BidsFile.set_contents(self, content_info=x)
