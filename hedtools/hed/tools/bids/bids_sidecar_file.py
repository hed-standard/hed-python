import os
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_file import BidsFile


class BidsSidecarFile(BidsFile):
    """Represents a bids file."""

    def __init__(self, file_path, set_contents=False):
        super().__init__(os.path.abspath(file_path))
        if set_contents:
            self.contents = Sidecar(self.file_path, name=os.path.abspath(self.file_path))
        else:
            self.contents = None

    def is_sidecar_for(self, obj):
        """ Returns true if this is a sidecar for obj.

         Args:
             obj (BidsFile):       A BIDSFile object to check

         Returns:
             bool:   True if this is a BIDS parent of obj and False otherwise
         """

        if obj.suffix != self.suffix:
            return False

        common_path = os.path.commonpath([obj.file_path, self.file_path])
        if common_path != os.path.dirname(self.file_path):
            return False
        for key, item in self.entities.items():
            if key not in obj.entities or obj.entities[key] != item:
                return False
        return True

    @staticmethod
    def get_sidecar(obj, sidecars):
        """ Return a single SideCar relevant to obj from list of sidecars """
        if not sidecars:
            return None
        for sidecar in sidecars:
            if sidecar.is_sidecar_for(obj):
                return sidecar.contents
        return None
