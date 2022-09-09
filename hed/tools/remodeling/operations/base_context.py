import os
from abc import ABC
from datetime import datetime
import json


class BaseContext(ABC):
    """ Abstract base class for summary contexts. Should not be instantiated.

    Args:
        context_type (str)  Type of summary.
        context_name (str)  Printable name -- should be unique.
        context_filename (str)  Base filename for saving the context.

    """
    def __init__(self, context_type, context_name, context_filename):
        self.context_type = context_type
        self.context_name = context_name
        self.context_filename = context_filename

    def get_summary_details(self, as_json=False, verbose=True):
        """ Return the summary-specific information.

        Args:
            as_json (bool)  If False return a dictionary otherwise return a JSON string.
            verbose (bool)  If True, may provide additional details in the summar.

        Notes:
            Abstract method be implemented by each individual context summary.

        """
        raise NotImplementedError

    def get_summary(self, as_json=False, verbose=True):
        ret_sum = {'context_name': self.context_name, 'context_type': self.context_type,
                   'context_filename': self.context_filename,
                   'summary': self.get_summary_details(verbose=verbose)}
        if as_json:
            return json.dumps(ret_sum, indent=4)
        else:
            return ret_sum

    def get_text_summary(self, title='', verbose=True):
        summary_details = json.dumps(self.get_summary_details(), indent=4)
        summary_details = summary_details.replace('"', '').replace('{', '').replace('}', '').replace(',', '')

        sum_str = ""
        if title:
            sum_str = title + "\n"
        sum_str = sum_str + f"Context name: {self.context_name}\n" + f"Context type: {self.context_type}\n" + \
            f"Context filename: {self.context_filename}\n" + f"Summary:\n{summary_details}"

        return sum_str

    def save(self, save_dir, file_formats, verbose=True):
        if not file_formats:
            return
        now = datetime.now()
        file_base = os.path.join(save_dir, self.context_filename) + '_' + now.strftime('%Y_%m_%d_T_%H_%M_%S_%f')
        for file_format in file_formats:
            if file_format == '.txt':
                summary = self.get_text_summary(verbose=verbose)
            elif file_format == '.json':
                summary = self.get_summary(as_json=True)
            else:
                continue

            with open(os.path.realpath(file_base + file_format), 'w') as text_file:
                text_file.write(summary)

    def update_context(self, context_dict):
        """ Method to update summary for a given tabular input.

        Args:
            context_dict (dict)  A context specific dictionary with the update information.

        """
        raise NotImplementedError
