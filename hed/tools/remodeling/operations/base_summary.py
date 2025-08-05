""" Abstract base class for the contents of summary operations. """

import os
from abc import ABC, abstractmethod
import json
from hed.tools.util import io_util


class BaseSummary(ABC):
    """ Abstract base class for summary contents. Should not be instantiated.

    Parameters:
        sum_op (BaseOp):  Operation corresponding to this summary.

    """

    DISPLAY_INDENT = "   "
    INDIVIDUAL_SUMMARIES_PATH = 'individual_summaries'

    def __init__(self, sum_op):
        self.op = sum_op
        self.summary_dict = {}

    def get_summary_details(self, include_individual=True) -> dict:
        """ Return a dictionary with the details for individual files and the overall dataset.

        Parameters:
            include_individual (bool):  If True, summaries for individual files are included.

        Returns:
            dict: A dictionary with 'Dataset' and 'Individual files' keys.

        Notes:
            - The 'Dataset' value is either a string or a dictionary with the overall summary.
            - The 'Individual files' value is dictionary whose keys are file names and values are
                   their corresponding summaries.

        Users are expected to provide merge_all_info and get_details_dict functions to support this.

        """
        merged_counts = self.merge_all_info()
        if merged_counts:
            details = self.get_details_dict(merged_counts)
        else:
            details = "Overall summary unavailable"

        summary_details = {"Dataset": details, "Individual files": {}}
        if include_individual:
            for name, count in self.summary_dict.items():
                summary_details["Individual files"][name] = self.get_details_dict(count)
        return summary_details

    def get_summary(self, individual_summaries="separate"):
        """ Return a summary dictionary with the information.

        Parameters:
            individual_summaries (str): "separate", "consolidated", or "none"

        Returns:
            dict: Dictionary with "Dataset" and "Individual files" keys.

        Notes: The individual_summaries value is processed as follows:
           -  "separate" individual summaries are to be in separate files.
           -  "consolidated" means that the individual summaries are in same file as overall summary.
           -  "none" means that only the overall summary is produced.

        """
        include_individual = individual_summaries == "separate" or individual_summaries == "consolidated"
        summary_details = self.get_summary_details(include_individual=include_individual)
        dataset_summary = {"Summary name": self.op.summary_name, "Summary type": self.op.SUMMARY_TYPE,
                           "Summary filename": self.op.summary_filename, "Overall summary": summary_details['Dataset']}
        summary = {"Dataset": dataset_summary, "Individual files": {}}
        if summary_details["Individual files"]:
            summary["Individual files"] = self.get_individual(summary_details["Individual files"],
                                                              separately=individual_summaries == "separate")
        return summary

    def get_individual(self, summary_details, separately=True):
        """ Return a dictionary of the individual file summaries.

        Parameters:
            summary_details (dict): Dictionary of the individual file summaries.
            separately (bool): If True (the default), each individual summary has a header for separate output.
        """
        individual_dict = {}
        for name, name_summary in summary_details.items():
            if separately:
                individual_dict[name] = {"Summary name": self.op.summary_name, "summary type": self.op.SUMMARY_TYPE,
                                         "Summary filename": self.op.summary_filename, "File summary": name_summary}
            else:
                individual_dict[name] = name_summary
        return individual_dict

    def get_text_summary_details(self, include_individual=True) -> dict:
        """ Return a text summary of the information represented by this summary.

        Parameters:
            include_individual (bool): If True (the default), individual summaries are in "Individual files".

        Returns:
            dict: Dictionary with "Dataset" and "Individual files" keys.

        """
        result = self.get_summary_details(include_individual=include_individual)
        summary_details = {"Dataset": self._get_result_string("Dataset", result.get("Dataset", "")),
                           "Individual files": {}}
        if include_individual:
            for name, individual_result in result.get("Individual files", {}).items():
                summary_details["Individual files"][name] = self._get_result_string(name, individual_result)
        return summary_details

    def get_text_summary(self, individual_summaries="separate") -> dict:
        """ Return a complete text summary by assembling the individual pieces.

        Parameters:
            individual_summaries(str):  One of the values "separate", "consolidated", or "none".

        Returns:
            dict: Complete text summary.

        Notes: The options are:
            - "none":  Just has "Dataset" key.
            - "consolidated"  Has "Dataset" and "Individual files" keys with the values of each is a string.
            - "separate" Has "Dataset" and "Individual files" keys. The values of "Individual files" is a dict.

        """
        include_individual = individual_summaries == "separate" or individual_summaries == "consolidated"
        summary_details = self.get_text_summary_details(include_individual=include_individual)
        summary = {"Dataset": f"Summary name: {self.op.summary_name}\n" +
                   f"Summary type: {self.op.SUMMARY_TYPE}\n" +
                   f"Summary filename: {self.op.summary_filename}\n\n" +
                   f"Overall summary:\n{summary_details['Dataset']}"}
        if individual_summaries == "separate":
            summary["Individual files"] = {}
            for name, name_summary in summary_details["Individual files"].items():
                summary["Individual files"][name] = f"Summary name: {self.op.summary_name}\n" + \
                                                    f"Summary type: {self.op.SUMMARY_TYPE}\n" + \
                                                    f"Summary filename: {self.op.summary_filename}\n\n" + \
                                                    f"Summary for {name}:\n{name_summary}"
        elif include_individual:
            ind_list = []
            for name, name_summary in summary_details["Individual files"].items():
                ind_list.append(f"{name}:\n{name_summary}\n")
            ind_str = "\n\n".join(ind_list)
            summary['Dataset'] = summary["Dataset"] + f"\n\nIndividual files:\n\n{ind_str}"

        return summary

    def save(self, save_dir, file_formats=['.txt'], individual_summaries="separate", task_name=""):
        """ Save the summaries using the format indicated.

        Parameters:
            save_dir (str):  Name of the directory to save the summaries in.
            file_formats (list):  List of file formats to use for saving.
            individual_summaries (str):  Save one file or multiple files based on setting.
            task_name (str): If this summary corresponds to files from a task, the task_name is used in filename.

        """
        for file_format in file_formats:
            if file_format == '.txt':
                summary = self.get_text_summary(individual_summaries=individual_summaries)
            elif file_format == '.json':
                summary = self.get_summary(individual_summaries=individual_summaries)
            else:
                continue
            self._save_summary_files(save_dir, file_format, summary, individual_summaries, task_name=task_name)

            self.save_visualizations(save_dir, file_formats=file_formats, individual_summaries=individual_summaries,
                                     task_name=task_name)

    def save_visualizations(self, save_dir, file_formats=['.svg'], individual_summaries="separate", task_name=""):
        """ Save summary visualizations, if any, using the format indicated.

        Parameters:
            save_dir (str):  Name of the directory to save the summaries in.
            file_formats (list):  List of file formats to use for saving.
            individual_summaries (str):  Save one file or multiple files based on setting.
            task_name (str): If this summary corresponds to files from a task, the task_name is used in filename.

        """
        pass

    def _save_summary_files(self, save_dir, file_format, summary, individual_summaries, task_name=''):
        """ Save the files in the appropriate format.

        Parameters:
            save_dir (str): Path to the directory in which the summaries will be saved.
            file_format (str): string representing the extension (including .), '.txt' or '.json'.
            summary (dictionary): Dictionary of summaries (has "Dataset" and "Individual files" keys).
            individual_summaries (str): "consolidated", "individual", or "none".
            task_name (str): Name of task to be included in file name if multiple tasks.

        """
        if self.op.append_timecode:
            time_stamp = '_' + io_util.get_timestamp()
        else:
            time_stamp = ''
        if task_name:
            task_name = "_" + task_name
        this_save = os.path.join(save_dir, self.op.summary_name + '/')
        os.makedirs(os.path.realpath(this_save), exist_ok=True)
        filename = os.path.realpath(os.path.join(this_save,
                                                 self.op.summary_filename + task_name + time_stamp + file_format))
        individual = summary.get("Individual files", {})
        if individual_summaries == "none" or not individual:
            self.dump_summary(filename, summary["Dataset"])
            return
        if individual_summaries == "consolidated":
            self.dump_summary(filename, summary)
            return
        self.dump_summary(filename, summary["Dataset"])
        individual_dir = os.path.join(this_save, self.INDIVIDUAL_SUMMARIES_PATH + '/')
        os.makedirs(os.path.realpath(individual_dir), exist_ok=True)
        for name, sum_str in individual.items():
            filename = self._get_summary_filepath(individual_dir, name, task_name, time_stamp, file_format)
            self.dump_summary(filename, sum_str)

    def _get_summary_filepath(self, individual_dir, name, task_name, time_stamp, file_format):
        """ Return the filepath for the summary including the timestamp

        Parameters:
            individual_dir (str):  path of the directory in which the summary should be stored.
            name (str): Path of the original file from which the summary was extracted.
            task_name (str): Task name if separate summaries for different tasks or the empty string if not separated.
            time_stamp (str):  Formatted date-time string to be included in the filename of the summary.

        Returns:
            str: Full path name of the summary.

        """
        this_name = os.path.basename(name)
        this_name = os.path.splitext(this_name)[0]
        count = 1
        match = True
        filename = None
        while match:
            filename = f"{self.op.summary_filename}_{this_name}{task_name}_{count}{time_stamp}{file_format}"
            filename = os.path.realpath(os.path.join(individual_dir, filename))
            if not os.path.isfile(filename):
                break
            count = count + 1
        return filename

    def _get_result_string(self, name, result, indent=DISPLAY_INDENT):
        """ Return a formatted string with the summary for the indicated name.

        Parameters:
            name (str):  Identifier (usually the filename) of the individual file.
            result (dict): The dictionary of the summary results indexed by name.
            indent (str): A string containing spaces used for indentation (usually 3 spaces).

        Returns:
            str: The results in a printable format ready to be saved to a text file.

        Notes:
            This file should be overridden by each summary.

        """
        return f"\n{name}\n{indent}{str(result)}"

    @staticmethod
    def dump_summary(filename, summary):
        with open(filename, 'w') as text_file:
            if not isinstance(summary, str):
                summary = json.dumps(summary, indent=4)
            text_file.write(summary)

    @abstractmethod
    def get_details_dict(self, summary_info):
        """ Return the summary-specific information.

        Parameters:
            summary_info (object):  Summary to return info from.

        Returns:
            dict: dictionary with the results.

        Notes:
            Abstract method be implemented by each individual summary.

        Notes:
            The expected return value is a dictionary of the form:

               {"Name": "", "Total events": 0, "Total files": 0, "Files": [], "Specifics": {}}"

        """
        raise NotImplementedError

    @abstractmethod
    def merge_all_info(self):
        """ Return merged information.

        Returns:
           object:  Consolidated summary of information.

        Notes:
            Abstract method be implemented by each individual summary.

        """
        raise NotImplementedError

    @abstractmethod
    def update_summary(self, summary_dict):
        """ Method to update summary for a given tabular input.

        Parameters:
            summary_dict (dict)  A summary specific dictionary with the update information.

        """
        raise NotImplementedError
