""" Command-line program for creating a remodeler backup. """

import argparse
from hed.errors.exceptions import HedFileError
from hed.tools.util import io_util
from hed.tools.remodeling.backup_manager import BackupManager


def get_parser():
    """ Create a parser for the run_remodel_backup command-line arguments.

    Returns:
        argparse.ArgumentParser:  A parser for parsing the command line arguments.

    """
    parser = argparse.ArgumentParser(description="Creates a backup for the remodeling process.")
    parser.add_argument("data_dir", help="Full path of dataset root directory.")
    parser.add_argument("-bd", "--backup_dir", default="", dest="backup_dir",
                        help="Directory for the backup that is being created")
    parser.add_argument("-bn", "--backup_name", default=BackupManager.DEFAULT_BACKUP_NAME, dest="backup_name",
                        help="Name of the default backup for remodeling")
    parser.add_argument("-fs", "--file-suffix", dest="suffixes", nargs="*", default=['events'],
                        help="Filename suffix of files to be backed up. A * indicates all files allowed.")

    parser.add_argument("-t", "--task-names", dest="task_names", nargs="*", default=[], help="The name of the task.")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="If present, output informative messages as computation progresses.")
    parser.add_argument("-x", "--exclude-dirs", nargs="*", default=['derivatives'], dest="exclude_dirs",
                        help="Directories names to exclude from search for files. " +
                             "If omitted, no directories except the backup directory will be excluded." +
                             "Note [data_root]/derivatives/remodel will always be excluded.")
    return parser


def main(arg_list=None):
    """ The command-line program for making a remodel backup.

    Parameters:
        arg_list (list or None):   Called with value None when called from the command line.
                                   Otherwise, called with the command-line parameters as an argument list.

    Raises:
        HedFileError: If the specified backup already exists.

    """

    parser = get_parser()
    args = parser.parse_args(arg_list)
    if '*' in args.suffixes:
        args.suffixes = None
    exclude_dirs = args.exclude_dirs + ['remodeling']
    file_list = io_util.get_file_list(args.data_dir, name_suffix=args.suffixes, extensions=['.tsv'],
                                      exclude_dirs=exclude_dirs)
    if args.task_names:
        file_list = io_util.get_filtered_by_element(file_list, args.task_names)
    if args.backup_dir:
        backups_root = args.backup_dir
    else:
        backups_root = None
    backup_man = BackupManager(args.data_dir, backups_root=backups_root)
    if backup_man.get_backup(args.backup_name):
        raise HedFileError("BackupExists", f"Backup {args.backup_name} already exists", "")
    else:
        backup_man.create_backup(file_list, backup_name=args.backup_name, verbose=args.verbose)


if __name__ == '__main__':
    main()
