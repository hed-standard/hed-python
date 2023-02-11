""" Main command-line program for running the remodeling tools. """

import os
import json
import argparse
from hed.errors.exceptions import HedFileError
from hed.tools.util.io_util import get_file_list
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
    parser.add_argument("remodel_path", help="Full path of the file with remodeling instructions.")
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
    parser.add_argument("-n", "--backup-name", default=BackupManager.DEFAULT_BACKUP_NAME, dest="backup_name",
                        help="Name of the default backup for remodeling")
    parser.add_argument("-r", "--hed-versions", dest="hed_versions", nargs="*", default=[],
                        help="Optional list of HED schema versions used for annotation, include prefixes.")
    parser.add_argument("-s", "--save-formats", nargs="*", default=['.json', '.txt'], dest="save_formats",
                        help="Format for saving any summaries, if any. If empty, then no summaries are saved.")
    parser.add_argument("-t", "--task-names", dest="task_names", nargs="*", default=[], help="The names of the task.")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="If present, output informative messages as computation progresses.")
    parser.add_argument("-x", "--exclude-dirs", nargs="*", default=[], dest="exclude_dirs",
                        help="Directories names to exclude from search for files.")
    return parser


def parse_arguments(arg_list=None):
    """ Parse the command line arguments or arg_list if given. 
    
    Parameters:
        arg_list (list):  List of command line arguments as a list.
        
    Returns:
        Object:  Argument object
        List: A list of parsed operations (each operation is a dictionary).
        
    Raises:
        ValueError  - If the operations were unable to be correctly parsed.
    
    """
    parser = get_parser()
    args = parser.parse_args(arg_list)
    if '*' in args.file_suffix:
        args.file_suffix = None
    if '*' in args.extensions:
        args.extensions = None
    args.data_dir = os.path.realpath(args.data_dir)
    args.exclude_dirs = args.exclude_dirs + ['remodel']
    args.model_path = os.path.realpath(args.remodel_path)
    if args.verbose:
        print(f"Data directory: {args.data_dir}\nRemodel path: {args.remodel_path}")
    with open(args.remodel_path, 'r') as fp:
        operations = json.load(fp)
    parsed_operations, errors = Dispatcher.parse_operations(operations)
    if errors:
        raise ValueError("UnableToFullyParseOperations",
                         f"Fatal operation error, cannot continue:\n{Dispatcher.errors_to_str(errors)}")
    return args, operations


def run_bids_ops(dispatch, args):
    """ Run the remodeler on a BIDS dataset.
    
    Parameters:
        dispatch (Dispatcher): Manages the execution of the operations.
        args (Object): The command-line arguments as an object.

    """
    bids = BidsDataset(dispatch.data_root, tabular_types=['events'], exclude_dirs=args.exclude_dirs)
    dispatch.hed_schema = bids.schema
    if args.verbose:
        print(f"Successfully parsed BIDS dataset with HED schema {str(bids.get_schema_versions())}")
    events = bids.get_tabular_group(args.file_suffix)
    if args.verbose:
        print(f"Processing {dispatch.data_root}")
    for events_obj in events.datafile_dict.values():
        if args.task_names and events_obj.get_entity('task') not in args.task_names:
            continue
        sidecar_list = events.get_sidecars_from_path(events_obj)
        if sidecar_list:
            sidecar = events.sidecar_dict[sidecar_list[-1]].contents
        else:
            sidecar = None
        if args.verbose:
            print(f"Events {events_obj.file_path}  sidecar {sidecar}")
        df = dispatch.run_operations(events_obj.file_path, sidecar=sidecar, verbose=args.verbose)
        df.to_csv(events_obj.file_path, sep='\t', index=False, header=True)


def run_direct_ops(dispatch, args):
    """ Run the remodeler on files of a specified form in a directory tree.

    Parameters:
        dispatch (Dispatcher):  Controls the application of the operations and backup.
        args (dict): Dictionary of arguments and their values.

    """

    tabular_files = get_file_list(dispatch.data_root, name_suffix=args.file_suffix, extensions=args.extensions,
                                  exclude_dirs=args.exclude_dirs)
    if args.verbose:
        print(f"Found {len(tabular_files)} files with suffix {args.file_suffix} and extensions {str(args.extensions)}")
    if hasattr(args, 'json_sidecar'):
        sidecar = args.json_sidecar
    else:
        sidecar = None
    for file_path in tabular_files:
        if args.task_names and not BackupManager.get_task(args.task_names, file_path):
            continue
        df = dispatch.run_operations(file_path, verbose=args.verbose, sidecar=sidecar)
        df.to_csv(file_path, sep='\t', index=False, header=True)


def main(arg_list=None):
    """ The command-line program.

    Parameters:
        arg_list (list or None):   Called with value None when called from the command line.
                                   Otherwise, called with the command-line parameters as an argument list.

    Raises:
        HedFileError   
            - if the data root directory does not exist.  
            - if the specified backup does not exist.  

    """
    args, operations = parse_arguments(arg_list)
    if not os.path.isdir(args.data_dir):
        raise HedFileError("DataDirectoryDoesNotExist", f"The root data directory {args.data_dir} does not exist", "")
    if args.backup_name:
        backup_man = BackupManager(args.data_dir)
        if not backup_man.get_backup(args.backup_name):
            raise HedFileError("BackupDoesNotExist", f"Backup {args.backup_name} does not exist. "
                               f"Please run_remodel_backup first", "")
        backup_man.restore_backup(args.backup_name, args.task_names, verbose=args.verbose)
    dispatch = Dispatcher(operations, data_root=args.data_dir, backup_name=args.backup_name,
                          hed_versions=args.hed_versions)
    if args.use_bids:
        run_bids_ops(dispatch, args)
    else:
        run_direct_ops(dispatch, args)
    dispatch.save_summaries(args.save_formats, individual_summaries=args.individual_summaries)


if __name__ == '__main__':
    main()
