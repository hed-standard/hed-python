from hed.models.column_mapper import ColumnMapper
from hed.models.base_input import BaseInput
from hed.models.sidecar import Sidecar
from hed.models.def_mapper import DefinitionMapper


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
            DefDict objects containing all the definitions this file should use other than the ones coming from the file
            itself and from the column def groups.  These are added as as the last entries, so names will override
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

        new_mapper = ColumnMapper(sidecars=sidecars, optional_tag_columns=[self.HED_COLUMN_NAME],
                                  attribute_columns=attribute_columns)

        self._also_gather_defs = also_gather_defs
        self._extra_def_dicts = extra_def_dicts
        def_mapper = self.create_def_mapper(new_mapper, extra_def_dicts)

        super().__init__(file, file_type=".tsv", worksheet_name=None, has_column_names=True, mapper=new_mapper,
                         def_mapper=def_mapper, name=name)

        if not self._has_column_names:
            raise ValueError("You are attempting to open a bids style file with no column headers provided.\n"
                             "This is probably not intended.")

    def create_def_mapper(self, column_mapper, extra_def_dicts=None):
        """
            Creates the definition mapper to parse definitions in this file.

        Parameters
        ----------
        column_mapper : ColumnMapper
            The column mapper to gather definitions from
        extra_def_dicts : DefDict or [DefDict]
            Optional. Adds any definitions in these to the def mapper as well, in addition to any found in the columns.
        Returns
        -------
        def mapper: DefinitionMapper
            A class to validate or expand definitions with the given def dicts.
        """
        def_dicts = []
        if self._also_gather_defs:
            def_dicts = column_mapper.get_def_dicts()

        if extra_def_dicts and not isinstance(extra_def_dicts, list):
            extra_def_dicts = [extra_def_dicts]
        if extra_def_dicts:
            def_dicts += extra_def_dicts
        def_mapper = DefinitionMapper(def_dicts)

        return def_mapper

    def reset_column_mapper(self, sidecars=None, attribute_columns=None):
        """
            Change the sidecars and settings in use for parsing this file.

        Parameters
        ----------
        sidecars : str or [str] or Sidecar or [Sidecar]
            A list of json filenames to pull events from
        attribute_columns: str or int or [str] or [int]
            A list of column names or numbers to treat as attributes.
            Default: ["duration", "onset"]
        Returns
        -------

        """
        new_mapper = ColumnMapper(sidecars=sidecars, optional_tag_columns=[self.HED_COLUMN_NAME],
                                  attribute_columns=attribute_columns)

        self._def_mapper = self.create_def_mapper(new_mapper, self._extra_def_dicts)
        self.reset_mapper(new_mapper)

    def validate_file_sidecars(self, validators=None, error_handler=None, **kwargs):
        """
        Validates all column definitions and column definition hed strings.

        This is not an encouraged way to do this.  You should instead validate the sidecars BEFORE creating the
        EventsInput object.

        Parameters
        ----------
        validators : [func or validator like] or func or validator like
            A validator or list of validators to apply to the hed strings in the sidecars.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        kwargs:
            See util.translate_ops or the specific validators for additional options
        Returns
        -------
        validation_issues : [{}]
            A list of syntax and semantic issues found in the definitions.
        """
        if not isinstance(validators, list):
            validators = [validators]
        validators.append(self._def_mapper)
        return self._mapper.validate_column_data(validators, error_handler=error_handler, **kwargs)
