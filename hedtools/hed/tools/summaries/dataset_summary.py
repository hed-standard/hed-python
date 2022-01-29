""" BidsDatasetSummary: Holds a summary of BIDS dataset """

from hed.tools.bids.bids_dataset import BidsDataset


class BidsDatasetSummary:

    def __init__(self, dataset):
        """ Construct a summary of a BidsDataset

        Parameters:
            dataset: BidsDataset or str
            The dataset to be summarized.

        """
        if isinstance(dataset, str):
            dataset = BidsDataset(dataset)
        self.dataset = dataset
