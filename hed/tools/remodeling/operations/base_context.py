import os
from abc import ABC, abstractmethod
import json
from hed.tools.util.io_util import generate_filename

DISPLAY_INDENT = "   "


class BaseContext(ABC):
    """ Abstract base class for summary contexts. Should not be instantiated.

    Parameters:
        context_type (str)  Type of summary.
        context_name (str)  Printable name -- should be unique.
        context_filename (str)  Base filename for saving the context.

    """
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
        summary_details = {"Dataset": details}
        if include_individual:
            individual = {}
            for name, count in self.summary_dict.items():
                individual[name] = self._get_summary_details(count)
            summary_details["Individual files"] = individual
        return summary_details

    def get_summary(self, as_json=False, include_individual=True):
        ret_sum = {'context_name': self.context_name, 'context_type': self.context_type,
                   'context_filename': self.context_filename,
                   'summary': self.get_summary_details(include_individual=include_individual)}
        if as_json:
            return json.dumps(ret_sum, indent=4)
        else:
            return ret_sum

    # def get_summary_details(self, include_individual=True):
    #     merged_summary = self._merge_all()
    #     summary_details = {"Dataset": self._get_summary_details(merged_summary)}
    #     if include_individual:
    #         individual = {}
    #         for name, count in self.summary_dict.items():
    #             individual[name] = self._get_summary_details(count)
    #         summary_details["Individual files"] = individual
    #     return summary_details

    # def get_text_summary(self, title='', include_individual=True):
    #     summary_details = json.dumps(self.get_summary_details(include_individual=include_individual), indent=4)
    #     summary_details = summary_details.replace('"', '').replace('{', '').replace('}', '').replace(',', '')
    #
    #     sum_str = ""
    #     if title:
    #         sum_str = title + "\n"
    #     sum_str = sum_str + f"Context name: {self.context_name}\n" + f"Context type: {self.context_type}\n" + \
    #         f"Context filename: {self.context_filename}\n" + f"Summary:\n{summary_details}"
    #
    #     return sum_str

    def get_text_summary(self, title='', include_individual=True):
        result = self.get_summary_details(include_individual=include_individual)
        summary_details = self._get_result_string("Dataset", result.get("Dataset", ""))
        if include_individual and "Individual files" in result:
            sum_list = []
            for name, individual_result in result["Individual files"].items():
                sum_list.append(self._get_result_string(name, individual_result))
            summary_details = summary_details + "\n\nIndividual files:\n" + "\n".join(sum_list)
        if title:
            title_str = title + "\n"
        else:
            title_str = ''
        sum_str = f"{title_str}Context name: {self.context_name}\n" + f"Context type: {self.context_type}\n" + \
                  f"Context filename: {self.context_filename}\n" + f"\nSummary details:\n{summary_details}"
        return sum_str

    def save(self, save_dir, file_formats=['.txt'], include_individual=True):
        file_base = os.path.join(save_dir, generate_filename(self.context_filename, append_datetime=True))
        for file_format in file_formats:
            if file_format == '.txt':
                summary = self.get_text_summary(include_individual=include_individual)
            elif file_format == '.json':
                summary = self.get_summary(as_json=True, include_individual=include_individual)
            else:
                continue

            with open(os.path.realpath(file_base + file_format), 'w') as text_file:
                text_file.write(summary)

    def _get_result_string(self, name, result):
        return f"\n{name}\n\t{str(result)}"

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
