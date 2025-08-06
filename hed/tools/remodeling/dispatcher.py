""" Controller for applying operations to tabular files and saving the results. """

from __future__ import annotations
import os
from typing import Union

import numpy as np
import pandas as pd
import json
from hed.errors.exceptions import HedFileError
from hed.schema.hed_schema_io import load_schema_version
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.tools.remodeling.backup_manager import BackupManager
from hed.tools.remodeling.operations.valid_operations import valid_operations
from hed.tools.util import io_util

# This isn't supported in all versions of pandas
try:
    pd.set_option('future.no_silent_downcasting', True)
except pd.errors.OptionError:
    pass


class Dispatcher:
    """ Controller for applying operations to tabular files and saving the results. """

    REMODELING_SUMMARY_PATH = 'remodel/summaries'

    def __init__(self, operation_list, data_root=None,
                 backup_name=BackupManager.DEFAULT_BACKUP_NAME, hed_versions=None):
        """ Constructor for the dispatcher.

        Parameters:
            operation_list (list): List of valid unparsed operations.
            data_root (str or None):  Root directory for the dataset. If none, then backups are not made.
            hed_versions (str, list, HedSchema, or HedSchemaGroup): The HED schema.

        Raises:
            HedFileError: If the specified backup does not exist.
            ValueError: If any of the operations cannot be parsed correctly.
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
        self.parsed_ops = self.parse_operations(operation_list)
        self.hed_schema = self.get_schema(hed_versions)
        self.summary_dicts = {}

    def get_summaries(self, file_formats=['.txt', '.json']) -> list[dict]:
        """ Return the summaries in a dictionary of strings suitable for saving or archiving.

        Parameters:
            file_formats (list):  List of formats for the context files ('.json' and '.txt' are allowed).

        Returns:
            list[dict]: A list of dictionaries of summaries keyed to filenames.
        """

        summary_list = []
        time_stamp = '_' + io_util.get_timestamp()
        for context_name, context_item in self.summary_dicts.items():
            file_base = context_item.op.summary_filename
            if self.data_root:
                file_base = io_util.extract_suffix_path(self.data_root, file_base)
            file_base = io_util.clean_filename(file_base)
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

    def get_data_file(self, file_designator) -> 'pd.DataFrame':
        """ Get the correct data file give the file designator.

        Parameters:
            file_designator (str, DataFrame ): A dataFrame or the full path of the dataframe in the original dataset.

        Returns:
            pd.DataFrame:  DataFrame after reading the path.

        Raises
            HedFileError: If a valid file cannot be found.

        Notes:
            - If a string is passed and there is a backup manager,
              the string must correspond to the full path of the file in the original dataset.
              In this case, the corresponding backup file is read and returned.
            - If a string is passed and there is no backup manager,
              the data file corresponding to the file_designator is read and returned.
            - If a Pandas DataFrame, return a copy.
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

    def get_summary_save_dir(self) -> str:
        """ Return the directory in which to save the summaries.

        Returns:
            str: the data_root + remodeling summary path

        Raises
            HedFileError: If this dispatcher does not have a data_root.
        """

        if self.data_root:
            return os.path.realpath(os.path.join(self.data_root, 'derivatives', Dispatcher.REMODELING_SUMMARY_PATH))
        raise HedFileError("NoDataRoot", "Dispatcher must have a data root to produce directories", "")

    def run_operations(self, file_path, sidecar=None, verbose=False) -> 'pd.DataFrame':
        """ Run the dispatcher operations on a file.

        Parameters:
            file_path (str or DataFrame):    Full path of the file to be remodeled or a DataFrame.
            sidecar (Sidecar or file-like):   Only needed for HED operations.
            verbose (bool):  If True, print out progress reports.

        Returns:
            pd.DataFrame:  The processed dataframe.
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

    def save_summaries(self, save_formats=['.json', '.txt'], individual_summaries="separate",
                       summary_dir=None, task_name=""):
        """ Save the summary files in the specified formats.

        Parameters:
            save_formats (list):  A list of formats [".txt", ."json"]
            individual_summaries (str):  "consolidated", "individual", or "none".
            summary_dir (str or None): Directory for saving summaries.
            task_name (str): Name of task if summaries separated by task or "" if not separated.

        Notes:
            The summaries are saved in the dataset derivatives/remodeling folder if no save_dir is provided.

        Notes:
            - "consolidated" means that the overall summary and summaries of individual files are in one summary file.
            - "individual" means that the summaries of individual files are in separate files.
            - "none" means that only the overall summary is produced.
        """

        if not save_formats:
            return
        if not summary_dir:
            summary_dir = self.get_summary_save_dir()
        os.makedirs(summary_dir, exist_ok=True)
        for summary_name, summary_item in self.summary_dicts.items():
            summary_item.save(summary_dir, save_formats, individual_summaries=individual_summaries, task_name=task_name)

    @staticmethod
    def parse_operations(operation_list) -> list:
        """ Return a parsed a list of remodeler operations.

        Parameters:
            operation_list (list): List of JSON remodeler operations.

        Returns:
            list: List of Python objects containing parsed remodeler operations.
        """

        operations = []
        for index, item in enumerate(operation_list):
            new_operation = valid_operations[item["operation"]](item["parameters"])
            operations.append(new_operation)
        return operations

    @staticmethod
    def prep_data(df) -> 'pd.DataFrame':
        """ Make a copy and replace all n/a entries in the data frame by np.nan for processing.

        Parameters:
            df (DataFrame): The DataFrame to be processed.

        Returns:
            DataFrame: A copy of the DataFrame with n/a entries replaced by np.nan.
        """

        result = df.replace('n/a', np.nan)
        # Comment in the next line if this behavior was actually needed, but I don't think it is.
        # result = result.infer_objects(copy=False)
        return result

    @staticmethod
    def post_proc_data(df) -> 'pd.DataFrame':
        """ Replace all nan entries with 'n/a' for BIDS compliance.

        Parameters:
            df (DataFrame): The DataFrame to be processed.

        Returns:
            pd.DataFrame: DataFrame with the 'np.nan replaced by 'n/a'.
        """

        dtypes = df.dtypes.to_dict()
        for col_name, typ in dtypes.items():
            if typ == 'category':
                df[col_name] = df[col_name].astype(str)
        return df.fillna('n/a')

    @staticmethod
    def errors_to_str(messages, title="", sep='\n') -> str:
        """ Return an error string representing error messages in a list.

        Parameters:
            messages (list of dict):  List of error dictionaries each representing a single error.
            title (str):  If provided the title is concatenated at the top.
            sep (str): Character used between lines in concatenation.

        Returns:
            str:  Single string representing the messages.
        """

        error_list = [0] * len(messages)
        for index, message in enumerate(messages):
            error_list[index] = f"Operation[{message.get('index', None)}] " + \
                                f"has error:{message.get('error_type', None)}" + \
                                f" with error code:{message.get('error_code', None)} " + \
                                f"\n\terror msg:{message.get('error_msg', None)}"
        errors = sep.join(error_list)
        if title:
            return title + sep + errors
        return errors

    @staticmethod
    def get_schema(hed_versions) -> Union['HedSchema', 'HedSchemaGroup', None]:
        """ Return the schema objects represented by the hed_versions.

        Parameters:
            hed_versions (str, list, HedSchema, HedSchemaGroup): If str, interpreted as a version number.

        Returns:
             Union[HedSchema, HedSchemaGroup, None]: Objects loaded from the hed_versions specification.
        """

        if not hed_versions:
            return None
        elif isinstance(hed_versions, str) or isinstance(hed_versions, list):
            return load_schema_version(hed_versions)
        elif isinstance(hed_versions, HedSchema) or isinstance(hed_versions, HedSchemaGroup):
            return hed_versions
        else:
            raise ValueError("InvalidHedSchemaOrSchemaVersion", "Expected schema or schema version")
