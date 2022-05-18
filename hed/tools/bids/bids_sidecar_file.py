import os
import io
import json
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_file import BidsFile


class BidsSidecarFile(BidsFile):
    """ Represents a BIDS JSON sidecar file."""

    def __init__(self, file_path):
        super().__init__(file_path)

    def is_sidecar_for(self, obj):
        """ Returns true if this is a sidecar for obj.

         Args:
             obj (BidsFile):       A BIDSFile object to check

         Returns:
             bool:   True if this is a BIDS parent of obj and False otherwise

         Notes:
             A sidecar is a sidecar for itself.

         """

        if obj.file_path == self.file_path:
            return True
        elif obj.suffix != self.suffix:
            return False
        elif os.path.dirname(self.file_path) != os.path.commonpath([obj.file_path, self.file_path]):
            return False

        for key, item in self.entity_dict.items():
            if key not in obj.entity_dict or obj.entity_dict[key] != item:
                return False
        return True

    def set_contents(self, content_info=None):
        if not content_info:
            self.contents = Sidecar(self.file_path, name=os.path.realpath(os.path.basename(self.file_path)))
        else:
            merged_sidecar = {}
            for s in content_info:
                with open(s.file_path, 'r') as fp:
                    next_sidecar = json.load(fp)
                    for key, item in next_sidecar.items():
                        merged_sidecar[key] = item

            self.contents = Sidecar(file=io.StringIO(json.dumps(merged_sidecar)),
                                    name=os.path.realpath(os.path.basename(self.file_path)))
