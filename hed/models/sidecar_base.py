import copy
from hed.models.column_metadata import ColumnMetadata
from hed.errors.error_types import ErrorContext
from hed.errors import error_reporter
from hed.errors import ErrorHandler
from hed.models.hed_string import HedString
from hed.models.def_mapper import DefMapper
from hed.models.hed_ops import translate_ops, apply_ops
from hed.models.definition_dict import DefinitionDict
from functools import partial


class SidecarBase:
    """ Baseclass for specialized spreadsheet sidecars

        To subclass this class, you'll want to override at the minimum:
        _hed_string_iter
        _set_hed_string
        validate_structure
        column_data property <- This is the only truly mandatory one

    """
    def __init__(self, name=None, hed_schema=None):
        """ Initialize a sidecar baseclass

        Parameters:
            name (str or None): Optional name identifying this sidecar, generally a filename.
            hed_schema(HedSchema or None): The schema to use by default in identifying tags
        """
        self.name = name
        self._schema = hed_schema
        # Expected to be called in subclass after data is loaded
        # self.def_dict = self.extract_definitions()

    @property
    def column_data(self):
        """ Generates the list of ColumnMetadata for this sidecar

        Returns:
            list(ColumnMetadata): the list of column metadata defined by this sidecar
        """
        return []

    def _hed_string_iter(self, tag_funcs, error_handler):
        """ Low level function to retrieve hed string in sidecar

        Parameters:
            tag_funcs(list): A list of functions to apply to returned strings
            error_handler(ErrorHandler): Error handler to use for context

        Yields:
            tuple:
                string(HedString): The retrieved and modified string
                position(tuple): The location of this hed string.  Black box.
                issues(list): A list of issues running the tag_funcs.
        """
        yield

    def _set_hed_string(self, new_hed_string, position):
        """ Low level function to update hed string in sidecar

        Parameters:
            new_hed_string (str or HedString): The new hed_string to replace the value at position.
            position (tuple):   The value returned from hed_string_iter.
        """
        return

    def validate_structure(self, error_handler):
        """ Validate the raw structure of this sidecar.

        Parameters:
            error_handler(ErrorHandler): The error handler to use for error context

        Returns:
            issues(list): A list of issues found with the structure
        """
        return []

    def __iter__(self):
        """ An iterator to go over the individual column metadata.

        Returns:
            iterator: An iterator over the column metadata values.

        """
        return iter(self.column_data)

    def hed_string_iter(self, hed_ops=None, error_handler=None, expand_defs=False, remove_definitions=False,
                        allow_placeholders=True, extra_def_dicts=None, **kwargs):
        """ Iterator over hed strings in columns.

        Parameters:
            hed_ops (func, HedOps, list):  A HedOps, funcs or list of these to apply to the hed strings
                                            before returning
            error_handler (ErrorHandler): The error handler to use for context, uses a default one if none.
            expand_defs (bool): If True, expand all def tags located in the strings.
            remove_definitions (bool): If True, remove all definitions found in the string.
            allow_placeholders (bool): If False, placeholders will be marked as validation warnings.
            extra_def_dicts (DefinitionDict, list, None): Extra dicts to add to the list.
            kwargs: See models.hed_ops.translate_ops or the specific hed_ops for additional options.

        Yields:
            tuple:
                - HedString: A HedString at a given column and key position.
                - tuple: Indicates where hed_string was loaded from so it can be later set by the user
                - list: A list of issues found performing ops. Each issue is a dictionary.

        """
        if error_handler is None:
            error_handler = ErrorHandler()
        hed_ops = self._standardize_ops(hed_ops)
        if expand_defs or remove_definitions:
            self._add_definition_mapper(hed_ops, extra_def_dicts)
        tag_funcs = translate_ops(hed_ops, hed_schema=self._schema, error_handler=error_handler,
                                  expand_defs=expand_defs, allow_placeholders=allow_placeholders,
                                  remove_definitions=remove_definitions, **kwargs)

        return self._hed_string_iter(tag_funcs, error_handler)

    def set_hed_string(self, new_hed_string, position):
        """ Set a provided column/category key/etc.

        Parameters:
            new_hed_string (str or HedString): The new hed_string to replace the value at position.
            position (tuple):   The (HedString, str, list) tuple returned from hed_string_iter.

        """
        return self._set_hed_string(new_hed_string, position)

    def _add_definition_mapper(self, hed_ops, extra_def_dicts=None):
        """ Add a DefMapper if the hed_ops list doesn't have one.

        Parameters:
            hed_ops (list):  A list of HedOps
            extra_def_dicts (list):  DefDicts from outside.

        Returns:
            DefMapper:  A shallow copy of the hed_ops list with a DefMapper added if there wasn't one.

        """
        def_mapper_list = [hed_op for hed_op in hed_ops if isinstance(hed_op, DefMapper)]

        if not def_mapper_list:
            def_dicts = self.get_def_dicts(extra_def_dicts)
            def_mapper = DefMapper(def_dicts)
            hed_ops.append(def_mapper)
            return def_mapper
        return def_mapper_list[0]

    @staticmethod
    def _standardize_ops(hed_ops):
        if not isinstance(hed_ops, list):
            hed_ops = [hed_ops]
        return hed_ops.copy()

    def get_def_dicts(self, extra_def_dicts=None):
        """ Returns the definition dict for this sidecar.

        Parameters:
            extra_def_dicts (list, DefinitionDict, or None): Extra dicts to add to the list.

        Returns:
            list: A list with the sidecar def_dict plus any found in extra_def_dicts.

        """
        def_dicts = [self.def_dict]
        if extra_def_dicts:
            if not isinstance(extra_def_dicts, list):
                extra_def_dicts = [extra_def_dicts]
            def_dicts += extra_def_dicts
        return def_dicts

    def validate_entries(self, hed_ops=None, name=None, extra_def_dicts=None,
                         error_handler=None, **kwargs):
        """ Run the given hed_ops on all columns in this sidecar.

        Parameters:
            hed_ops (list, func, or HedOps): A HedOps, func or list of these to apply to hed strings in this sidecar.
            name (str): If present, will use this as the filename for context, rather than using the actual filename
                Useful for temp filenames.
            extra_def_dicts (DefinitionDict, list, or None): If present use these in addition to sidecar's def dicts.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default one if none passed in.
            kwargs: See models.hed_ops.translate_ops or the specific hed_ops for additional options.

        Returns:
            list: The list of validation issues found. Individual issues are in the form of a dict.

        """
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()
        if not name:
            name = self.name
        if name:
            error_handler.push_error_context(ErrorContext.FILE_NAME, name, False)

        all_validation_issues = self.validate_structure(error_handler)

        # Early out major errors so the rest of our code can assume they won't happen.
        if all_validation_issues:
            return all_validation_issues

        hed_ops = self._standardize_ops(hed_ops)
        def_mapper = self._add_definition_mapper(hed_ops, extra_def_dicts)
        all_validation_issues += def_mapper.issues

        for hed_string, key_name, issues in self.hed_string_iter(hed_ops=hed_ops, allow_placeholders=True,
                                                                 error_handler=error_handler, **kwargs):
            self.set_hed_string(hed_string, key_name)
            all_validation_issues += issues

        # Finally check what requires the final mapped data to check
        for column_data in self.column_data:
            validate_pound_func = partial(self._validate_pound_sign_count, column_type=column_data.column_type)
            _, issues = apply_ops(column_data.hed_dict, validate_pound_func)
            all_validation_issues += issues
        all_validation_issues += self.def_dict.get_definition_issues()
        if name:
            error_handler.pop_error_context()
        return all_validation_issues

    def extract_definitions(self, hed_schema=None, error_handler=None):
        """ Gather and validate definitions in metadata.

        Parameters:
            error_handler (ErrorHandler): The error handler to use for context, uses a default one if None.
            hed_schema (HedSchema or None): The schema to used to identify tags.

        Returns:
            DefinitionDict: Contains all the definitions located in the column.
            issues: List of issues encountered in extracting the definitions. Each issue is a dictionary.

        """
        if error_handler is None:
            error_handler = ErrorHandler()
        new_def_dict = DefinitionDict()
        hed_ops = []
        hed_ops.append(hed_schema)
        hed_ops.append(new_def_dict)

        all_issues = []
        for hed_string, key_name, issues in self.hed_string_iter(hed_ops=hed_ops, allow_placeholders=True,
                                                                 error_handler=error_handler):
            all_issues += issues

        return new_def_dict

    def _validate_pound_sign_count(self, hed_string, column_type):
        """ Check if a given hed string in the column has the correct number of pound signs.

        Parameters:
            hed_string (str or HedString): HED string to be checked.

        Returns:
            list: Issues due to pound sign errors. Each issue is a dictionary.

        Notes:
            Normally the number of # should be either 0 or 1, but sometimes will be higher due to the
            presence of definition tags.

        """
        # Make a copy without definitions to check placeholder count.
        expected_count, error_type = ColumnMetadata.expected_pound_sign_count(column_type)
        hed_string_copy = copy.deepcopy(hed_string)
        hed_string_copy.remove_definitions()

        if hed_string_copy.lower().count("#") != expected_count:
            return ErrorHandler.format_error(error_type, pound_sign_count=str(hed_string_copy).count("#"))

        return []
