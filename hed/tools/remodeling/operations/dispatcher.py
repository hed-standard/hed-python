import os
import numpy as np
import pandas as pd
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.remodeling.operations.number_rows_op import NumberRowsOp
from hed.tools.remodeling.operations.number_groups_op import NumberGroupsOp
from hed.tools.remodeling.operations.remap_columns_op import RemapColumnsOp
from hed.tools.remodeling.operations.factor_column_op import FactorColumnOp
from hed.tools.remodeling.operations.factor_hed_tags_op import FactorHedTagsOp
from hed.tools.remodeling.operations.factor_hed_type_op import FactorHedTypeOp
from hed.tools.remodeling.operations.merge_consecutive_op import MergeConsecutiveOp
from hed.tools.remodeling.operations.remove_columns_op import RemoveColumnsOp
from hed.tools.remodeling.operations.reorder_columns_op import ReorderColumnsOp
from hed.tools.remodeling.operations.remove_rows_op import RemoveRowsOp
from hed.tools.remodeling.operations.rename_columns_op import RenameColumnsOp
from hed.tools.remodeling.operations.split_event_op import SplitEventOp
from hed.tools.remodeling.operations.summarize_column_names_op import SummarizeColumnNamesOp
from hed.tools.remodeling.operations.summarize_column_values_op import SummarizeColumnValuesOp
from hed.tools.remodeling.operations.summarize_hed_type_op import SummarizeHedTypeOp
from hed.errors.exceptions import HedFileError

dispatch = {
    'number_rows': NumberRowsOp,
    'number_groups': NumberGroupsOp,
    'factor_column': FactorColumnOp,
    'factor_hed_tags': FactorHedTagsOp,
    'factor_hed_type': FactorHedTypeOp,
    'merge_consecutive': MergeConsecutiveOp,
    'number_groups_op': NumberGroupsOp,
    'number_rows_op': NumberRowsOp,
    'remap_columns': RemapColumnsOp,
    'remove_columns': RemoveColumnsOp,
    'remove_rows': RemoveRowsOp,
    'rename_columns': RenameColumnsOp,
    'reorder_columns': ReorderColumnsOp,
    'split_event': SplitEventOp,
    'summarize_column_names': SummarizeColumnNamesOp,
    'summarize_column_values': SummarizeColumnValuesOp,
    'summarize_hed_type': SummarizeHedTypeOp
}


class Dispatcher:
    REMODELING_SUMMARY_PATH = 'derivatives/remodel/summaries'

    def __init__(self, command_list, data_root=None, hed_versions=None):
        self.data_root = data_root
        op_list, errors = self.parse_commands(command_list)
        if errors:
            these_errors = self.errors_to_str(errors, 'Dispatcher failed due to invalid commands')
            raise ValueError("InvalidCommandList", f"{these_errors}")
        self.parsed_ops = op_list
        if hed_versions:
            self.hed_schema = load_schema_version(hed_versions)
        else:
            self.hed_schema = None
        self.context_dict = {}

    def get_remodel_save_dir(self):
        return os.path.realpath(os.path.join(self.data_root, Dispatcher.REMODELING_SUMMARY_PATH))

    def run_operations(self, filename, sidecar=None, verbose=False):
        """ Run the dispatcher commands on a file.

        Args:
            filename (str)      Full path of the file to be remodeled.
            sidecar (Sidecar or file-like)   Only needed for HED operations.
            verbose (bool):  If true, print out progress reports

        """

        # string to functions
        if verbose:
            print(f"Reading {filename}...")
        try:
            df = pd.read_csv(filename, sep='\t')
        except Exception:
            raise HedFileError("BadDataFrameFile",
                               f"{str(filename)} does not correspond to a valid tab-separated value file", "")
        df = self.prep_events(df)
        for operation in self.parsed_ops:
            df = operation.do_op(self, df, filename, sidecar=sidecar)
        df = df.fillna('n/a')
        return df

    def save_context(self, save_formats, verbose=True):
        """ Save the summary files in the specified formats.

        Args:
            save_formats (list) list of formats [".txt", ."json"]
            verbose (bool) If include additional details

        The summaries are saved in the dataset derivatives/remodeling folder.

        """
        if not save_formats:
            return
        summary_path = self.get_remodel_save_dir()
        os.makedirs(summary_path, exist_ok=True)
        for context_name, context_item in self.context_dict.items():
            context_item.save(summary_path, save_formats, verbose=verbose)

    @staticmethod
    def parse_commands(command_list):
        errors = []
        commands = []
        for index, item in enumerate(command_list):
            try:
                if not isinstance(item, dict):
                    raise TypeError("InvalidCommandFormat",
                                    f"Each commands must be a dictionary but command {str(item)} is {type(item)}")
                if "command" not in item:
                    raise KeyError("MissingCommand",
                                   f"Command {str(item)} does not have a command key")
                if "parameters" not in item:
                    raise KeyError("MissingParameters",
                                   f"Command {str(item)} does not have a parameters key")
                if item["command"] not in dispatch:
                    raise KeyError("CommandCanNotBeDispatched",
                                   f"Command {item['command']} must be added to dispatch before it can be executed.")
                new_command = dispatch[item["command"]](item["parameters"])
                commands.append(new_command)
            except Exception as ex:
                errors.append({"index": index, "item": f"{item}", "error_type": type(ex),
                               "error_code": ex.args[0], "error_msg": ex.args[1]})
        if errors:
            return [], errors
        return commands, []

    @staticmethod
    def prep_events(df):
        """ Replace all n/a entries in the data frame by np.NaN for processing.

        Args:
            df (DataFrame) - The DataFrame to be processed.

        """
        df = df.replace('n/a', np.NaN)
        return df

    @staticmethod
    def errors_to_str(messages, title="", sep='\n'):
        error_list = [0]*len(messages)
        for index, message in enumerate(messages):
            error_list[index] = f"Command[{message.get('index', None)}] " + \
                                f"has error:{message.get('error_type', None)}" + \
                                f" with error code:{message.get('error_code', None)} " + \
                                f"\n\terror msg:{message.get('error_msg', None)}"
        errors = sep.join(error_list)
        if title:
            return title + sep + errors
        return errors
