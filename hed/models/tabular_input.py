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
            name (str): The name to display for this file for error purposes.

        :raises HedFileError:
            - file is blank
            - An invalid dataframe was passed with size 0
            - An invalid extension was provided
            - A duplicate or empty column name appears

        :raises OSError:
            - Cannot open the indicated file

        :raises ValueError:
            - This file has no column names
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

    def get_def_dict(self, hed_schema=None, extra_def_dicts=None):
        """ Returns the definition dict for this sidecar.

        Parameters:
            hed_schema(HedSchema): used to identify tags to find definitions
            extra_def_dicts (list, DefinitionDict, or None): Extra dicts to add to the list.

        Returns:
            DefinitionDict:   A single definition dict representing all the data(and extra def dicts)
        """
        if self._sidecar:
            return self._sidecar.get_def_dict(hed_schema, extra_def_dicts)
        else:
            super().get_def_dict(hed_schema, extra_def_dicts)

    def get_column_refs(self):
        """ Returns a list of column refs for this file.

            Default implementation returns none.

        Returns:
            column_refs(list): A list of unique column refs found
        """
        if self._sidecar:
            return self._sidecar.get_column_refs()
        return []
