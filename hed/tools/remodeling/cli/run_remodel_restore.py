import argparse
from hed.errors.exceptions import HedFileError
from hed.tools.remodeling.backup_manager import BackupManager


def get_parser():
    parser = argparse.ArgumentParser(description="Restores the backup files for the original data.")
    parser.add_argument("data_dir", help="Full path of dataset root directory.")
    parser.add_argument("-n", "--backup_name", default=BackupManager.DEFAULT_BACKUP_NAME, dest="backup_name",
                        help="Name of the default backup for remodeling")
    parser.add_argument("-t", "--task-names", dest="task_names", nargs="*", default=[], help="The names of the task.")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="If present, output informative messages as computation progresses.")
    return parser


def main(arg_list=None):
    parser = get_parser()
    args = parser.parse_args(arg_list)
    backup_man = BackupManager(args.data_dir)
    if not backup_man.get_backup(args.backup_name):
        raise HedFileError("BackupDoesNotExist", f"{args.backup_name}", "")
    backup_man.restore_backup(args.backup_name, task_names=args.task_names, verbose=args.verbose)


if __name__ == '__main__':
    main()
