from hed.tools.bids.bids_dataset import BidsDataset


class BidsDatasetSummary:
    """ Summary of a BIDS dataset events and other info. """

    def __init__(self, dataset):
        """ Constructor for producing a BIDS dataset JSON summary.

        Args:
            dataset (BidsDataset or str): The dataset to be summarized.

        """
        if isinstance(dataset, str):
            dataset = BidsDataset(dataset)
        self.dataset = dataset
