import os
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_file import BidsFile


class BidsSidecarFile(BidsFile):
    """ Represents a BIDS JSON sidecar file."""

    def __init__(self, file_path):
        super().__init__(file_path)
        self.is_validated = False
        self.issues = []

    def add_inherited_columns(self):
        """ Add additional columns assuming that the inherited sidecars are from top to bottom. """

        for sidecar in self.bids_sidecars:
            column_dict = sidecar.contents._column_data
            for column_name, column_meta in column_dict.items():
                self._column_data[column_name] = column_meta

    def clear_contents(self):
        self.contents = None
        self.is_validated = False
        self.issues = []

    def is_sidecar_for(self, obj):
        """ Returns true if this is a sidecar for obj.

         Args:
             obj (BidsFile):       A BIDSFile object to check

         Returns:
             bool:   True if this is a BIDS parent of obj and False otherwise

         Notes:
             A sidecar cannot be a sidecar for itself.

         """

        if obj.file_path == self.file_path or obj.suffix != self.suffix:
            return False
        elif os.path.dirname(self.file_path) != os.path.commonpath([obj.file_path, self.file_path]):
            return False

        for key, item in self.entity_dict.items():
            if key not in obj.entity_dict or obj.entity_dict[key] != item:
                return False
        return True

    def set_contents(self):
        self.contents = Sidecar(self.file_path, name=os.path.realpath(self.file_path))

    @staticmethod
    def get_sidecar(obj, sidecars):
        """ Return a single SideCar relevant to obj from list of sidecars """
        if not sidecars:
            return None
        for sidecar in sidecars:
            if sidecar.is_sidecar_for(obj):
                return sidecar.contents
        return None
