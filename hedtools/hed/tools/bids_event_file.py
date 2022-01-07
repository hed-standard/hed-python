import os
from bids_file import BidsFile
from hed.models.events_input import EventsInput


class BidsEventFile(BidsFile):
    """Represents a bids file."""

    def __init__(self, file_path):
        super().__init__(os.path.abspath(file_path))
        self.contents = None
        self.sidecars = None

    def clear_contents(self):
        self.contents = None

    def set_contents(self):
        self.contents = EventsInput(file=self.file_path, sidecars=self.sidecars,
                                    name=os.path.abspath(self.file_path))

    def set_sidecars(self, sidecars):
        self.sidecars = sidecars

    def __str__(self):
        my_str = super().__str__()
        if self.sidecars:
            my_str = my_str + "\n\tsidecars=" + str(self.sidecars)
        return my_str
