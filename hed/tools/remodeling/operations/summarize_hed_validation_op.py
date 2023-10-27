""" Validate the HED tags in a dataset and report errors. """

import os
from hed.errors import ErrorSeverity, ErrorHandler, get_printable_issue_string
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

    The purpose of this op is to produce a summary of the HED validation errors in a file.

    """

    PARAMS = {
        "operation": "summarize_hed_validation",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str
        },
        "optional_parameters": {
            "append_timecode": bool,
            "check_for_warnings": bool
        }
    }

    SUMMARY_TYPE = 'hed_validation'

    def __init__(self, parameters):
        """ Constructor for the summarize hed validation operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        :raises KeyError:
            - If a required parameter is missing.
            - If an unexpected parameter is provided.

        :raises TypeError:
            - If a parameter has the wrong type.

        """
        super().__init__(self.PARAMS, parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.append_timecode = parameters.get('append_timecode', False)
        self.check_for_warnings = parameters.get('check_for_warnings', False)

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Validate the dataframe with the accompanying sidecar, if any.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be validated.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Usually needed unless only HED tags in HED column of event file.

        Returns:
            DataFrame: A copy of df

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


class HedValidationSummary(BaseSummary):

    def __init__(self, sum_op):
        super().__init__(sum_op)
        self.check_for_warnings = sum_op.check_for_warnings

    def _get_result_string(self, name, result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return a formatted string with the summary for the indicated name.

        Parameters:
            name (str):  Identifier (usually the filename) of the individual file.
            result (dict): The dictionary of the summary results indexed by name.
            indent (str): A string containing spaces used for indentation (usually 3 spaces).

        Returns:
            str - The results in a printable format ready to be saved to a text file.

        Notes:
            This gets the error list from "sidecar_issues" and "event_issues".

        """
        specifics = result.get("Specifics", {})
        sum_list = [f"{name}: [{len(specifics['sidecar_files'])} sidecar files, "
                    f"{len(specifics['event_files'])} event files]"]
        if specifics.get('is_merged'):
            sum_list = sum_list + self.get_error_list(specifics['sidecar_issues'], count_only=True, indent=indent)
            sum_list = sum_list + self.get_error_list(specifics['event_issues'], count_only=True, indent=indent)
        else:
            sum_list = sum_list + self.get_error_list(specifics['sidecar_issues'], indent=indent*2)
            if specifics['sidecar_had_issues']:
                sum_list = sum_list + self.get_error_list(specifics['sidecar_issues'], count_only=False, indent=indent*2)
            else:
                sum_list = sum_list + self.get_error_list(specifics['event_issues'], count_only=False, indent=indent*2)
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
        results = self._get_sidecar_results(sidecar, new_info, self.check_for_warnings)
        if not results['sidecar_had_issues']:
            input_data = TabularInput(new_info['df'], sidecar=sidecar)
            issues = input_data.validate(new_info['schema'])
            if not self.check_for_warnings:
                issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
            issues = [get_printable_issue_string([issue], skip_filename=True) for issue in issues]
            results['event_issues'][new_info["name"]] = issues
            results['total_event_issues'] = len(issues)
        self.summary_dict[new_info["name"]] = results

    def get_details_dict(self, summary_info):
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

    def merge_all_info(self):
        """ Create a dictionary containing all the errors in the dataset.

        Returns:
            dict - dictionary of issues organized into sidecar_issues and event_issues.

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
        results["total_event_issues"] += ind_results["total_event_issues"]
        for ikey, errors in ind_results["event_issues"].items():
            if ind_results["sidecar_had_issues"]:
                results["event_issues"][ikey] = \
                    f"Validation incomplete due to {ind_results['total_sidecar_issues']} sidecar issues"
            else:
                results["event_issues"][ikey] = f"{len(errors)}"

    @staticmethod
    def _update_sidecar_results(results, ind_results):
        results["total_sidecar_issues"] += ind_results["total_sidecar_issues"]
        results["sidecar_files"] = results["sidecar_files"] + ind_results["sidecar_files"]
        for ikey, errors in ind_results["sidecar_issues"].items():
            results["sidecar_issues"][ikey] = errors

    @staticmethod
    def get_empty_results():
        return {"event_files": [], "total_event_issues": 0, "event_issues": {}, "is_merged": False,
                "sidecar_files": [], "total_sidecar_issues": 0, "sidecar_issues": {},
                "sidecar_had_issues": False}

    @staticmethod
    def get_error_list(error_dict, count_only=False, indent=BaseSummary.DISPLAY_INDENT):
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
                #HedValidationSummary._format_errors(error_list, key, item, indent)
        return error_list

    @staticmethod
    def _format_errors(error_list, name, errors, indent):
        error_list.append(f"{indent}{name} issues:")
        for this_item in errors:
            error_list.append(f"{indent * 2}{HedValidationSummary._format_error(this_item)}")

    @staticmethod
    def _format_error(error):
        error_str = error['code']
        error_locations = []
        HedValidationSummary.update_error_location(error_locations, "row", "ec_row", error)
        HedValidationSummary.update_error_location(error_locations, "column", "ec_column", error)
        HedValidationSummary.update_error_location(error_locations, "sidecar column",
                                                   "ec_sidecarColumnName", error)
        HedValidationSummary.update_error_location(error_locations, "sidecar key", "ec_sidecarKeyName", error)
        location_str = ",".join(error_locations)
        if location_str:
            error_str = error_str + f"[{location_str}]"
        error_str = error_str + f": {error['message']}"
        return error_str

    @staticmethod
    def update_error_location(error_locations, location_name, location_key, error):
        if location_key in error:
            error_locations.append(f"{location_name}={error[location_key][0]}")

    @staticmethod
    def _get_sidecar_results(sidecar, new_info, check_for_warnings):
        results = HedValidationSummary.get_empty_results()
        results["event_files"].append(new_info["name"])
        results["event_issues"][new_info["name"]] = []
        if sidecar:
            results["sidecar_files"].append(sidecar.name)
            results["sidecar_issues"][sidecar.name] = []
            sidecar_issues = sidecar.validate(new_info['schema'])
            filtered_issues = ErrorHandler.filter_issues_by_severity(sidecar_issues, ErrorSeverity.ERROR)
            if filtered_issues:
                results["sidecar_had_issues"] = True
            if not check_for_warnings:
                sidecar_issues = filtered_issues
            str_issues = [get_printable_issue_string([issue], skip_filename=True) for issue in sidecar_issues]
            results['sidecar_issues'][sidecar.name] = str_issues
            results['total_sidecar_issues'] = len(sidecar_issues)
        return results
