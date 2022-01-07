import os


class BidsDataset:
    """Represents a bids dataset."""

    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        self.files = self.get_dataset_files()
        self.dataset_description = {}
        self.participants = []

    def get_dataset_files(self):
        return self.files
