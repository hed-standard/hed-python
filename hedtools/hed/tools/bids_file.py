import os
from hed.models.sidecar import Sidecar
from hed.models.events_input import EventsInput
from hed.tools.io_utils import get_file_list, parse_bids_filename


class BidsFile:
    """Represents a bids file."""

    def __init__(self, file_path):
        self.file_path = os.path.abspath(file_path)
        suffix, ext, entity_dict = parse_bids_filename(self.file_path)
        self.suffix = suffix
        self.ext = ext
        self.entities = entity_dict
        self.my_sidecars = []

    def is_sidecar_for(self, obj):
        """ Returns true if this is a sidecar for obj.

         Args:
             obj (BidsFile):       A BIDSFile object to check

         Returns:
             bool:   True if this is a BIDS parent of obj and False otherwise
         """
        if self.ext != ".json":
            return False
        elif obj.suffix != self.suffix:
            return False
        common_path = os.path.commonpath([obj.file_path, self.file_path])
        if common_path != os.path.dirname(self.file_path):
            return False
        for key, item in self.entities.items():
            if key not in obj.entities or obj.entities[key] != item:
                return False
        return True

    def set_sidecars(self, sidecars):
        self.my_sidecars = sidecars

    def __str__(self):
        my_str = self.file_path + ":\n\tname_suffix=" + self.suffix + " ext=" + self.ext + \
                 " entities=" + str(self.entities)
        if self.my_sidecars:
            my_str = my_str + "\n\tmy_sidecars=" + str(self.my_sidecars)
        return my_str


class BidsJsonFile(BidsFile):
    """Represents a bids file."""

    def __init__(self, file_path):
        super().__init__(file_path)
        self.my_contents = Sidecar(file_path, name=file_path)


class BidsEventFile(BidsFile):
    """Represents a bids file."""

    def __init__(self, file_path):
        super().__init__(file_path)
        self.my_contents = None


if __name__ == '__main__':
    path = 'D:\\Research\\HED\\hed-examples\\datasets\\eeg_ds003654s'
    files = get_file_list(path, name_prefix=None, name_suffix="events", extensions=None)
    for file in files:
        bids = BidsFile(file)
        print(bids)
        break
