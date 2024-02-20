""" A BIDS time series tabular file. """
from hed.models.base_input import BaseInput


class TimeseriesInput(BaseInput):
    """ A BIDS time series tabular file. """

    HED_COLUMN_NAME = "HED"

    def __init__(self, file=None, sidecar=None, extra_def_dicts=None, name=None):
        """Constructor for the TimeseriesInput class.

        Parameters:
            file (str or file like): A tsv file to open.
            sidecar (str or Sidecar): A json sidecar to pull metadata from.
            extra_def_dicts (DefinitionDict, list, or None): Additional definition dictionaries.
            name (str): The name to display for this file for error purposes.

        Notes:
             - The extra_def_dicts are external definitions that override the ones in the object.

        """

        super().__init__(file, file_type=".tsv", worksheet_name=None, has_column_names=False, mapper=None,
                         name=name)
