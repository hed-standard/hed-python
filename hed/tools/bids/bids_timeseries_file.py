import os
from hed.models.tabular_input import TabularInput
from hed.tools.bids.bids_file import BidsFile


class BidsTimeseriesFile(BidsFile):
    """ Represents a BIDS continuous file including its associated sidecar. """

    def __init__(self, file_path):
        """ Constructor for a BIDS events file. """
        super().__init__(file_path)

    def set_contents(self, content_info=None, no_overwrite=True):
        if self.contents and no_overwrite:
            return
        BidsFile.set_contents(self, content_info=TabularInput(file=self.file_path, sidecar=self.sidecar,
                                                              name=os.path.realpath(self.file_path)))
