from hed.models.column_mapper import ColumnMapper
from hed.models.base_input import BaseInput
from hed.models.sidecar import Sidecar


class EventsInput(BaseInput):
    """A class to parse bids style spreadsheets into a more general format."""

    HED_COLUMN_NAME = "HED"

    def __init__(self, file=None, sidecars=None, attribute_columns=None, extra_def_dicts=None,
                 also_gather_defs=True, name=None):
        """Constructor for the EventsInput class.

        Parameters
        ----------
         file: str or file like
             An xlsx/tsv file to open.
        sidecars : str or [str] or Sidecar or [Sidecar]
            A list of json files to pull column metadata from
        attribute_columns: str or int or [str] or [int]
            A list of column names or numbers to treat as attributes.
            Default: ["duration", "onset"]
        extra_def_dicts: [DefDict]
            DefDict's containing all the definitions this file should use - other than the ones coming from the file
            itself, and from the column def groups.  These are added as as the last entries, so names will override
            earlier ones.
        also_gather_defs: bool
            Default to true.  If False, do NOT extract any definitions from column groups, assume they are already
            in the def_dict list.
        name: str
            The name to display for this file for error purposes.
        """
        if attribute_columns is None:
            attribute_columns = ["duration", "onset"]

        if sidecars:
            sidecars = Sidecar.load_multiple_sidecars(sidecars)
        if extra_def_dicts and not isinstance(extra_def_dicts, list):
            extra_def_dicts = [extra_def_dicts]

        new_mapper = ColumnMapper(sidecars=sidecars, optional_tag_columns=[self.HED_COLUMN_NAME],
                                  attribute_columns=attribute_columns,
                                  extra_def_dicts=extra_def_dicts,
                                  also_gather_defs=also_gather_defs)

        super().__init__(file, file_type=".tsv", worksheet_name=None, has_column_names=True, mapper=new_mapper,
                         name=name)

        if not self._has_column_names:
            raise ValueError("You are attempting to open a bids style file with no column headers provided.\n"
                             "This is probably not intended.")

    def reset_column_mapper(self, sidecars=None, attribute_columns=None, extra_def_dicts=None, also_gather_defs=True):
        """
            Change the sidecars and settings in use for parsing this file.

        Parameters
        ----------
        sidecars : str or [str] or Sidecar or [Sidecar]
            A list of json filenames to pull events from
        attribute_columns: str or int or [str] or [int]
            A list of column names or numbers to treat as attributes.
            Default: ["duration", "onset"]
        extra_def_dicts: [DefDict]
            DefDict's containing all the definitions this file should use - other than the ones coming from the file
            itself, and from the column def groups.  These are added as as the last entries, so names will override
            earlier ones.
        also_gather_defs: bool
            Default to true.  If False, do NOT extract any definitions from column groups, assume they are already
            in the def_dict list.
        Returns
        -------

        """
        new_mapper = ColumnMapper(sidecars=sidecars, optional_tag_columns=[self.HED_COLUMN_NAME],
                                  attribute_columns=attribute_columns,
                                  extra_def_dicts=extra_def_dicts,
                                  also_gather_defs=also_gather_defs)

        self.reset_mapper(new_mapper)

    def validate_file_sidecars(self, hed_schema=None, error_handler=None):
        """
        Validates all column definitions and column definition hed strings.

        This is not an encouraged way to do this.  You should instead validate the sidecars BEFORE creating
        an EventsInput
        Parameters
        ----------
        hed_schema : HedSchema, optional
            Also semantically validates hed strings if present.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        Returns
        -------
        validation_issues : [{}]
            A list of syntax and semantic issues found in the definitions.
        """
        return self._mapper.validate_column_data(hed_schema, error_handler)
