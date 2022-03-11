import os
from hed.util.io_util import parse_bids_filename


class BidsFile:
    """Represents the entity and file names for a BIDs file."""

    def __init__(self, file_path):
        self.file_path = os.path.realpath(file_path)
        suffix, ext, entity_dict, unmatched = parse_bids_filename(self.file_path)
        self.suffix = suffix
        self.ext = ext
        self.entities = entity_dict

    def __str__(self):
        return self.file_path + ":\n\tname_suffix=" + self.suffix + " ext=" + self.ext + \
               " entities=" + str(self.entities)

