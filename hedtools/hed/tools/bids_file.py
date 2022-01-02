import os

from hed.tools.io_utils import get_file_list, parse_bids_filename


class BidsFile:
    """Represents a bids file."""

    def __init__(self, file_path):
        self.file_path = os.path.abspath(file_path)
        suffix, ext, entity_dict = parse_bids_filename(self.file_path)
        self.suffix = suffix
        self.ext = ext
        self.entities = entity_dict
        self.sidecars = []

    def set_sidecars(self, sidecars):
        self.sidecars = sidecars

    def __str__(self):
        my_str = self.file_path + ":\n\tname_suffix=" + self.suffix + " ext=" + self.ext + \
                 " entities=" + str(self.entities)
        if self.sidecars:
            my_str = my_str + "\n\tsidecars=" + str(self.sidecars)
        return my_str


if __name__ == '__main__':
    path = 'D:\\Research\\HED\\hed-examples\\datasets\\eeg_ds003654s'
    files = get_file_list(path, name_prefix=None, name_suffix="events", extensions=None)
    for file in files:
        bids = BidsFile(file)
        print(str(bids))
