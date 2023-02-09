""" Controller for applying operations to tabular files and saving the results. """

import os
import numpy as np
import pandas as pd
import json
from hed.errors.exceptions import HedFileError
from hed.schema.hed_schema_io import get_schema
from hed.tools.remodeling.backup_manager import BackupManager
from hed.tools.remodeling.operations.valid_operations import valid_operations
from hed.tools.util.io_util import generate_filename, extract_suffix_path, get_timestamp


class Dispatcher:
    """ Controller for applying operations to tabular files and saving the results. """

    REMODELING_SUMMARY_PATH = 'derivatives/remodel/summaries'

    def __init__(self, operation_list, data_root=None,
                 backup_name=BackupManager.DEFAULT_BACKUP_NAME, hed_versions=None):
        """ Constructor for the dispatcher.

        Parameters:
            operation_list (list): List of unparsed operations.
            data_root (str or None):  Root directory for the dataset. If none, then backups are not made.
            hed_versions (str, list, HedSchema, or HedSchemaGroup): The HED schema.

        Raises:
            HedFileError
                - If the specified backup does not exist.

            - ValueError:
                - If any of the operations cannot be parsed correctly.
        """
        self.data_root = data_root
        self.backup_name = backup_name
        self.backup_man = None
        if self.data_root and backup_name:
            self.backup_man = BackupManager(data_root)
            if not self.backup_man.get_backup(self.backup_name):
                raise HedFileError("BackupDoesNotExist",
                                   f"Remodeler cannot be run with a dataset without first creating the "
                                   f"{self.backup_name} backup for {self.data_root}", "")
        op_list, errors = self.parse_operations(operation_list)
        if errors:
            these_errors = self.errors_to_str(errors, 'Dispatcher failed due to invalid operations')
            raise ValueError("InvalidOperationList", f"{these_errors}")
        self.parsed_ops = op_list
        self.hed_schema = get_schema(hed_versions)
        self.context_dict = {}

    def get_summaries(self, file_formats=['.txt', '.json']):
        """ Return the summaries in a dictionary of strings suitable for saving or archiving.

        Parameters:
            file_formats (list):  List of formats for the context files ('.json' and '.txt' are allowed).

        Returns:
            list: A list of dictionaries of summaries keyed to filenames.

        """

        summary_list = []
        time_stamp = '_' + get_timestamp()
        for context_name, context_item in self.context_dict.items():
            file_base = context_item.context_filename
            if self.data_root:
                file_base = extract_suffix_path(self.data_root, file_base)
            file_base = generate_filename(file_base)
            for file_format in file_formats:
                if file_format == '.txt':
                    summary = context_item.get_text_summary(individual_summaries="consolidated")
                    summary = summary['Dataset']
                elif file_format == '.json':
                    summary = json.dumps(context_item.get_summary(individual_summaries="consolidated"), indent=4)

                else:
                    continue
                summary_list.append({'file_name': file_base + time_stamp + file_format, 'file_format': file_format,
                                     'file_type': 'summary', 'content': summary})
        return summary_list

    def get_data_file(self, file_designator):
        """ Get the correct data file give the file designator.

        Parameters:
            file_designator (str, DataFrame ): A dataFrame or the full path of the dataframe in the original dataset.

        Returns:
            DataFrame:  DataFrame after reading the path.

        Raises:
            HedFileError:  If a valid file cannot be found.

        Note:
        - If a string is passed and there is a backup manager,
          the string must correspond to the full path of the file in the original dataset.
          In this case, the corresponding backup file is read and returned.
        - If a string is passed and there is no backup manager,
          the data file corresponding to the file_designator is read and returned.
        - If a Pandas DataFrame is passed, a copy is returned.

        """
        if isinstance(file_designator, pd.DataFrame):
            return file_designator.copy()
        if self.backup_man:
            actual_path = self.backup_man.get_backup_path(self.backup_name, file_designator)
        else:
            actual_path = file_designator
        try:
            df = pd.read_csv(actual_path, sep='\t', header=0, keep_default_na=False, na_values=",null")
        except Exception:
            raise HedFileError("BadDataFile",
                               f"{str(actual_path)} (orig: {file_designator}) does not correspond to a valid tsv file",
                               "")
        return df

    def get_summary_save_dir(self):
        """ Return the directory in which to save the summaries.

        Returns:
            str: the data_root + remodeling summary path

        Raises:
            HedFileError  if this dispatcher does not have a data_root.

        """

        if self.data_root:
            return os.path.realpath(os.path.join(self.data_root, Dispatcher.REMODELING_SUMMARY_PATH))
        raise HedFileError("NoDataRoot", f"Dispatcher must have a data root to produce directories", "")

    def run_operations(self, file_path, sidecar=None, verbose=False):
        """ Run the dispatcher operations on a file.

        Parameters:
            file_path (str or DataFrame):    Full path of the file to be remodeled or a DataFrame
            sidecar (Sidecar or file-like):   Only needed for HED operations.
            verbose (bool):  If true, print out progress reports

        Returns:
            DataFrame:  The processed dataframe.

        """

        # string to functions
        if verbose:
            print(f"Reading {file_path}...")
        df = self.get_data_file(file_path)
        for operation in self.parsed_ops:
            df = self.prep_data(df)
            df = operation.do_op(self, df, file_path, sidecar=sidecar)
            df = self.post_proc_data(df)
        return df

    def save_summaries(self, save_formats=['.json', '.txt'], individual_summaries="separate", summary_dir=None):
        """ Save the summary files in the specified formats.

        Parameters:
            save_formats (list):  A list of formats [".txt", ."json"]
            individual_summaries (str): If True, include summaries of individual files.
            summary_dir (str or None): Directory for saving summaries

        The summaries are saved in the dataset derivatives/remodeling folder if no save_dir is provided.

        """
        if not save_formats:
            return
        if not summary_dir:
            summary_dir = self.get_summary_save_dir()
        os.makedirs(summary_dir, exist_ok=True)
        for context_name, context_item in self.context_dict.items():
            context_item.save(summary_dir, save_formats, individual_summaries=individual_summaries)

    @staticmethod
    def parse_operations(operation_list):
        errors = []
        operations = []
        for index, item in enumerate(operation_list):
            try:
                if not isinstance(item, dict):
                    raise TypeError("InvalidOperationFormat",
                                    f"Each operations must be a dictionary but operation {str(item)} is {type(item)}")
                if "operation" not in item:
                    raise KeyError("MissingOperation",
                                   f"operation {str(item)} does not have a operation key")
                if "parameters" not in item:
                    raise KeyError("MissingParameters",
                                   f"Operation {str(item)} does not have a parameters key")
                if item["operation"] not in valid_operations:
                    raise KeyError("OperationNotListedAsValid",
                                   f"Operation {item['operation']} must be added to operations_list "
                                   f"before it can be executed.")
                new_operation = valid_operations[item["operation"]](item["parameters"])
                operations.append(new_operation)
            except Exception as ex:
                errors.append({"index": index, "item": f"{item}", "error_type": type(ex),
                               "error_code": ex.args[0], "error_msg": ex.args[1]})
        if errors:
            return [], errors
        return operations, []

    @staticmethod
    def prep_data(df):
        """ Replace all n/a entries in the data frame by np.NaN for processing.

        Parameters:
            df (DataFrame) - The DataFrame to be processed.

        """
        return df.replace('n/a', np.NaN)

    @staticmethod
    def post_proc_data(df):
        """ Replace all nan entries with 'n/a' for BIDS compliance

        Parameters:
            df (DataFrame): The DataFrame to be processed.

        Returns:
            DataFrame: DataFrame with the 'np.NAN replaced by 'n/a'

        """
        return df.fillna('n/a')

    @staticmethod
    def errors_to_str(messages, title="", sep='\n'):
        error_list = [0]*len(messages)
        for index, message in enumerate(messages):
            error_list[index] = f"Operation[{message.get('index', None)}] " + \
                                f"has error:{message.get('error_type', None)}" + \
                                f" with error code:{message.get('error_code', None)} " + \
                                f"\n\terror msg:{message.get('error_msg', None)}"
        errors = sep.join(error_list)
        if title:
            return title + sep + errors
        return errors
