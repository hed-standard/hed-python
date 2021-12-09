import os

from hed.models.def_dict import DefDict
from hed.models.column_mapper import ColumnMapper
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.errors.error_types import ErrorContext, ErrorSeverity
from hed.errors.error_reporter import ErrorHandler
from hed.models import model_constants
from hed.models.util import translate_ops
from hed.models.onset_mapper import OnsetMapper
from hed.models.hed_string import HedString
from hed.tools.io_utils import get_dir_dictionary, get_file_list, get_path_components
from hed.tools.bids_file import BIDSFile


class BIDSFiles:
    """Represents the event files and their sidecars in a BIDS dataset."""

    def __init__(self, root_path, suffix='events', extensions=['.tsv']):
        self.root_path = root_path
        self.suffix = suffix
        self.dataset_description = ''
        self.json_files = self.get_file_dict()
        self.data_files = self.get_file_dict(extensions=extensions)

        self.dir_dict = get_dir_dictionary(self.root_path, name_suffix=self.suffix, extensions=['.json'])

        for bids_obj in self.json_files.values():
            bids_obj.set_sidecars(self._set_sidecars_from_path(bids_obj))
        for bids_obj in self.data_files.values():
            bids_obj.set_sidecars(self._set_sidecars_from_path(bids_obj))

    def get_file_dict(self, extensions=['.json']):
        files = get_file_list(self.root_path, name_suffix='_'+self.suffix, extensions=extensions)
        file_dict = {}
        for file in files:
            file_dict[os.path.abspath(file)] = BIDSFile(file)
        return file_dict

    def get_sidecar(self, obj, sidecars):
        if not sidecars:
            return None
        for sidecar in sidecars:
            sidecar_obj = self.json_files[sidecar]
            if sidecar_obj.is_parent(obj):
                return sidecar
        return None

    def _set_sidecars_from_path(self, obj):
        sidecar_list = []
        current_path = ''
        for comp in get_path_components(obj.file_path, self.root_path):
            current_path = os.path.abspath(os.path.join(current_path, comp))
            sidecars = self.dir_dict.get(current_path, None)
            sidecar = self.get_sidecar(obj, sidecars)
            if sidecar:
                sidecar_list.append(sidecar)
        return sidecar_list

    def validate_dataset(self, validators, name=None, error_handler=None, check_for_warnings=True, **kwargs):
        """Run the given validators on a BIDS dataset

         Parameters
         ----------

         validators : [func or validator like] or func or validator like
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
        # if not name:
        #     name = self.name
        # if not isinstance(validators, list):
        #     validators = [validators]
        #
        # if error_handler is None:
        #     error_handler = ErrorHandler()
        #
        # error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        # validation_issues = self.get_def_and_mapper_issues(error_handler, check_for_warnings)
        # validators = validators.copy()
        # validation_issues += self._run_validators(validators, error_handler=error_handler,
        #                                           check_for_warnings=check_for_warnings, **kwargs)
        # error_handler.pop_error_context()
        #
        # return validation_issues

    def get_def_and_mapper_issues(self, error_handler, check_for_warnings=False):
        """
            Returns formatted issues found with definitions and columns.
        Parameters
        ----------
        error_handler : ErrorHandler
            The error handler to use
        check_for_warnings: bool
            If True this will check for and return warnings as well
        Returns
        -------
        issues_list: [{}]
            A list of definition and mapping issues.
        """
        # issues = []
        # issues += self.file_def_dict.get_definition_issues()
        #
        # # Gather any issues from the mapper for things like missing columns.
        # mapper_issues = self._mapper.get_column_mapping_issues()
        # error_handler.add_context_to_issues(mapper_issues)
        # issues += mapper_issues
        # if not check_for_warnings:
        #     issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
        # return issues


if __name__ == '__main__':
    path = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s_inheritance'
    bids = BIDSFiles(path)

    for file_obj in bids.json_files.values():
        print(file_obj)

    for file_obj in bids.data_files.values():
        print(file_obj)
