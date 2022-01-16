import os
import json
from hed.tools.data_util import get_new_dataframe
from hed.schema.hed_schema_file import load_schema_version
from hed.tools.bids.bids_event_files import BidsEventFiles


class BidsDataset:
    """Represents a bids dataset."""

    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        self.dataset_description = {}
        self.participants = []
        self.hed_schema = None
        self._load_info()
        self.event_files = BidsEventFiles(root_path)

    def _load_info(self):
        part_path = os.path.join(self.root_path, "participants.tsv")
        self.participants = get_new_dataframe(part_path)
        desc_path = os.path.join(self.root_path, "dataset_description.json")
        with open(desc_path, "r") as fp:
            self.dataset_description = json.load(fp)
        hed = self.dataset_description.get("HEDVersion", None)
        if isinstance(hed, str):
            self.hed_schema = load_schema_version(xml_version_number=hed)


if __name__ == '__main__':
    path = 'D:\\Research\\HED\\hed-examples\\datasets\\eeg_ds003654s'
    bids = BidsDataset(path)