import os
from bids_file import BidsFile


class BidsEventFile(BidsFile):
    """Represents a bids file."""

    def __init__(self, file_path):
        super().__init__(os.path.abspath(file_path))
        self.my_contents = None
