from hed.models.column_mapper import ColumnMapper
from hed.models.base_input import BaseInput
from hed.models.sidecar import Sidecar
from hed.models.def_mapper import DefMapper


class TimeseriesInput(BaseInput):
    """ Represents a BIDS time series tsv file."""

    HED_COLUMN_NAME = "HED"

    def __init__(self, file=None, sidecar=None, extra_def_dicts=None, name=None):
        """Constructor for the TimeseriesInput class.

        Args:
            file (str or file like): A tsv file to open.
            sidecar (str or Sidecar): A json sidecar to pull metadata from.
            extra_def_dicts ([DefinitionDict] or DefinitionDict or None)
                DefinitionDict objects containing all the definitions this file should use other than the ones coming
                from the file itself and from the column def groups. These are added as the last entries,
                so names will override earlier ones.
            name (str): The name to display for this file for error purposes.
        """

        super().__init__(file, file_type=".tsv", worksheet_name=None, has_column_names=False, mapper=None,
                         def_mapper=None, name=name)
