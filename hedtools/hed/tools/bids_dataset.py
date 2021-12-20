import os
from hed.errors.error_reporter import get_printable_issue_string
from hed.schema.hed_schema_file import load_schema
from hed.tools.bids_file import BidsJsonFile, BidsEventFile
from hed.models.events_input import EventsInput
from hed.tools.io_utils import get_dir_dictionary, get_file_list, get_path_components
from hed.validator.hed_validator import HedValidator


class BidsDataset:
    """Represents a bids dataset."""

    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        self.files = self.get_dataset_files()
        self.dataset_description = {}
        self.participants = []

    def get_dataset_files(self):
        return {}