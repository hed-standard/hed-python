import os
from hed.tools.io_utils import get_file_list, parse_bids_filename


class BIDSFile:
    """Represents a bids event file and its sidecar files."""

    def __init__(self, file_path):
        self.file_path = os.path.abspath(file_path)
        suffix, ext, entity_dict = parse_bids_filename(self.file_path)
        self.suffix = suffix
        self.ext = ext
        self.entities = entity_dict
        self.sidecars = []

    def is_parent(self, obj):
        """ Returns true if this is a parent of obj.

         Args:
             obj (BIDSFile):       A BIDSFile object to check

         Returns:
             bool:   True if this is a BIDS parent of obj and False otherwise
         """
        common_path = os.path.commonpath([obj.file_path, self.file_path])
        if common_path != os.path.dirname(self.file_path):
            return False
        elif obj.suffix != self.suffix:
            return False
        for key, item in self.entities.items():
            if key not in obj.entities or obj.entities[key] != item:
                return False
        return True

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
        bids = BIDSFile(file)
        print(bids)
        break
