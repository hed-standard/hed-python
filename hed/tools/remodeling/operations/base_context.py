""" Abstract base class for the context of summary operations. """

import os
from abc import ABC, abstractmethod
import json
from hed.tools.util.io_util import get_timestamp


class BaseContext(ABC):
    """ Abstract base class for summary contexts. Should not be instantiated.

    Parameters:
        context_type (str)  Type of summary.
        context_name (str)  Printable name -- should be unique.
        context_filename (str)  Base filename for saving the context.

    """

    DISPLAY_INDENT = "   "
    INDIVIDUAL_SUMMARIES_PATH = 'individual_summaries'

    def __init__(self, context_type, context_name, context_filename):
        self.context_type = context_type
        self.context_name = context_name
        self.context_filename = context_filename
        self.summary_dict = {}

    def get_summary_details(self, include_individual=True):
        merged_summary = self._merge_all()
        if merged_summary:
            details = self._get_summary_details(merged_summary)
        else:
            details = "Overall summary unavailable"

        summary_details = {"Dataset": details, "Individual files": {}}
        if include_individual:
            for name, count in self.summary_dict.items():
                summary_details["Individual files"][name] = self._get_summary_details(count)
        return summary_details

    def get_summary(self, individual_summaries="separate"):

        include_individual = individual_summaries == "separate" or individual_summaries == "consolidated"
        summary_details = self.get_summary_details(include_individual=include_individual)
        dataset_summary = {"Context name": self.context_name, "Context type": self.context_type,
                           "Context filename": self.context_filename, "Overall summary": summary_details['Dataset']}
        summary = {"Dataset": dataset_summary, "Individual files": {}}
        if summary_details["Individual files"]:
            summary["Individual files"] = self.get_individual(summary_details["Individual files"],
                                                              separately=individual_summaries == "separate")
        return summary

    def get_individual(self, summary_details, separately=True):
        individual_dict = {}
        for name, name_summary in summary_details.items():
            if separately:
                individual_dict[name] = {"Context name": self.context_name, "Context type": self.context_type,
                                         "Context filename": self.context_filename, "File summary": name_summary}
            else:
                individual_dict[name] = name_summary
        return individual_dict

    def get_text_summary_details(self, include_individual=True):
        result = self.get_summary_details(include_individual=include_individual)
        summary_details = {"Dataset": self._get_result_string("Dataset", result.get("Dataset", "")),
                           "Individual files": {}}
        if include_individual:
            for name, individual_result in result.get("Individual files", {}).items():
                summary_details["Individual files"][name] = self._get_result_string(name, individual_result)
        return summary_details

    def get_text_summary(self, individual_summaries="separate"):
        include_individual = individual_summaries == "separate" or individual_summaries == "consolidated"
        summary_details = self.get_text_summary_details(include_individual=include_individual)
        summary = {"Dataset": f"Context name: {self.context_name}\n" + f"Context type: {self.context_type}\n" +
                   f"Context filename: {self.context_filename}\n\n" + f"Overall summary:\n{summary_details['Dataset']}"}
        if individual_summaries == "separate":
            summary["Individual files"] = {}
            for name, name_summary in summary_details["Individual files"].items():
                summary["Individual files"][name] = f"Context name: {self.context_name}\n" + \
                                                    f"Context type: {self.context_type}\n" + \
                                                    f"Context filename: {self.context_filename}\n\n" + \
                                                    f"Summary for {name}:\n{name_summary}"
        elif include_individual:
            ind_list = []
            for name, name_summary in summary_details["Individual files"].items():
                ind_list.append(f"{name}:\n{name_summary}\n")
            ind_str = "\n\n".join(ind_list)
            summary['Dataset'] = summary["Dataset"] + f"\n\nIndividual files:\n\n{ind_str}"

        return summary

    def save(self, save_dir, file_formats=['.txt'], individual_summaries="separate"):

        for file_format in file_formats:
            if file_format == '.txt':
                summary = self.get_text_summary(individual_summaries=individual_summaries)
            elif file_format == '.json':
                summary = self.get_summary(individual_summaries=individual_summaries)
            else:
                continue
            self._save_separate(save_dir, file_format, summary, individual_summaries)

    def _save_separate(self, save_dir, file_format, summary, individual_summaries):
        time_stamp = '_' + get_timestamp()
        this_save = os.path.join(save_dir, self.context_name + '/')
        os.makedirs(os.path.realpath(this_save), exist_ok=True)
        filename = os.path.realpath(os.path.join(this_save, self.context_filename + time_stamp + file_format))
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
            filename = self._get_individual_filename(individual_dir, name, time_stamp, file_format)
            self.dump_summary(filename, sum_str)

    def _get_individual_filename(self, individual_dir, name, time_stamp, file_format):
        this_name = os.path.basename(name)
        this_name = os.path.splitext(this_name)[0]
        count = 1
        match = True
        filename = None
        while match:
            filename = f"{self.context_filename}_{this_name}_{count}{time_stamp}{file_format}"
            filename = os.path.realpath(os.path.join(individual_dir, filename))
            if not os.path.isfile(filename):
                break
            count = count + 1
        return filename

    def _get_result_string(self, name, result, indent=DISPLAY_INDENT):
        return f"\n{name}\n{indent}{str(result)}"

    @staticmethod
    def dump_summary(filename, summary):
        with open(filename, 'w') as text_file:
            if not isinstance(summary, str):
                summary = json.dumps(summary, indent=4)
            text_file.write(summary)

    @abstractmethod
    def _get_summary_details(self, summary_info):
        """ Return the summary-specific information.

        Parameters:
            summary_info (object):  Summary to return info from

        Notes:
            Abstract method be implemented by each individual context summary.

        """
        raise NotImplementedError

    @abstractmethod
    def _merge_all(self):
        """ Return merged information.

        Returns:
           object:  Consolidated summary of information.

        Notes:
            Abstract method be implemented by each individual context summary.

        """
        raise NotImplementedError

    @abstractmethod
    def update_context(self, context_dict):
        """ Method to update summary for a given tabular input.

        Parameters:
            context_dict (dict)  A context specific dictionary with the update information.

        """
        raise NotImplementedError
