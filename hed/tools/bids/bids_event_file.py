import os
from hed.models.events_input import EventsInput
from hed.tools.bids.bids_tsv_file import BidsTsvFile


class BidsEventFile(BidsTsvFile):
    """ Represents a BIDS event file including its associated sidecars.

    """

    def __init__(self, file_path):
        """ Constructor for a BIDS events file. """
        super().__init__(file_path)

    def set_contents(self):
        self.contents = EventsInput(file=self.file_path, sidecars=self.sidecar, name=os.path.realpath(self.file_path))
