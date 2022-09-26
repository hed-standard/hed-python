from hed.models.column_mapper import ColumnMapper
from hed.models.base_input import BaseInput
from hed.models.sidecar import Sidecar
from hed.models.def_mapper import DefMapper


class TabularInput(BaseInput):
    """ A BIDS tabular tsv file with sidecar. """

    HED_COLUMN_NAME = "HED"

    def __init__(self, file=None, sidecar=None, extra_def_dicts=None, also_gather_defs=True, name=None,
                 hed_schema=None):

        """ Constructor for the TabularInput class.

        Parameters:
            file (str or file like): A tsv file to open.
            sidecar (str or Sidecar): A Sidecar filename or Sidecar
            extra_def_dicts ([DefinitionDict], DefinitionDict, or None): DefinitionDict objects containing all
                the definitions this file should use other than the ones coming from the file
                itself and from the sidecar.  These are added as the last entries, so names will override
                earlier ones.
            name (str): The name to display for this file for error purposes.
            hed_schema(HedSchema or None): The schema to use by default in identifying tags
        """
        if sidecar and not isinstance(sidecar, Sidecar):
            sidecar = Sidecar(sidecar)
        new_mapper = ColumnMapper(sidecar=sidecar, optional_tag_columns=[self.HED_COLUMN_NAME],
                                  warn_on_missing_column=True)

        definition_columns = [self.HED_COLUMN_NAME]
        self._sidecar = sidecar
        self._also_gather_defs = also_gather_defs
        if extra_def_dicts and not isinstance(extra_def_dicts, list):
            extra_def_dicts = [extra_def_dicts]
        self._extra_def_dicts = extra_def_dicts
        def_mapper = self.create_def_mapper(new_mapper)

        super().__init__(file, file_type=".tsv", worksheet_name=None, has_column_names=True, mapper=new_mapper,
                         def_mapper=def_mapper, name=name, definition_columns=definition_columns,
                         allow_blank_names=False, hed_schema=hed_schema)

        if not self._has_column_names:
            raise ValueError("You are attempting to open a bids_old style file with no column headers provided.\n"
                             "This is probably not intended.")

    def create_def_mapper(self, column_mapper):
        """ Create the definition mapper for this file.

        Parameters:
            column_mapper (ColumnMapper): The column mapper to gather definitions from.


        Returns:
            def mapper (DefMapper): A class to validate or expand definitions with the given def dicts.

        Notes:
            - The extra_def_dicts are definitions not included in the column mapper.

        """

        def_dicts = column_mapper.get_def_dicts()
        if self._extra_def_dicts:
            def_dicts += self._extra_def_dicts
        def_mapper = DefMapper(def_dicts)

        return def_mapper

    def reset_column_mapper(self, sidecar=None):
        """ Change the sidecars and settings.

        Parameters:
            sidecar (str or [str] or Sidecar or [Sidecar]): A list of json filenames to pull sidecar info from.

        """
        new_mapper = ColumnMapper(sidecar=sidecar, optional_tag_columns=[self.HED_COLUMN_NAME])

        self._def_mapper = self.create_def_mapper(new_mapper)
        self.reset_mapper(new_mapper)

    def validate_sidecar(self, hed_ops=None, error_handler=None, **kwargs):
        """ Validate column definitions and hed strings.

        Parameters:
            hed_ops (list or HedOps): A list of HedOps of funcs to apply to the hed strings in the sidecars.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default one if none passed in.
            kwargs: See models.hed_ops.translate_ops or the specific hed_ops for additional options.

        Returns:
            list: A list of syntax and semantic issues found in the definitions. Each issue is a dictionary.

        Notes:
            - For full validation you should validate the sidecar separately.

        """
        if not isinstance(hed_ops, list):
            hed_ops = [hed_ops]
        hed_ops.append(self._def_mapper)
        return self._sidecar.validate_entries(hed_ops, error_handler=error_handler, **kwargs)
