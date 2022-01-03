"""
This module contains the HedValidator class which is used to validate the tags in a HED string or a file. The file
types include .tsv, .txt,, and .xlsx. To get the validation issues after creating a HedValidator class call
the get_validation_issues() function.

"""

from hed.errors.error_types import ValidationErrors
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ErrorContext

from hed.models.hed_string import HedString
from hed.validator.tag_validator import TagValidator
from functools import partial


class BidsValidator:
    def __init__(self, hed_schema=None):
        """Constructor for the BidsValidator class.

        Parameters
        ----------
        hed_schema: HedSchema
            HedSchema object to use to use for validation

        Returns
        -------
        BidsValidator object
            A HedValidator object.

        """

        self._hed_schema = hed_schema


    def validate_events(self, bids_validators, name=None, error_handler=None, check_for_warnings=True, **kwargs):
        """Run the given validators on a BIDS dataset
         Parameters
         ----------
         bids_validators : [func or validator like] or func or validator like
             A validator or list of validators to apply to the hed strings in this sidecar.
         name: str
             If present, will use this as the filename for context, rather than using the actual filename
             Useful for temp filenames.
         error_handler : ErrorHandler or None
             Used to report errors.  Uses a default one if none passed in.
         check_for_warnings: bool
             If True this will check for and return warnings as well
         kwargs:
             See util.translate_ops or the specific validators for additional options
         Returns
         -------
         validation_issues: [{}]
             The list of validation issues found
         """
        if not name:
            name = self.name
        if not isinstance(bids_validators, list):
            validators = [bids_validators]

        if error_handler is None:
            error_handler = ErrorHandler()

        error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        validation_issues = self.get_def_and_mapper_issues(error_handler, check_for_warnings)
        validators = validators.copy()
        validation_issues += self._run_validators(validators, error_handler=error_handler,
                                                  check_for_warnings=check_for_warnings, **kwargs)
        error_handler.pop_error_context()

        return validation_issues

