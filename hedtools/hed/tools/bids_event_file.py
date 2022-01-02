import os
from bids_file import BidsFile
from hed.models.events_input import EventsInput


class BidsEventFile(BidsFile):
    """Represents a bids file."""

    def __init__(self, file_path, set_contents=False):
        super().__init__(os.path.abspath(file_path))
        self.contents = []
        self.reset_contents(set_contents)

    def reset_contents(self, set_contents=False):
        if set_contents:
            self.contents = EventsInput(file=self.file_path, sidecars=self.sidecars,
                                        name=os.path.abspath(self.file_path))
        else:
            self.contents = None
