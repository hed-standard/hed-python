""" Validate the HED tags in a dataset and report errors. """

import os
from hed.errors import ErrorSeverity, ErrorHandler
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

        Side-effect:
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

        if result["is_merged"]:
            sum_list = [f"{name}: [{result['total_sidecar_files']} sidecar files, "
                        f"{result['total_event_files']} event files]"]
            sum_list = sum_list + self.get_error_list(result['sidecar_issues'], count_only=True, indent=indent)
            sum_list = sum_list + self.get_error_list(result['event_issues'], count_only=True, indent=indent)
        else:
            sum_list = [f"{indent}{name}: {result['total_sidecar_files']} sidecar files"]
            sum_list = sum_list + self.get_error_list(result['sidecar_issues'], indent=indent*2)
            if result['validation_completed']:
                sum_list = sum_list + self.get_error_list(result['event_issues'], count_only=False, indent=indent*2)
            else:
                sum_list = sum_list + [f"{indent*2}Event file validation was incomplete because of sidecar errors"]
        return "\n".join(sum_list)

    def update_summary(self, new_info):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_info (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary needs a "name" str, a schema, a "df", and a "Sidecar".
        """

        results = self.get_empty_results()
        results["total_event_files"] = 1
        results["event_issues"][new_info["name"]] = []
        self.summary_dict[new_info["name"]] = results
        sidecar = new_info.get('sidecar', None)
        filtered_issues = []
        if sidecar:
            if not isinstance(sidecar, Sidecar):
                sidecar = Sidecar(files=new_info['sidecar'], name=os.path.basename(sidecar))
            results["sidecar_issues"][sidecar.name] = []
            sidecar_issues = sidecar.validate(new_info['schema'])
            filtered_issues = ErrorHandler.filter_issues_by_severity(sidecar_issues, ErrorSeverity.ERROR)
            if not self.check_for_warnings:
                sidecar_issues = filtered_issues
            results['sidecar_issues'][sidecar.name] = sidecar_issues
            results['total_sidecar_issues'] = len(sidecar_issues)
            results['total_sidecar_files'] = 1
        if not filtered_issues:
            results['validation_completed'] = True
            input_data = TabularInput(new_info['df'], sidecar=sidecar)
            issues = input_data.validate(new_info['schema'])
            if not self.check_for_warnings:
                issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
            results['event_issues'][new_info["name"]] = issues
            results['total_event_issues'] = len(issues)

    def get_details_dict(self, summary_info):
        """Return the summary details from the summary_info.

        Parameters:
            summary_info (dict): Dictionary of issues

        Returns:
            dict:  Same summary_info as was passed in.

        """
        return summary_info

    def merge_all_info(self):
        """ Create a dictionary containing all of the errors in the dataset.

        Returns:
            dict - dictionary of issues organized into sidecar_issues and event_issues.

        """

        results = self.get_empty_results()
        results["is_merged"] = True
        for key, ind_results in self.summary_dict.items():
            results["total_event_files"] += ind_results["total_event_files"]
            results["total_event_issues"] += ind_results["total_event_issues"]

            for ikey, errors in ind_results["sidecar_issues"].items():
                results["sidecar_issues"][ikey] = errors
            for ikey, errors in ind_results["event_issues"].items():
                if not ind_results["validation_completed"]:
                    results["event_issues"][ikey] = \
                       f"Validation incomplete due to {ind_results['total_sidecar_issues']} sidecar issues"
                else:
                    results["event_issues"][ikey] = f"{len(errors)}"
            results["total_sidecar_files"] += ind_results["total_sidecar_files"]
        return results

    @staticmethod
    def get_empty_results():
        return {"total_event_files": 0, "total_event_issues": 0, "event_issues": {}, "is_merged": False,
                "total_sidecar_files": 0, "total_sidecar_issues": 0, "sidecar_issues": {},
                "validation_completed": False}

    @staticmethod
    def get_error_list(error_dict, count_only=False, indent=BaseSummary.DISPLAY_INDENT):
        error_list = []
        for key, item in error_dict.items():
            if count_only and isinstance(item, list):
                error_list.append(f"{indent}{key}: {len(item)} issues")
            elif count_only:
                error_list.append(f"{indent}{key}: {item} issues")
            elif not len(item):
                error_list.append(f"{indent}{key} has no issues")
            else:
                error_list.append(f"{indent}{key} issues:")
                for this_item in item:
                    error_list.append(f"{indent*2}{HedValidationSummary.format_error(this_item)}")
        return error_list

    @staticmethod
    def format_errors(error_list):
        pass

    @staticmethod
    def format_error(error):
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
