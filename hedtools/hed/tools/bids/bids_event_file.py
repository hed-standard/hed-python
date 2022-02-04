import os
from hed.models.events_input import EventsInput
from hed.tools.bids.bids_tsv_file import BidsTsvFile


class BidsEventFile(BidsTsvFile):
    """Represents a BIDS event file including its associated sidecars."""

    def __init__(self, file_path):
        super().__init__(os.path.abspath(file_path), set_contents=False)
        self.contents = None
        self.sidecars = None

    def clear_contents(self):
        self.contents = None

    def set_contents(self):
        self.contents = EventsInput(file=self.file_path, sidecars=self.sidecars,
                                    name=os.path.abspath(self.file_path))

    def set_sidecars(self, sidecars):
        if sidecars is None:
            self.sidecars = []
        elif not isinstance(sidecars, list):
            self.sidecars = [sidecars]
        else:
            self.sidecars = sidecars

    def __str__(self):
        my_str = super().__str__()
        if self.sidecars:
            my_str = my_str + "\n\tsidecars=" + str(self.sidecars)
        return my_str
