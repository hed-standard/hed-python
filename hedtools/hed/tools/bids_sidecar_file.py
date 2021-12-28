import os
from hed.models.sidecar import Sidecar
from bids_file import BidsFile


class BidsSidecarFile(BidsFile):
    """Represents a bids file."""

    def __init__(self, file_path):
        super().__init__(os.path.abspath(file_path))
        self.my_contents = Sidecar(file_path, name=os.path.abspath(file_path))

    @staticmethod
    def get_sidecar(obj, sidecars):
        """ Return a single SideCar relevant to this object from list of sidecars """
        if not sidecars:
            return None
        for sidecar in sidecars:
            if sidecar.is_sidecar_for(obj):
                return sidecar.my_contents
        return None
