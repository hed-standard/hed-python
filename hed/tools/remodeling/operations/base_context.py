import os
from abc import ABC, abstractmethod
from datetime import datetime
import json
from werkzeug.utils import secure_filename


DISPLAY_INDENT = "   "


class BaseContext(ABC):
    """ Abstract base class for summary contexts. Should not be instantiated.

    Parameters:
        context_type (str)  Type of summary.
        context_name (str)  Printable name -- should be unique.
        context_filename (str)  Base filename for saving the context.

    """

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

    # def get_summary(self, include_individual=True):
    #     ret_sum = {'context_name': self.context_name, 'context_type': self.context_type,
    #                'context_filename': self.context_filename,
    #                'summary': self.get_summary_details(include_individual=include_individual)}
    #     if as_json:
    #         return json.dumps(ret_sum, indent=4)
    #     else:
    #         return ret_sum

    def get_summary(self, as_json=True, include_individual=True, separate_files=True):
        summary_details = self.get_summary_details(include_individual=include_individual)
        summary = {"Dataset": {"Context name": self.context_name, "Context type": self.context_type,
                   "Context filename": self.context_filename, "Overall summary": summary_details['Dataset']}}

        if separate_files:
            summary["Individual files"] = {}
            for name, name_summary in summary_details["Individual files"].items():
                summary["Individual files"][name] = {"Context name": self.context_name,
                                                      "Context type": self.context_type,
                                                      "Context filename": self.context_filename,
                                                      "Summary": summary_details['Individual files'][name]}
                if as_json:
                    summary["Individual files"][name] = \
                        json.dumps(summary_details["Individual files"][name], indent=4)
            if as_json:
                summary["Dataset"] = json.dumps(summary["Dataset"], indent=4)
            return summary
        if summary_details["Individual files"]:
            summary["Dataset"]["Individual files"] = summary_details["Individual files"]
        if as_json:
            summary["Dataset"] = json.dumps(summary["Dataset"], indent=4)
        return summary

    def get_text_summary_details(self, include_individual=True):
        result = self.get_summary_details(include_individual=include_individual)
        summary_details = {"Dataset": self._get_result_string("Dataset", result.get("Dataset", "")),
                           "Individual files": {}}
        if include_individual:
            for name, individual_result in result.get("Individual files",{}).items():
                summary_details["Individual files"][name] = self._get_result_string(name, individual_result)
        return summary_details

    def get_text_summary(self, include_individual=True, separate_files=True):
        summary_details = self.get_text_summary_details(include_individual=include_individual)
        summary = {"Dataset": f"Context name: {self.context_name}\n" + f"Context type: {self.context_type}\n" + \
                   f"Context filename: {self.context_filename}\n\n" + f"Overall summary:\n{summary_details['Dataset']}"}
        if separate_files and include_individual:
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

    def save(self, save_dir, file_formats=['.txt'], include_individual=True, separate_files=True):
        now = datetime.now()
        time_stamp = '_' + now.strftime('%Y_%m_%d_T_%H_%M_%S_%f')

        for file_format in file_formats:
            if file_format == '.txt':
                summary = self.get_text_summary(include_individual=include_individual, separate_files=separate_files)
            elif file_format == '.json':
                summary = self.get_summary(as_json=True, include_individual=include_individual,
                                           separate_files=separate_files)
            else:
                continue
            self._save_separate(save_dir, file_format, time_stamp, summary)

    def _save_separate(self, save_dir, file_format, time_stamp, summary):
        this_save = os.path.join(save_dir, self.context_name + '/')
        os.makedirs(os.path.realpath(this_save), exist_ok=True)
        file_name = os.path.realpath(os.path.join(this_save, secure_filename(self.context_filename) + "_overall" +
                                                  time_stamp + file_format))

        with open(file_name, 'w') as text_file:
            text_file.write(summary["Dataset"])
        individual= summary.get("Individual files", {})

        if not individual:
            return

        individual_dir = os.path.join(this_save, self.INDIVIDUAL_SUMMARIES_PATH + '/')
        os.makedirs(os.path.realpath(individual_dir), exist_ok=True)
        for name, sum_str in individual.items():
            file_name = os.path.realpath(os.path.join(individual_dir,
                                                      self.context_filename + "_" + name + time_stamp + file_format))
            with open(file_name, 'w') as text_file:
                text_file.write(sum_str)

    def _get_result_string(self, name, result):
        return f"\n{name}\n{DISPLAY_INDENT}{str(result)}"

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
