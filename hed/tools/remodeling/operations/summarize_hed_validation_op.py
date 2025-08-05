""" Validate the HED tags in a dataset and report errors. """

import os
import pandas as pd
from hed.errors import error_reporter
from hed.errors import error_types
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary


class SummarizeHedValidationOp(BaseOp):
    """ Validate the HED tags in a dataset and report errors.

    Required remodeling parameters:
        - **summary_name** (*str*): The name of the summary.
        - **summary_filename** (*str*): Base filename of the summary.
        - **check_for_warnings** (*bool*): If true include warnings as well as errors.

    Optional remodeling parameters:
        - **append_timecode** (*bool*): If true, the timecode is appended to the base filename when summary is saved.

    The purpose of this op is to produce a summary of the HED validation errors in a file.

    """
    NAME = "summarize_hed_validation"

    PARAMS = {
        "type": "object",
        "properties": {
            "summary_name": {
                "type": "string",
                "description": "Name to use for the summary in titles."
            },
            "summary_filename": {
                "type": "string",
                "description": "Name to use for the summary file name base."
            },
            "append_timecode": {
                "type": "boolean",
                "description": "If true, the timecode is appended to the base filename so each run has a unique name."
            },
            "check_for_warnings": {
                "type": "boolean",
                "description": "If true warnings as well as errors are reported."
            }
        },
        "required": [
            "summary_name",
            "summary_filename",
            "check_for_warnings"
        ],
        "additionalProperties": False
    }

    SUMMARY_TYPE = 'hed_validation'

    def __init__(self, parameters):
        """ Constructor for the summarize HED validation operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        """
        super().__init__(parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.append_timecode = parameters.get('append_timecode', False)
        self.check_for_warnings = parameters['check_for_warnings']

    def do_op(self, dispatcher, df, name, sidecar=None) -> 'pd.DataFrame':
        """ Validate the dataframe with the accompanying sidecar, if any.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be validated.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Usually needed unless only HED tags in HED column of event file.

        Returns:
            pd.DataFrame: A copy of df

        Side effect:
            Updates the relevant summary.

        """
        df_new = df.copy()
        summary = dispatcher.summary_dicts.get(self.summary_name, None)
        if not summary:
            summary = HedValidationSummary(self)
            dispatcher.summary_dicts[self.summary_name] = summary
        summary.update_summary({'df': dispatcher.post_proc_data(df_new), 'name': name,
                                'schema': dispatcher.hed_schema, 'sidecar': sidecar})
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []


class HedValidationSummary(BaseSummary):
    """ Manager for summary of validation issues. """

    def __init__(self, sum_op):
        """ Constructor for validation issue manager.

        Parameters:
            sum_op (SummarizeHedValidationOp): Operation associated with this summary.

        """
        super().__init__(sum_op)
        self.sum_op = sum_op

    def _get_result_string(self, name, result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return a formatted string with the summary for the indicated name.

        Parameters:
            name (str):  Identifier (usually the filename) of the individual file.
            result (dict): The dictionary of the summary results indexed by name.
            indent (str): A string containing spaces used for indentation (usually 3 spaces).

        Returns:
            str: The results in a printable format ready to be saved to a text file.

        Notes:
            This gets the error list from "sidecar_issues" and "event_issues".

        """
        specifics = result.get("Specifics", {})
        sum_list = [f"{name}: [{len(specifics['sidecar_files'])} sidecar files, "
                    f"{len(specifics['event_files'])} event files]"]
        if specifics.get('is_merged'):
            sum_list = sum_list + self.get_error_list(specifics['sidecar_issues'], count_only=True)
            sum_list = sum_list + self.get_error_list(specifics['event_issues'], count_only=True)
        else:
            sum_list = sum_list + self.get_error_list(specifics['sidecar_issues'])
            if specifics['sidecar_had_issues']:
                sum_list = sum_list + self.get_error_list(specifics['sidecar_issues'], count_only=False)
            else:
                sum_list = sum_list + self.get_error_list(specifics['event_issues'], count_only=False)
        return "\n".join(sum_list)

    def update_summary(self, new_info):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_info (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary needs a "name" str, a schema, a "df", and a "Sidecar".
        """

        sidecar = new_info.get('sidecar', None)
        if sidecar and not isinstance(sidecar, Sidecar):
            sidecar = Sidecar(files=new_info['sidecar'], name=os.path.basename(sidecar))
        results = self._get_sidecar_results(
            sidecar, new_info, self.sum_op.check_for_warnings)
        if not results['sidecar_had_issues']:
            input_data = TabularInput(new_info['df'], sidecar=sidecar)
            issues = input_data.validate(new_info['schema'])
            if not self.sum_op.check_for_warnings:
                issues = error_reporter.ErrorHandler.filter_issues_by_severity(issues, error_types.ErrorSeverity.ERROR)
            issues = [error_reporter.get_printable_issue_string([issue], skip_filename=True) for issue in issues]
            results['event_issues'][new_info["name"]] = issues
            results['total_event_issues'] = len(issues)
        self.summary_dict[new_info["name"]] = results

    def get_details_dict(self, summary_info) -> dict:
        """Return the summary details from the summary_info.

        Parameters:
            summary_info (dict): Dictionary of issues

        Returns:
            dict:  Same summary_info as was passed in.

        """

        return {"Name": "", "Total events": "n/a",
                "Total files": len(summary_info.get("event_files", [])),
                "Files": summary_info.get("event_files", []),
                "Specifics": summary_info}

    def merge_all_info(self) -> dict:
        """ Create a dictionary containing all the errors in the dataset.

        Returns:
            dict: dictionary of issues organized into sidecar_issues and event_issues.

        """
        results = self.get_empty_results()
        results["is_merged"] = True
        for key, ind_results in self.summary_dict.items():
            HedValidationSummary._update_sidecar_results(results, ind_results)
            results["event_files"].append(key)
            HedValidationSummary._update_events_results(results, ind_results)
        return results

    @staticmethod
    def _update_events_results(results, ind_results):
        """ Update the issues counts in a results dictionary based on a dictionary of individual info.

        Parameters:
            results (dict):  Dictionary containing overall information.
            ind_results (dict): Dictionary to be updated.

        """
        results["total_event_issues"] += ind_results["total_event_issues"]
        for ikey, errors in ind_results["event_issues"].items():
            if ind_results["sidecar_had_issues"]:
                results["event_issues"][ikey] = \
                    f"Validation incomplete due to {ind_results['total_sidecar_issues']} sidecar issues"
            else:
                results["event_issues"][ikey] = f"{len(errors)}"

    @staticmethod
    def _update_sidecar_results(results, ind_results):
        """ Update the sidecar issue counts in a results dictionary based on dictionary of individual info.

        Parameters:
            ind_results (dict):  Info dictionary from another HedValidationSummary

        """
        results["total_sidecar_issues"] += ind_results["total_sidecar_issues"]
        results["sidecar_files"] = results["sidecar_files"] + \
            ind_results["sidecar_files"]
        for ikey, errors in ind_results["sidecar_issues"].items():
            results["sidecar_issues"][ikey] = errors

    @staticmethod
    def get_empty_results() -> dict:
        """ Return an empty results dictionary to use as a template.

        Returns:
            dict: Dictionary template of results info for the validation summary to fill in

        """
        return {"event_files": [], "total_event_issues": 0, "event_issues": {}, "is_merged": False,
                "sidecar_files": [], "total_sidecar_issues": 0, "sidecar_issues": {},
                "sidecar_had_issues": False}

    @staticmethod
    def get_error_list(error_dict, count_only=False) -> list:
        """ Convert errors produced by the HED validation into a list which includes filenames.

        Parameters:
            error_dict (dict):  Dictionary {filename: error_list} from validation.
            count_only (bool):  If False (the default), a full list of errors is included otherwise only error counts.

        Returns:
            list:  Error list of form [filenameA, issueA1, issueA2, ..., filenameB, issueB1, ...].

        """
        error_list = []
        for key, item in error_dict.items():
            if count_only and isinstance(item, list):
                error_list.append(f"{key}: {len(item)} issues")
            elif count_only:
                error_list.append(f"{key}: {item} issues")
            elif not len(item):
                error_list.append(f"{key} has no issues")
            else:
                error_list.append(f"{key}:")
                error_list = error_list + item
        return error_list

    @staticmethod
    def _format_errors(error_list, name, errors, indent):
        """ Reformat errors to have appropriate indentation for readability.

        Parameters:
            error_list (list):  Overall list of error to append these errors to.
            name (str): Name of the file which generated these errors.
            errors (list): List of error associated with filename.
            indent (str):  Spaces used to control indentation.

        """
        error_list.append(f"{indent}{name} issues:")
        for this_item in errors:
            error_list.append(
                f"{indent * 2}{HedValidationSummary._format_error(this_item)}")

    @staticmethod
    def _format_error(error):
        """ Format a HED error in a string suitable for summary display.

        Parameters:
            error (dict): Represents a single HED error with its standard keys.

        Returns:
            str: String version of the error.


        """
        if not error:
            return ""
        error_str = error['code']
        error_locations = []
        HedValidationSummary.update_error_location(
            error_locations, "row", "ec_row", error)
        HedValidationSummary.update_error_location(
            error_locations, "column", "ec_column", error)
        HedValidationSummary.update_error_location(error_locations, "sidecar column",
                                                   "ec_sidecarColumnName", error)
        HedValidationSummary.update_error_location(
            error_locations, "sidecar key", "ec_sidecarKeyName", error)
        location_str = ",".join(error_locations)
        if location_str:
            error_str = error_str + f"[{location_str}]"
        error_str = error_str + f": {error['message']}"
        return error_str

    @staticmethod
    def update_error_location(error_locations, location_name, location_key, error):
        """ Updates error information about where an error occurred in sidecar or columnar file.

        Parameters:
            error_locations (list): List of error locations detected so far is this error.
            location_name (str): Error location name, for example 'row', 'column', or 'sidecar column'.
            location_key (str): Standard key name for this location in the dictionary for an error.
            error (dict): Dictionary containing the information about this error.

        """
        if location_key in error:
            error_locations.append(f"{location_name}={error[location_key][0]}")

    @staticmethod
    def _get_sidecar_results(sidecar, new_info, check_for_warnings):
        """ Return a dictionary of errors detected in a sidecar.

        Parameters:
            sidecar (Sidecar): The Sidecar to validate.
            new_info (dict): Dictionary with information such as the schema needed for validation.
            check_for_warnings (bool): If False, filter out warning errors.

        Returns:
            dict: Results of the validation.

        """
        results = HedValidationSummary.get_empty_results()
        results["event_files"].append(new_info["name"])
        results["event_issues"][new_info["name"]] = []
        if sidecar:
            results["sidecar_files"].append(sidecar.name)
            results["sidecar_issues"][sidecar.name] = []
            sidecar_issues = sidecar.validate(new_info.get('schema', None))
            filtered_issues = error_reporter.ErrorHandler.filter_issues_by_severity(sidecar_issues,
                                                                                    error_types.ErrorSeverity.ERROR)
            if filtered_issues:
                results["sidecar_had_issues"] = True
            if not check_for_warnings:
                sidecar_issues = filtered_issues
            str_issues = [error_reporter.get_printable_issue_string([issue],
                                                                    skip_filename=True) for issue in sidecar_issues]
            results['sidecar_issues'][sidecar.name] = str_issues
            results['total_sidecar_issues'] = len(sidecar_issues)
        return results
