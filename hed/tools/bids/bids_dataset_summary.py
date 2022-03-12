from hed.tools.bids.bids_dataset import BidsDataset


class BidsDatasetSummary:
    """ Summarizes a BIDS dataset. """

    def __init__(self, dataset):
        """

        Parameters:
            dataset: BidsDataset or str
            The dataset to be summarized.

        """
        if isinstance(dataset, str):
            dataset = BidsDataset(dataset)
        self.dataset = dataset
