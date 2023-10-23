""" Main command-line program for running the remodeling tools. """

import os
import json
import argparse
from hed.errors.exceptions import HedFileError
from hed.tools.util.io_util import get_file_list, get_task_from_file
from hed.tools.bids.bids_dataset import BidsDataset
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.backup_manager import BackupManager


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
    parser.add_argument("-e", "--extensions", nargs="*", default=['.tsv'], dest="extensions",
                        help="File extensions to allow in locating files.")
    parser.add_argument("-f", "--file-suffix", dest="file_suffix", default='events',
                        help="Filename suffix excluding file type of items to be analyzed (events by default).")
    parser.add_argument("-i", "--individual-summaries", dest="individual_summaries", default="separate",
                        choices=["separate", "consolidated", "none"],
                        help="Controls individual file summaries ('none', 'separate', 'consolidated')")
    parser.add_argument("-j", "--json-sidecar", dest="json_sidecar", nargs="?",
                        help="Optional path to JSON sidecar with HED information")
#    parser.add_argument("-n", "--backup-name", default=BackupManager.DEFAULT_BACKUP_NAME, dest="backup_name",
#                        help="Name of the default backup for remodeling")
    parser.add_argument("-nb", "--no-backup", action='store_true', dest="no_backup",
                        help="If present, the operations are run directly on the files with no backup.")
    parser.add_argument("-ns", "--no-summaries", action='store_true', dest="no_summaries",
                        help="If present, the summaries are not saved, but rather discarded.")
    parser.add_argument("-nu", "--no-update", action='store_true', dest="no_update",
                        help="If present, the files are not saved, but rather discarded.")
    parser.add_argument("-r", "--hed-versions", dest="hed_versions", nargs="*", default=[],
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
    """ Restores the backup if applicable.

    Parameters:
        args (obj): parsed arguments as an object.

    Returns:
        str or None:  backup name if there was a backup done.

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
        Object:  Argument object
        List: A list of parsed operations (each operation is a dictionary).

    :raises ValueError:
        - If the operations were unable to be correctly parsed.

    """
    parser = get_parser()
    args = parser.parse_args(arg_list)
    if '*' in args.file_suffix:
        args.file_suffix = None
    if '*' in args.extensions:
        args.extensions = None
    args.data_dir = os.path.realpath(args.data_dir)
    args.exclude_dirs = args.exclude_dirs + ['remodel']
    args.model_path = os.path.realpath(args.model_path)
    if args.verbose:
        print(f"Data directory: {args.data_dir}\nModel path: {args.model_path}")
    with open(args.model_path, 'r') as fp:
        operations = json.load(fp)
    parsed_operations, errors = Dispatcher.parse_operations(operations)
    if errors:
        raise ValueError("UnableToFullyParseOperations",
                         f"Fatal operation error, cannot continue:\n{Dispatcher.errors_to_str(errors)}")
    return args, operations


def parse_tasks(files, task_args):
    if not task_args:
        return {"": files}
    task_dict = {}
    for my_file in files:
        task = get_task_from_file(my_file)
        if not task:
            continue
        task_entry = task_dict.get(task, [])
        task_entry.append(my_file)
        task_dict[task] = task_entry
    if task_args == "*" or isinstance(task_args, list) and task_args[0] == "*":
        return task_dict
    task_dict = {key: task_dict[key] for key in task_args if key in task_dict}
    return task_dict


def run_bids_ops(dispatch, args, tabular_files):
    """ Run the remodeler on a BIDS dataset.

    Parameters:
        dispatch (Dispatcher): Manages the execution of the operations.
        args (Object): The command-line arguments as an object.
        tabular_files (list): List of tabular files to run the ops on.

    """
    bids = BidsDataset(dispatch.data_root, tabular_types=['events'], exclude_dirs=args.exclude_dirs)
    dispatch.hed_schema = bids.schema
    if args.verbose:
        print(f"Successfully parsed BIDS dataset with HED schema {str(bids.schema.get_schema_versions())}")
    data = bids.get_tabular_group(args.file_suffix)
    if args.verbose:
        print(f"Processing {dispatch.data_root}")
    filtered_events = [data.datafile_dict[key] for key in tabular_files]
    for data_obj in filtered_events:
        sidecar_list = data.get_sidecars_from_path(data_obj)
        if sidecar_list:
            sidecar = data.sidecar_dict[sidecar_list[-1]].contents
        else:
            sidecar = None
        if args.verbose:
            print(f"Tabular file {data_obj.file_path}  sidecar {sidecar}")
        df = dispatch.run_operations(data_obj.file_path, sidecar=sidecar, verbose=args.verbose)
        if not args.no_update:
            df.to_csv(data_obj.file_path, sep='\t', index=False, header=True)


def run_direct_ops(dispatch, args, tabular_files):
    """ Run the remodeler on files of a specified form in a directory tree.

    Parameters:
        dispatch (Dispatcher):  Controls the application of the operations and backup.
        args (argparse.Namespace): Dictionary of arguments and their values.
        tabular_files (list): List of files to include in this run.

    """

    if args.verbose:
        print(f"Found {len(tabular_files)} files with suffix {args.file_suffix} and extensions {str(args.extensions)}")
    if hasattr(args, 'json_sidecar'):
        sidecar = args.json_sidecar
    else:
        sidecar = None
    for file_path in tabular_files:
        if args.verbose:
            print(f"Tabular file {file_path}  sidecar {sidecar}")
        df = dispatch.run_operations(file_path, verbose=args.verbose, sidecar=sidecar)
        if not args.no_update:
            df.to_csv(file_path, sep='\t', index=False, header=True)


def main(arg_list=None):
    """ The command-line program.

    Parameters:
        arg_list (list or None):   Called with value None when called from the command line.
                                   Otherwise, called with the command-line parameters as an argument list.

    :raises HedFileError:
        - if the data root directory does not exist.
        - if the specified backup does not exist.

    """
    args, operations = parse_arguments(arg_list)
    if not os.path.isdir(args.data_dir):
        raise HedFileError("DataDirectoryDoesNotExist", f"The root data directory {args.data_dir} does not exist", "")
    backup_name = handle_backup(args)
    save_dir = None
    if args.work_dir:
        save_dir = os.path.realpath(os.path.join(args.work_dir, Dispatcher.REMODELING_SUMMARY_PATH))
    files = get_file_list(args.data_dir, name_suffix=args.file_suffix, extensions=args.extensions,
                          exclude_dirs=args.exclude_dirs)
    task_dict = parse_tasks(files, args.task_names)
    for task, files in task_dict.items():
        dispatch = Dispatcher(operations, data_root=args.data_dir, backup_name=backup_name,
                              hed_versions=args.hed_versions)
        if args.use_bids:
            run_bids_ops(dispatch, args, files)
        else:
            run_direct_ops(dispatch, args, files)
        if not args.no_summaries:
            dispatch.save_summaries(args.save_formats, individual_summaries=args.individual_summaries, 
                                    summary_dir=save_dir, task_name=task)


if __name__ == '__main__':
    main()
