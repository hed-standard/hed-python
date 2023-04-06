from hed.models.column_mapper import ColumnMapper
from hed.models.base_input import BaseInput
from hed.models.sidecar import Sidecar


class TabularInput(BaseInput):
    """ A BIDS tabular tsv file with sidecar. """

    HED_COLUMN_NAME = "HED"

    def __init__(self, file=None, sidecar=None, name=None):

        """ Constructor for the TabularInput class.

        Parameters:
            file (str or file like): A tsv file to open.
            sidecar (str or Sidecar): A Sidecar filename or Sidecar
                Note: If this is a string you MUST also pass hed_schema.
            name (str): The name to display for this file for error purposes.
        """
        if sidecar and not isinstance(sidecar, Sidecar):
            sidecar = Sidecar(sidecar)
        new_mapper = ColumnMapper(sidecar=sidecar, optional_tag_columns=[self.HED_COLUMN_NAME],
                                  warn_on_missing_column=True)

        self._sidecar = sidecar

        super().__init__(file, file_type=".tsv", worksheet_name=None, has_column_names=True, mapper=new_mapper,
                         name=name, allow_blank_names=False, )

        if not self._has_column_names:
            raise ValueError("You are attempting to open a bids_old style file with no column headers provided.\n"
                             "This is probably not intended.")

    def reset_column_mapper(self, sidecar=None):
        """ Change the sidecars and settings.

        Parameters:
            sidecar (str or [str] or Sidecar or [Sidecar]): A list of json filenames to pull sidecar info from.

        """
        new_mapper = ColumnMapper(sidecar=sidecar, optional_tag_columns=[self.HED_COLUMN_NAME])

        self.reset_mapper(new_mapper)
