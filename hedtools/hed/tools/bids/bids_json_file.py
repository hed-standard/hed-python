import os
import json
from hed.tools.bids.bids_file import BidsFile


class BidsJsonFile(BidsFile):
    """Represents a bids_old file."""

    def __init__(self, file_path, set_contents=False):
        super().__init__(os.path.abspath(file_path))
        if set_contents:

            with open(self.file_path, 'r') as f:
                self.contents = json.load(f)
        else:
            self.contents = None
