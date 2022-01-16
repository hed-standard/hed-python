from hed.tools.bids.bids_event_files import BidsEventFiles


class BidsDatasetSummary:

    def __init__(self, root_path, hed_schema):
        self.event_files = BidsEventFiles(root_path)
        self.hed_schema = hed_schema
