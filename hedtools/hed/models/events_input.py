from hed.models.column_mapper import ColumnMapper
from hed.models.base_input import BaseInput
from hed.models.column_def_group import ColumnDefGroup


class EventsInput(BaseInput):
    """A class to parse bids style spreadsheets into a more general format."""

    HED_COLUMN_NAME = "HED"

    def __init__(self, filename=None, json_def_files=None, attribute_columns=None, extra_def_dicts=None,
                 also_gather_defs_from_column_groups=True, name=None):
        """Constructor for the EventsInput class.

        Parameters
        ----------
         filename: str or file like
             An xlsx/tsv file to open.
        json_def_files : str or [str] or ColumnDefGroup or [ColumnDefGroup]
            A list of json filenames to pull events from
        attribute_columns: str or int or [str] or [int]
            A list of column names or numbers to treat as attributes.
            Default: ["duration", "onset"]
        extra_def_dicts: [DefDict]
            DefDict's containing all the definitions this file should use - other than the ones coming from the file
            itself, and from the column def groups.  These are added as as the last entries, so names will override
            earlier ones.
        also_gather_defs_from_column_groups: bool
            Default to true.  If False, do NOT extract any definitions from column groups, assume they are already
            in the def_dict list.
        name: str
            The name to display for this file for error purposes.
        """
        if attribute_columns is None:
            attribute_columns = ["duration", "onset"]

        column_group_defs = None
        if json_def_files:
            column_group_defs = ColumnDefGroup.load_multiple_json_files(json_def_files)
        if extra_def_dicts and not isinstance(extra_def_dicts, list):
            extra_def_dicts = [column_group_defs]
        else:
            extra_def_dicts = column_group_defs

        new_mapper = ColumnMapper(json_def_files=column_group_defs, tag_columns=[self.HED_COLUMN_NAME],
                                  attribute_columns=attribute_columns,
                                  extra_def_dicts=extra_def_dicts,
                                  also_gather_defs_from_column_groups=also_gather_defs_from_column_groups,
                                  strict_named_columns=False)

        super().__init__(filename, file_type=".tsv", worksheet_name=None, has_column_names=True, mapper=new_mapper,
                         name=name)

        if not self._has_column_names:
            raise ValueError("You are attempting to open a bids style file with no column headers provided.\n"
                             "This is probably not intended.")

    def reset_column_defs(self, json_def_files=None, attribute_columns=None, extra_def_dicts=None,
                          also_gather_defs_from_column_groups=True):
        """
            Change the sidecars in use for parsing this file.

        Parameters
        ----------
        json_def_files : str or [str] or ColumnDefGroup or [ColumnDefGroup]
            A list of json filenames to pull events from
        attribute_columns: str or int or [str] or [int]
            A list of column names or numbers to treat as attributes.
            Default: ["duration", "onset"]
        extra_def_dicts: [DefDict]
            DefDict's containing all the definitions this file should use - other than the ones coming from the file
            itself, and from the column def groups.  These are added as as the last entries, so names will override
            earlier ones.
        also_gather_defs_from_column_groups: bool
            Default to true.  If False, do NOT extract any definitions from column groups, assume they are already
            in the def_dict list.
        Returns
        -------

        """
        new_mapper = ColumnMapper(json_def_files=json_def_files, tag_columns=[self.HED_COLUMN_NAME],
                                  attribute_columns=attribute_columns,
                                  extra_def_dicts=extra_def_dicts,
                                  also_gather_defs_from_column_groups=also_gather_defs_from_column_groups,
                                  strict_named_columns=False)

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
        return self._mapper.validate_column_defs(hed_schema, error_handler)
