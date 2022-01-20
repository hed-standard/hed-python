""" BidsSidecarSummary: Holds a summary of BIDS Json Sidecar """

from hed.tools.bids.bids_sidecar_file import BidsSidecarFile


class BidsSidecarSummary:

    def __init__(self, dataset):
        """ Construct a summary of a BidsDataset 

        Parameters:
            dataset: BidsDataset
            The dataset to be summarized.

        """
        self.dataset = dataset