""" Command-line program for restoring files from remodeler backup. """

import argparse
from hed.errors.exceptions import HedFileError
from hed.tools.remodeling.backup_manager import BackupManager


def get_parser():
    """ Create a parser for the run_remodel_restore command-line arguments.

    Returns:
        argparse.ArgumentParser:  A parser for parsing the command line arguments.

    """
    parser = argparse.ArgumentParser(description="Restores the backup files for the original data.")
    parser.add_argument("data_dir", help="Full path of dataset root directory.")
    parser.add_argument("-bd", "--backup_dir", default="", dest="backup_dir",
                        help="Directory for the backup that is being created")
    parser.add_argument("-bn", "--backup_name", default=BackupManager.DEFAULT_BACKUP_NAME, dest="backup_name",
                        help="Name of the default backup for remodeling")
    parser.add_argument("-t", "--task-names", dest="task_names", nargs="*", default=[], help="The names of the task.")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="If present, output informative messages as computation progresses.")
    return parser


def main(arg_list=None):
    """ The command-line program for restoring a remodel backup.

    Parameters:
        arg_list (list or None):   Called with value None when called from the command line.
                                   Otherwise, called with the command-line parameters as an argument list.

    Raises:
        HedFileError: If the specified backup does not exist.

    """
    parser = get_parser()
    args = parser.parse_args(arg_list)
    if args.backup_dir:
        backups_root = args.backup_dir
    else:
        backups_root = None
    backup_man = BackupManager(args.data_dir, backups_root=backups_root)
    if not backup_man.get_backup(args.backup_name):
        raise HedFileError("BackupDoesNotExist", f"{args.backup_name}", "")
    backup_man.restore_backup(args.backup_name, task_names=args.task_names, verbose=args.verbose)


if __name__ == '__main__':
    main()
