""" A group of BIDS files with specified suffix name. """

import os
import pandas as pd

from hed.errors.error_reporter import ErrorHandler
from hed.validator.sidecar_validator import SidecarValidator
from hed.tools.analysis.tabular_summary import TabularSummary
from hed.tools.bids.bids_tabular_file import BidsTabularFile
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile
from hed.tools.util import io_util


class BidsFileGroup:
    """ Container for BIDS files with a specified suffix.

    Attributes:
        suffix (str):             The file suffix specifying the class of file represented in this group (e.g., events).
        sidecar_dict (dict):      A dictionary of sidecars associated with this suffix .
        datafile_dict (dict):     A dictionary with values either BidsTabularFile or BidsTimeseriesFile.
        sidecar_dir_dict (dict):  Dictionary whose keys are directory paths and values are list of sidecars in the
            corresponding directory.

    """

    def __init__(self, root_path, file_list, suffix="events"):
        """ Constructor for a BidsFileGroup.

        Parameters:
            file_list (list):  List of paths to the relevant tsv and json files.
            suffix (str):     Suffix indicating the type this group represents (e.g. events, or channels, etc.).
        """

        self.suffix = suffix
        ext_dict = io_util.separate_by_ext(file_list)
        self.bad_files = {}
        self.sidecar_dict = {}
        self.sidecar_dir_dict = {}
        self.datafile_dict = {}
        self.has_hed = False
        self._make_sidecar_dict(ext_dict.get('.json', []))
        self._make_dir_dict(root_path)
        self._make_datafile_dict(root_path, ext_dict.get('.tsv', []))

    def summarize(self, value_cols=None, skip_cols=None):
        """ Return a BidsTabularSummary of group files.

        Parameters:
            value_cols (list):  Column names designated as value columns.
            skip_cols (list):   Column names designated as columns to skip.

        Returns:
            Union[TabularSummary, None]:  A summary of the number of values in different columns if tabular group.

        Notes:
            - The columns that are not value_cols or skip_col are summarized by counting
        the number of times each unique value appears in that column.

        """
        info = TabularSummary(value_cols=value_cols, skip_cols=skip_cols)
        info.update(list(self.datafile_dict.keys()))
        return info

    def validate(self, hed_schema, extra_def_dicts=None, check_for_warnings=False):
        """ Validate the sidecars and datafiles and return a list of issues.

        Parameters:
            hed_schema (HedSchema):  Schema to apply to the validation.
            extra_def_dicts (DefinitionDict):  Extra definitions that come from outside.
            check_for_warnings (bool):  If True, include warnings in the check.

        Returns:
            list:  A list of validation issues found. Each issue is a dictionary.
        """
        error_handler = ErrorHandler(check_for_warnings)
        issues = []
        issues += self.validate_sidecars(hed_schema, extra_def_dicts=extra_def_dicts,  error_handler=error_handler)
        issues += self.validate_datafiles(hed_schema, extra_def_dicts=extra_def_dicts,
                                          error_handler=error_handler)
        return issues

    def validate_sidecars(self, hed_schema, extra_def_dicts=None, error_handler=None):
        """ Validate merged sidecars.

        Parameters:
            hed_schema (HedSchema):  HED schema for validation.
            extra_def_dicts (DefinitionDict): Extra definitions.
            error_handler (ErrorHandler):  Error handler to use.

        Returns:
            list:   A list of validation issues found. Each issue is a dictionary.
        """

        if not error_handler:
            error_handler = ErrorHandler(False)
        issues = []
        validator = SidecarValidator(hed_schema)
        for sidecar in self.sidecar_dict.values():
            issues += validator.validate(sidecar.contents, extra_def_dicts=extra_def_dicts,
                                         name=sidecar.file_path, error_handler=error_handler)
        return issues

    def validate_datafiles(self, hed_schema, extra_def_dicts=None, error_handler=None):
        """ Validate the datafiles and return an error list.

        Parameters:
            hed_schema (HedSchema):  Schema to apply to the validation.
            extra_def_dicts (DefinitionDict):  Extra definitions that come from outside.
            error_handler (ErrorHandler):  Error handler to use.

        Returns:
            list:    A list of validation issues found. Each issue is a dictionary.

        Notes: This will clear the contents of the datafiles if they were not previously set.
        """

        if not error_handler:
            error_handler = ErrorHandler(False)
        issues = []
        for data_obj in self.datafile_dict.values():
            if not data_obj.has_hed:
                continue
            had_contents = data_obj.contents
            data_obj.set_contents(overwrite=False)
            issues += data_obj.contents.validate(hed_schema, extra_def_dicts=extra_def_dicts, name=data_obj.file_path,
                                                 error_handler=error_handler)
            if not had_contents:
                data_obj.clear_contents()
        return issues

    def _make_dir_dict(self, root_path):
        """ Create dictionary directory paths keys and assign to self.sidecar_dir_dict.

        Parameters:
            root_path (str):  The root path of the BIDS dataset.

        Note: Creates dictionary with directories as keys and list of sidecars in that directory as values.

        """
        self.sidecar_dir_dict = {}
        for root, dirs, files in os.walk(root_path, topdown=True):
            sidecar_list = []
            for r_file in files:
                file_path = os.path.join(os.path.realpath(root), r_file)
                if file_path in self.sidecar_dict:
                    sidecar_list.append(file_path)
            if not sidecar_list:
                continue
            self.sidecar_dir_dict[os.path.realpath(root)] = sidecar_list

    def _make_datafile_dict(self, root_path, tsv_list):
        """ Sets the dictionary of BIDS Tabular file objects for the give list of tabular files.

        Parameters:
            root_path (str):  The root path of the BIDS dataset.
            tsv_list (list):  A list of paths to the tabular files.

        """
        self.datafile_dict = {}
        for file_path in tsv_list:
            tsv_obj = BidsTabularFile(file_path)
            if os.path.getsize(file_path) == 0:
                continue
            if tsv_obj.bad:
                self.bad_files[file_path] = f"{file_path} violates BIDS naming convention for {str(tsv_obj.bad)}"
                continue
            tsv_obj.set_sidecar(self._get_tsv_sidecar(root_path, tsv_obj))
            try:
                column_headers = list(pd.read_csv(file_path, sep='\t', nrows=0).columns)
            except Exception as e:
                self.bad_files[file_path] = f"{file_path} does not have a valid column header: {str(e)}"
                continue
            if "HED" in column_headers or "HED_assembled" in column_headers or tsv_obj.sidecar:
                self.has_hed = True
                tsv_obj.has_hed = True
            self.datafile_dict[os.path.realpath(file_path)] = tsv_obj

    def _get_tsv_sidecar(self, root_path, tsv_obj):
        """ Return the merged Sidecar for the tsv_obj

        Parameters:
            root_path (str):  The root path of the BIDS dataset.
            tsv_obj (BidsTabularFile):  The BIDS tabular file to get the sidecars for.

        Returns:
            Union[Sidecar, None]:  The merged Sidecar for the tsv_obj, if any.

        """
        path_components = [root_path] + io_util.get_path_components(root_path, tsv_obj.file_path)
        sidecar_list = []
        current_path = ''
        for comp in path_components:
            current_path = os.path.realpath(os.path.join(current_path, comp))
            candidate = self._get_sidecar_for_obj(tsv_obj, current_path)
            if candidate:
                sidecar_list.append(candidate)
        if len(sidecar_list) > 1:
            merged_name = "merged_" + io_util.get_basename(tsv_obj.file_path) + '.json'
            return BidsSidecarFile.merge_sidecar_list(sidecar_list, name=merged_name)
        elif len(sidecar_list) == 1:
            return sidecar_list[0].contents
        return None

    def _get_sidecar_for_obj(self, tsv_obj, current_path):
        """ Return a single BidsSidecarFile relevant to obj from the sidecars in the current path.

        Parameters:
            tsv_obj (BidsTabularFile): A file whose sidecars are to be found.
            current_path (str):  The path of the directory whose sidecars are to be checked.

        Returns:
            Union[BidsSidecarFile, None]:  The BidsSidecarFile in current_path relevant to obj, if any.

         """
        sidecar_paths = self.sidecar_dir_dict.get(current_path, [])
        if not sidecar_paths:
            return None
        candidates = []
        for sidecar_path in sidecar_paths:
            sidecar = self.sidecar_dict[sidecar_path]
            if sidecar.is_sidecar_for(tsv_obj):
                candidates.append(sidecar)
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            for candidate in candidates:
                self.bad_files[candidate] = f"Sidecar {str(candidate.file_path)} conflicts with other sidecars for {tsv_obj.file_path} in {current_path}"
            return None
        return None

    def _make_sidecar_dict(self, json_files):
        """ Create a dictionary of BidsSidecarFile objects for the specified entity type and set contents.

        Parameters:
            json_files (list):  A list of paths to the json files.

        Notes: sets the
            dict:   a dictionary of BidsSidecarFile objects keyed by real path for the specified suffix type.

        """

        self.sidecar_dict = {}
        for file_path in json_files:
            if os.path.getsize(file_path) == 0:
                continue
            sidecar_file =  BidsSidecarFile(os.path.realpath(file_path))
            if sidecar_file.bad:
                self.bad_files[file_path] = f"{file_path} violates BIDS naming convention for {str(sidecar_file.bad)}"
                continue
            sidecar_file.set_contents(overwrite=False)
            if sidecar_file.has_hed:
                self.sidecar_dict[os.path.realpath(file_path)] = sidecar_file
                self.has_hed = True

    @staticmethod
    def create_file_group(root_path, file_list, suffix):
        file_group = BidsFileGroup(root_path, file_list, suffix=suffix)
        if not file_group.sidecar_dict and not file_group.datafile_dict:
            return None
        return file_group
