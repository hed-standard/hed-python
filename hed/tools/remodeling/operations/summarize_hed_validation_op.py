""" Validate the HED tags in a dataset and report errors. """

import os
from hed.errors import ErrorSeverity, ErrorHandler
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext
from hed.validator import HedValidator


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
            "summary_filename": str,
            "check_for_warnings": bool
        },
        "optional_parameters": {
        }
    }

    SUMMARY_TYPE = 'hed_validation'

    def __init__(self, parameters):
        """ Constructor for the summarize hed validation operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        Raises:  
            KeyError   
                - If a required parameter is missing.   
                - If an unexpected parameter is provided.   

            TypeError   
                - If a parameter has the wrong type.   
 
        """
        super().__init__(self.PARAMS, parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.check_for_warnings = parameters['check_for_warnings']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Validate the dataframe with the accompanying sidecar, if any.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be validated.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Usually needed unless only HED tags in HED column of event file.

        Returns:
            DataFrame: Input DataFrame, unchanged.

        Side-effect:
            Updates the context.

        """
        summary = dispatcher.context_dict.get(self.summary_name, None)
        if not summary:
            summary = HedValidationSummaryContext(self)
            dispatcher.context_dict[self.summary_name] = summary
        summary.update_context({'df': dispatcher.post_proc_data(df), 'name': name,
                                'schema': dispatcher.hed_schema, 'sidecar': sidecar})
        return df


class HedValidationSummaryContext(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.SUMMARY_TYPE, sum_op.summary_name, sum_op.summary_filename)
        self.check_for_warnings = sum_op.check_for_warnings

    def _get_result_string(self, name, result, indent=BaseContext.DISPLAY_INDENT):

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

    def update_context(self, new_context):
        validator = HedValidator(hed_schema=new_context['schema'])
        results = self.get_empty_results()
        results["total_event_files"] = 1
        results["event_issues"][new_context["name"]] = []
        self.summary_dict[new_context["name"]] = results
        sidecar = new_context.get('sidecar', None)
        filtered_issues = []
        if sidecar:
            if not isinstance(sidecar, Sidecar):
                sidecar = Sidecar(files=new_context['sidecar'], name=os.path.basename(sidecar))
            results["sidecar_issues"][sidecar.name] = []
            sidecar_issues = sidecar.validate_entries(validator, check_for_warnings=self.check_for_warnings)
            filtered_issues = ErrorHandler.filter_issues_by_severity(sidecar_issues, ErrorSeverity.ERROR)
            if not self.check_for_warnings:
                sidecar_issues = filtered_issues
            results['sidecar_issues'][sidecar.name] = sidecar_issues
            results['total_sidecar_issues'] = len(sidecar_issues)
            results['total_sidecar_files'] = 1
        if not filtered_issues:
            results['validation_completed'] = True
            input_data = TabularInput(new_context['df'], hed_schema=new_context['schema'],  sidecar=sidecar)
            issues = input_data.validate_file(validator, check_for_warnings=self.check_for_warnings)
            if not self.check_for_warnings:
                issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
            results['event_issues'][new_context["name"]] = issues
            results['total_event_issues'] = len(issues)

    def _get_summary_details(self, summary_info):
        return summary_info

    def _merge_all(self):
        """ Return merged information.

        Returns:
           object:  Consolidated summary of information.

        Notes:
            Abstract method be implemented by each individual context summary.

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
    def get_error_list(error_dict, count_only=False, indent=BaseContext.DISPLAY_INDENT):
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
                    error_list.append(f"{indent*2}{HedValidationSummaryContext.format_error(this_item)}")
        return error_list

    @staticmethod
    def format_errors(error_list):
        pass

    @staticmethod
    def format_error(error):
        error_str = error['code']
        error_locations = []
        HedValidationSummaryContext.update_error_location(error_locations, "row", "ec_row", error)
        HedValidationSummaryContext.update_error_location(error_locations, "column", "ec_column", error)
        HedValidationSummaryContext.update_error_location(error_locations, "sidecar column",
                                                          "ec_sidecarColumnName", error)
        HedValidationSummaryContext.update_error_location(error_locations, "sidecar key", "ec_sidecarKeyName", error)
        location_str = ",".join(error_locations)
        if location_str:
            error_str = error_str + f"[{location_str}]"
        error_str = error_str + f": {error['message']}"
        return error_str

    @staticmethod
    def update_error_location(error_locations, location_name, location_key, error):
        if location_key in error:
            error_locations.append(f"{location_name}={error[location_key][0]}")
