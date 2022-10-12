import os
import numpy as np
import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.schema.hed_schema_io import get_schema
from hed.tools.remodeling.backup_manager import BackupManager
from hed.tools.remodeling.operations.valid_operations import valid_operations
from hed.tools.util.io_util import generate_filename


class Dispatcher:
    REMODELING_SUMMARY_PATH = 'derivatives/remodel/summaries'

    def __init__(self, operation_list, data_root=None,
                 backup_name=BackupManager.DEFAULT_BACKUP_NAME, hed_versions=None):
        """ Initialize the dispatcher.

        Parameters:
            operation_list (list): List of unparsed operations.
            data_root (str or None):  Root directory for the dataset. If none, then backups are not made.
            hed_versions (str, list, HedSchema, or HedSchemaGroup): The HED schema.

        """
        self.data_root = data_root
        self.backup_name = backup_name
        self.backup_man = None
        if self.data_root:
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

    def get_context_summaries(self, file_formats=['.txt', '.json'], verbose=True):
        """ Return the summaries in a dictionary suitable for saving or archiving.

        Parameters:
            file_formats (list):  List of formats for the context files ('.json' and '.txt' are allowed).
            verbose (bool): If true, a more extensive summary is archived.

        Returns:
            list: A list of dictionaries of summaries keyed to filenames.

        """

        summary_list = []
        for context_name, context_item in self.context_dict.items():
            file_base = generate_filename(context_item.context_filename, append_datetime=True)
            for file_format in file_formats:
                if file_format == '.txt':
                    summary = context_item.get_text_summary(verbose=True)
                elif file_format == '.json':
                    summary = context_item.get_summary(as_json=True)
                else:
                    continue
                summary_list.append({'file_name': file_base + file_format, 'file_format': file_format,
                                     'file_type': 'summary', 'content': summary})
        return summary_list

    def get_data_file(self, file_path):
        """ Full path of the backup file corresponding to the file path.

        Parameters:
            file_path (str): Full path of the dataframe in the original dataset.

        Returns:
            str: Full path of the corresponding file in the backup.

        """
        if self.backup_man:
            actual_path = self.backup_man.get_backup_path(self.backup_name, file_path)
        else:
            actual_path = file_path

        try:
            df = pd.read_csv(actual_path, sep='\t', header=0)
        except Exception:
            raise HedFileError("BadDataFile",
                               f"{str(actual_path)} (orig: {file_path}) does not correspond to "
                               f"a valid tab-separated value file", "")
        df = self.prep_events(df)
        return df

    def get_context_save_dir(self):
        """"""

        if self.data_root:
            return os.path.realpath(os.path.join(self.data_root, Dispatcher.REMODELING_SUMMARY_PATH))
        raise HedFileError("NoDataRoot", f"Dispatcher must have a data root to produce directories", "")

    def run_operations(self, file_path, sidecar=None, verbose=False):
        """ Run the dispatcher operations on a file.

        Parameters:
            file_path (str):      Full path of the file to be remodeled.
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
            df = operation.do_op(self, df, file_path, sidecar=sidecar)
        df = df.fillna('n/a')
        return df

    def save_context(self, save_formats=['.json', '.txt'], verbose=True):
        """ Save the summary files in the specified formats.

        Parameters:
            save_formats (list) list of formats [".txt", ."json"]
            verbose (bool) If include additional details

        The summaries are saved in the dataset derivatives/remodeling folder.

        """
        if not save_formats:
            return
        summary_path = self.get_context_save_dir()
        os.makedirs(summary_path, exist_ok=True)
        for context_name, context_item in self.context_dict.items():
            context_item.save(summary_path, save_formats, verbose=verbose)

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
                    raise KeyError("OperationCanNotBeDispatched",
                                   f"Operation {item['operation']} must be added to operations_list"
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
    def prep_events(df):
        """ Replace all n/a entries in the data frame by np.NaN for processing.

        Parameters:
            df (DataFrame) - The DataFrame to be processed.

        """
        df = df.replace('n/a', np.NaN)
        return df

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

    @staticmethod
    def save_archive(archive, archive_path):
        this_path = os.path.realpath(archive_path)
        os.makedirs(os.path.dirname(this_path), exist_ok=True)
        archive.seek(0)
        with open(this_path, "wb") as f:  # use `wb` mode
            f.write(archive.getvalue())

    @staticmethod
    def get_save_frame(df, filename):
        return {'file_name': filename,
                'file_format': '.tsv',
                'file_type': 'dataframe',
                'content': df.to_csv(None, sep='\t', index=False, header=True)}
