import os
import json
from hed.tools.bids.bids_file import BidsFile


class BidsJsonFile(BidsFile):
    """Represents a BIDS JSON file."""

    def __init__(self, file_path, set_contents=False):
        super().__init__(file_path)
        self.contents = None
        if set_contents:
            self.set_contents()

    def clear_contents(self):
        self.contents = None

    def set_contents(self):
        with open(self.file_path, 'r') as f:
            self.contents = json.load(f)

    def __str__(self):
        """ Returns a string summary of the tsv file."""
        if isinstance(self.contents, dict):
            return super().__str__() + f"\n\tKeys: [{str(list(self.contents.keys()))}\n\t"
        else:
            return super().__str__()
