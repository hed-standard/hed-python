""" Main command-line program for running the remodeling tools. """

import os
import io
import json
import argparse
import logging
from hed.errors.exceptions import HedFileError
from hed.models.sidecar import Sidecar
from hed.tools.remodeling.remodeler_validator import RemodelerValidator
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.backup_manager import BackupManager
from hed.tools.util import io_util
from hed.tools.bids import bids_util


def get_parser():
    """ Create a parser for the run_remodel command-line arguments.

    Returns:
        argparse.ArgumentParser:  A parser for parsing the command line arguments.

    """
    parser = argparse.ArgumentParser(description="Converts event files based on a json file specifying operations.")
    parser.add_argument("data_dir", help="Full path of dataset root directory.")
    parser.add_argument("model_path", help="Full path of the file with remodeling instructions.")
    parser.add_argument("-bd", "--backup_dir", default="", dest="backup_dir",
                        help="Directory for the backup that is being created")
    parser.add_argument("-bn", "--backup_name", default=BackupManager.DEFAULT_BACKUP_NAME, dest="backup_name",
                        help="Name of the default backup for remodeling")
    parser.add_argument("-b", "--bids-format", action='store_true', dest="use_bids",
                        help="If present, the dataset is in BIDS format with sidecars. HED analysis is available.")
    parser.add_argument("-fs", "--file-suffix", dest="suffixes", nargs="*", default=['events'],
                        help="Optional list of suffixes (no under_bar) of tsv files to validate. If -s with no values, will use all possible suffixes as with single argument '*'.")
    parser.add_argument("-i", "--individual-summaries", dest="individual_summaries", default="separate",
                        choices=["separate", "consolidated", "none"],
                        help="Controls individual file summaries ('none', 'separate', 'consolidated')")
    parser.add_argument("-j", "--json-sidecar", dest="json_sidecar", nargs="?",
                        help="Optional path to JSON sidecar with HED information")
    parser.add_argument("-ld", "--log_dir", dest="log_dir", default="",
                        help="Directory for storing log entries for errors.")
    parser.add_argument("-nb", "--no-backup", action='store_true', dest="no_backup",
                        help="If present, the operations are run directly on the files with no backup.")
    parser.add_argument("-ns", "--no-summaries", action='store_true', dest="no_summaries",
                        help="If present, the summaries are not saved, but rather discarded.")
    parser.add_argument("-nu", "--no-update", action='store_true', dest="no_update",
                        help="If present, the files are not saved, but rather discarded.")
    parser.add_argument("-hv", "--hed-versions", dest="hed_versions", nargs="*", default=[],
                        help="Optional list of HED schema versions used for annotation, include prefixes.")
    parser.add_argument("-s", "--save-formats", nargs="*", default=['.json', '.txt'], dest="save_formats",
                        help="Format for saving any summaries, if any. If no summaries are to be written," +
                             "use the -ns option.")
    parser.add_argument("-t", "--task-names", dest="task_names", nargs="*", default=[],
                        help="The names of the task. If an empty list is given, all tasks are lumped together." +
                        " If * is given, then tasks are found and reported individually.")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="If present, output informative messages as computation progresses.")
    parser.add_argument("-w", "--work-dir", default="", dest="work_dir",
                        help="If given, is the path to directory for saving, otherwise derivatives/remodel is used.")
    parser.add_argument("-x", "--exclude-dirs", nargs="*", default=[], dest="exclude_dirs",
                        help="Directories names to exclude from search for files.")
    return parser


def handle_backup(args):
    """ Restore the backup if applicable.

    Parameters:
        args (obj): Parsed arguments as an object.

    Returns:
        Union[str, None]:  Backup name if there was a backup done.

    """
    if args.no_backup:
        backup_name = None
    else:
        backup_man = BackupManager(args.data_dir)
        if not backup_man.get_backup(args.backup_name):
            raise HedFileError("BackupDoesNotExist", f"Backup {args.backup_name} does not exist. "
                               f"Please run_remodel_backup first", "")
        backup_man.restore_backup(args.backup_name, args.task_names, verbose=args.verbose)
        backup_name = args.backup_name
    return backup_name


def parse_arguments(arg_list=None):
    """ Parse the command line arguments or arg_list if given.

    Parameters:
        arg_list (list):  List of command line arguments as a list.

    Returns:
        Tuple[Object, list]:
        - Argument object.
        - A list of parsed operations (each operation is a dictionary).

    Raises:
        ValueError: If the operations were unable to be correctly parsed.

    """
    parser = get_parser()
    args = parser.parse_args(arg_list)
    if '*' in args.suffixes:
        args.suffixes = None
    args.data_dir = os.path.realpath(args.data_dir)
    args.exclude_dirs = args.exclude_dirs + ['remodel']
    args.model_path = os.path.realpath(args.model_path)
    if args.verbose:
        print(f"Data directory: {args.data_dir}\nModel path: {args.model_path}")
    with open(args.model_path, 'r') as fp:
        operations = json.load(fp)
    validator = RemodelerValidator()
    errors = validator.validate(operations)
    if errors:
        raise ValueError("UnableToFullyParseOperations",
                         f"Fatal operation error, cannot continue:\n{errors}")
    return args, operations


def parse_tasks(files, task_args):
    """ Parse the tasks argument to get a task list.

    Parameters:
        files (list):  List of full paths of files.
        task_args (str or list):  The argument values for the task parameter.

    """
    if not task_args:
        return {"": files}
    task_dict = io_util.get_task_dict(files)
    if task_args == "*" or isinstance(task_args, list) and task_args[0] == "*":
        return task_dict
    task_dict = {key: task_dict[key] for key in task_args if key in task_dict}
    return task_dict


def run_ops(dispatch, args, tabular_files):
    """ Run the remodeler on files of a specified form in a directory tree.

    Parameters:
        dispatch (Dispatcher):  Controls the application of the operations and backup.
        args (argparse.Namespace): Dictionary of arguments and their values.
        tabular_files (list): List of files to include in this run.

    """

    if args.verbose:
        print(f"Found {len(tabular_files)} files to process")
    if hasattr(args, 'json_sidecar'):
        base_sidecar = Sidecar(args.json_sidecar, name=args.json_sidecar)
    else:
        base_sidecar = None
    for file_path in tabular_files:
        if not base_sidecar and args.use_bids:
            sidecar = get_sidecar(file_path, args.data_dir)
        else:
            sidecar = base_sidecar
        if args.verbose:
            print(f"Tabular file {file_path}  sidecar {str(sidecar)}")
        df = dispatch.run_operations(file_path, verbose=args.verbose, sidecar=sidecar)
        if not args.no_update:
            df.to_csv(file_path, sep='\t', index=False, header=True)

def get_sidecar(data_dir, tsv_path):
    """ Get the sidecar for a file if it exists.

    Parameters:
        data_dir (str):  Full path of the data directory.
        tsv_path (str):  Full path of the file.

    Returns:
        Union[Sidecar, None]:  The Sidecar if it exists, otherwise None.

    """
    merged_dict = bids_util.get_merged_sidecar(data_dir, tsv_path)
    if not merged_dict:
        return None
    name = 'merged_' + io_util.get_basename(tsv_path)[0] + '.json'
    return Sidecar(files=io.StringIO(json.dumps(merged_dict)), name=name)

def main(arg_list=None):
    """ The command-line program.

    Parameters:
        arg_list (list or None):   Called with value None when called from the command line.
                                   Otherwise, called with the command-line parameters as an argument list.

    Raises:
        HedFileError:
        - if the data root directory does not exist.
        - if the specified backup does not exist.

    """
    args, operations = parse_arguments(arg_list)

    if args.log_dir:
        os.makedirs(args.log_dir, exist_ok=True)
        timestamp = '_' + io_util.get_timestamp()
    else:
        timestamp = ''
    try:
        if not os.path.isdir(args.data_dir):
            raise HedFileError("DataDirectoryDoesNotExist",
                               f"The root data directory {args.data_dir} does not exist", "")
        backup_name = handle_backup(args)
        save_dir = None
        if args.work_dir:
            save_dir = os.path.realpath(os.path.join(args.work_dir, Dispatcher.REMODELING_SUMMARY_PATH))
        tsv_files = io_util.get_file_list(args.data_dir, name_suffix=args.suffixes, extensions=[".tsv"],
                                      exclude_dirs=args.exclude_dirs)
        task_dict = parse_tasks(tsv_files, args.task_names)
        for task, files in task_dict.items():
            dispatch = Dispatcher(operations, data_root=args.data_dir, backup_name=backup_name,
                                  hed_versions=args.hed_versions)
            run_ops(dispatch, args, files)
            if not args.no_summaries:
                dispatch.save_summaries(args.save_formats, individual_summaries=args.individual_summaries,
                                        summary_dir=save_dir, task_name=task)
    except Exception:
        if args.log_dir:
            log_name = io_util.get_alphanumeric_path(os.path.realpath(args.data_dir)) + timestamp + '.txt'
            logging.basicConfig(filename=os.path.join(args.log_dir, log_name), level=logging.ERROR)
            logging.exception(f"{args.data_dir}: {args.model_path}")
        raise


if __name__ == '__main__':
    main()
