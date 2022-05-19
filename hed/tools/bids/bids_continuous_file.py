import os
from hed.models.events_input import EventsInput
from hed.tools.bids.bids_file import BidsFile


class BidsContinuousFile(BidsFile):
    """ Represents a BIDS continuous file including its associated sidecar. """

    def __init__(self, file_path):
        """ Constructor for a BIDS events file. """
        super().__init__(file_path)

    def set_contents(self, content_info=None, no_overwrite=True):
        if self.contents and no_overwrite:
            return
        BidsFile.set_contents(self, content_info=EventsInput(file=self.file_path, sidecars=self.sidecar,
                                                             name=os.path.realpath(self.file_path)))
