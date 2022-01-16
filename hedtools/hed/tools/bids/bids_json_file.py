import os
import json
from hed.tools.bids.bids_file import BidsFile


class BidsJsonFile(BidsFile):
    """Represents a bids file."""

    def __init__(self, file_path, set_contents=False):
        super().__init__(os.path.abspath(file_path))
        if set_contents:
            self.contents = json.load(self.file_path)
        else:
            self.contents = None

