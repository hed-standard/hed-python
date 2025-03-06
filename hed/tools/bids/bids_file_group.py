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
        root_path (str):          Real root path of the Bids dataset.
        suffix (str):             The file suffix specifying the class of file represented in this group (e.g., events).
        sidecar_dict (dict):      A dictionary of sidecars associated with this suffix .
        datafile_dict (dict):     A dictionary with values either BidsTabularFile or BidsTimeseriesFile.
        sidecar_dir_dict (dict):  Dictionary whose keys are directory paths and values are list of sidecars in the
            corresponding directory.

    """

    def __init__(self, root_path, file_list, suffix="_events"):
        """ Constructor for a BidsFileGroup.

        Parameters:
            root_path (str):  Path of the root of the BIDS dataset.
            file_list (list):  List of paths to the relevant tsv and json files.
            suffix (str):     Suffix indicating the type this group represents (e.g. events, or channels, etc.).
        """
        self.root_path = os.path.realpath(root_path)
        self.suffix = suffix
        [tsv_list, json_list] = self.separate_file_list(file_list)
        self.sidecar_dict = self._make_sidecar_dict(json_list)
        self.sidecar_dir_dict = self._make_dir_dict()
        self.datafile_dict = self._make_datafile_dict(tsv_list)

    def summarize(self, value_cols=None, skip_cols=None):
        """ Return a BidsTabularSummary of group files.

        Parameters:
            value_cols (list):  Column names designated as value columns.
            skip_cols (list):   Column names designated as columns to skip.

        Returns:
            TabularSummary or None:  A summary of the number of values in different columns if tabular group.

        Notes:
            - The columns that are not value_cols or skip_col are summarized by counting
        the number of times each unique value appears in that column.

        """
        info = TabularSummary(value_cols=value_cols, skip_cols=skip_cols)
        info.update(list(self.datafile_dict.keys()))
        return info

    def validate(self, hed_schema, extra_def_dicts=None, check_for_warnings=True, keep_contents=False):
        """ Validate the sidecars and datafiles and return a list of issues.

        Parameters:
            hed_schema (HedSchema):  Schema to apply to the validation.
            extra_def_dicts (DefinitionDict):  Extra definitions that come from outside.
            check_for_warnings (bool):  If True, include warnings in the check.
            keep_contents (bool):       If True, the underlying data files are read and their contents retained.

        Returns:
            list:  A list of validation issues found. Each issue is a dictionary.
        """
        issues = []
        issues += self.validate_sidecars(hed_schema, extra_def_dicts=extra_def_dicts,
                                         check_for_warnings=check_for_warnings)
        issues += self.validate_datafiles(hed_schema, extra_def_dicts=extra_def_dicts,
                                          check_for_warnings=check_for_warnings, keep_contents=keep_contents)
        return issues

    def validate_sidecars(self, hed_schema, extra_def_dicts=None, check_for_warnings=True):
        """ Validate merged sidecars.

        Parameters:
            hed_schema (HedSchema):  HED schema for validation.
            extra_def_dicts (DefinitionDict): Extra definitions.
            check_for_warnings (bool):  If True, include warnings in the check.

        Returns:
            list:   A list of validation issues found. Each issue is a dictionary.
        """

        error_handler = ErrorHandler(check_for_warnings)
        issues = []
        validator = SidecarValidator(hed_schema)

        for sidecar in self.sidecar_dict.values():
            name = os.path.basename(sidecar.file_path)
            issues += validator.validate(sidecar.contents, extra_def_dicts=extra_def_dicts, name=name,
                                         error_handler=error_handler)
        return issues

    def validate_datafiles(self, hed_schema, extra_def_dicts=None, check_for_warnings=True, keep_contents=False):
        """ Validate the datafiles and return an error list.

        Parameters:
            hed_schema (HedSchema):  Schema to apply to the validation.
            extra_def_dicts (DefinitionDict):  Extra definitions that come from outside.
            check_for_warnings (bool):  If True, include warnings in the check.
            keep_contents (bool):       If True, the underlying data files are read and their contents retained.

        Returns:
            list:    A list of validation issues found. Each issue is a dictionary.

        """

        error_handler = ErrorHandler(check_for_warnings)
        issues = []
        for data_obj in self.datafile_dict.values():
            data_obj.set_contents(overwrite=False)
            name = os.path.basename(data_obj.file_path)
            issues += data_obj.contents.validate(hed_schema, extra_def_dicts=extra_def_dicts, name=name,
                                                 error_handler=error_handler)
            if not keep_contents:
                data_obj.clear_contents()
        return issues

    def _make_dir_dict(self):
        """ Create dictionary directory paths keys.

        Returns:
            dict:  Dictionary with directories as keys and list of sidecars in that directory as values.

        """

        dir_dict = {}
        for root, dirs, files in os.walk(self.root_path, topdown=True):
            sidecar_list = []
            for r_file in files:
                file_path = os.path.join(os.path.realpath(root), r_file)
                if file_path in self.sidecar_dict:
                    sidecar_list.append(os.path.join(file_path))
            if not sidecar_list:
                continue
            dir_dict[os.path.realpath(root)] = sidecar_list
        return dir_dict

    def _make_datafile_dict(self, tsv_list):
        """ Get a dictionary of BIDS Tabular file objects for the give list of tabular files.

        Parameters:
            tsv_list (list):  A list of paths to the tabular files.

        Returns:
            dict:   A dictionary of BidsTabularFile objects keyed by real path.

        """
        file_dict = {}
        for file in tsv_list:
            tsv_obj = BidsTabularFile(file)
            tsv_obj.set_sidecar(self.get_tsv_sidecar(tsv_obj))
            column_headers = list(pd.read_csv(file, sep='\t', nrows=0).columns)
            if "HED" not in column_headers and tsv_obj.sidecar is None:
                continue
            file_dict[os.path.realpath(file)] = tsv_obj
        return file_dict

    def get_tsv_sidecar(self, tsv_obj):
        """ Return the merged Sidecar for the tsv_obj

        Parameters:
            tsv_obj (BidsTabularFile):  The BIDS tabular file to get the sidecars for.

        Returns:
            Sidecar or None:  The merged Sidecar for the tsv_obj, if any.

        """
        path_components = [self.root_path] + io_util.get_path_components(self.root_path, tsv_obj.file_path)
        sidecar_list = []
        current_path = ''
        for comp in path_components:
            current_path = os.path.realpath(os.path.join(current_path, comp))
            candidate = self._get_sidecar_for_obj(tsv_obj, current_path)
            if candidate:
                sidecar_list.append(candidate)
        if len(sidecar_list) > 1:
            merged_name = "merged_" + io_util.get_basename(tsv_obj.file_path) + '.json'
            return BidsSidecarFile.get_merged_sidecar(sidecar_list, name=merged_name)
        elif len(sidecar_list) == 1:
            return sidecar_list[0].contents
        return None

    def _get_sidecar_for_obj(self, tsv_obj, current_path):
        """ Return a single BidsSidecarFile relevant to obj from the sidecars in the current path.

        Parameters:
            tsv_obj (BidsTabularFile): A file whose sidecars are to be found.
            current_path (str):  The path of the directory whose sidecars are to be checked.

        Returns:
            BidsSidecarFile or None:  The BidsSidecarFile in current_path relevant to obj, if any.

         """
        sidecar_paths = self.sidecar_dir_dict.get(current_path, [])
        if not sidecar_paths:
            return None
        candidates = []
        for sidecar_path in sidecar_paths:
            sidecar = self.sidecar_dict[sidecar_path]
            if sidecar.is_sidecar_for(tsv_obj):
                candidates.append(sidecar)
        if len(candidates) > 1:
            paths = sorted(file.file_path for file in candidates)
            raise Exception({"code": "MULTIPLE_INHERITABLE_FILES", "location": paths[0], "affects": tsv_obj.file_path,
                            "issueMessage": f"Candidate files: {paths}"})
        if candidates:
            return candidates[0]
        return None

    @staticmethod
    def separate_file_list(file_list):
        """ Separate a list of files into tsv and json files.

        Parameters:
            file_list (list):  A list of file paths.

        Returns:
            tuple:  A tuple of lists of tsv and json files.

        """
        tsv_files = []
        json_files = []
        for file in file_list:
            if file.endswith('.tsv'):
                tsv_files.append(file)
            elif file.endswith('.json'):
                json_files.append(file)
        return tsv_files, json_files

    @staticmethod
    def _make_sidecar_dict(json_files):
        """ Create a dictionary of BidsSidecarFile objects for the specified entity type.

        Parameters:
            json_files (list):  A list of paths to the json files.

        Returns:
            dict:   a dictionary of BidsSidecarFile objects keyed by real path for the specified suffix type.

        Notes:
            - This function creates the sidecars, but does not set their contents.

        """

        file_dict = {}
        for file_path in json_files:
            sidecar_file =  BidsSidecarFile(os.path.realpath(file_path))
            sidecar_file.set_contents(overwrite=False)
            if sidecar_file.has_hed:
                file_dict[os.path.realpath(file_path)] = sidecar_file
        return file_dict

    @staticmethod
    def _get_candidate(candidate_list, tsv_file):
        if not candidate_list:
            return None
        candidates = []
        for sidecar_candidate in candidate_list:
            if sidecar_candidate.is_sidecar_for(tsv_file):
                candidates.append(sidecar_candidate)
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) == 0:
            return None
        else:
            paths = sorted(file.file_path for file in candidates)
            raise Exception({"code": "MULTIPLE_INHERITABLE_FILES", "location": paths[0], "affects": tsv_file.file_path,
                            "issueMessage": f"Candidate files: {paths}"})

    @staticmethod
    def create_file_group(root_path, file_list, suffix):
        file_group = BidsFileGroup(root_path, file_list, suffix=suffix)
        if not file_group.sidecar_dict and not file_group.sidecar_dict:
            return None
        return file_group