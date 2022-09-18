import os
import json
import shutil
from datetime import datetime
from hed.errors.exceptions import HedFileError
from hed.tools.util.io_util import extract_suffix_path, get_file_list, get_path_components


class BackupManager:
    RELATIVE_BACKUP_LOCATION = 'derivatives/remodeling/backups'
    BACKUP_DICTIONARY = 'backup_lock.json'
    BACKUP_ROOT = 'backup_root'

    def __init__(self, data_root):
        if not os.path.isdir(data_root):
            raise HedFileError('NonExistentData', f"{data_root} is not an existing directory", "")
        self.data_root = data_root
        self.backup_root = os.path.realpath(os.path.join(data_root, self.RELATIVE_BACKUP_LOCATION))
        os.makedirs(self.backup_root, exist_ok=True)
        self.backups = self._get_backups()

    def check_missing(self, backup_name, file_list):
        backup_dir, backup_dict, backup_root = self.get_backup_paths(backup_name)
        if not os.path.exists(backup_dict) or not os.path.isdir(backup_root):
            return file_list.copy()
        with open(backup_dict, 'r') as fp:
            backup_info = json.load(fp)
        base_set = set([extract_suffix_path(file, self.data_root) for file in file_list])
        back_set = set(backup_info)
        missing_list = []
        # in_list
        # for file in file_list:
        #     base_file = extract_suffix_path(file, self.data_root)
        #     backup_file = os.path.realpath(os.path.join(backup_root, base_file))
        #     if base_file not in backup_info or not os.path.exists(backup_file):
        #         missing_list.append(file)
        return missing_list

    def create_backup(self, backup_name, file_list):
        """ Create a new backup from file_list.

        Args:
            backup_name (str):  name of the backup.
            file_list (list):   full paths of the files to be in the backup.

        Returns:
            bool:  True if the backup was successful. False if a backup of that name already exists.

        Raises:
            Exceptions when file errors of any kind occur during the creation of a backup.
            
        """
        if backup_name in self.backups:
            return False
        backup_dir, backup_dict, backup_root = self.get_backup_paths(backup_name)
        backup = {}
        time_stamp = f"{str(datetime.now())}"
        for file in file_list:
            file_comp = get_path_components(self.data_root, file) + [os.path.basename(file)]
            backup_key = ('/').join(file_comp)
            backup_file = os.path.realpath(os.path.join(backup_root, backup_key))
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
            shutil.copy2(file, backup_file)
            backup[backup_key] = time_stamp
        self.backups[backup_name] = backup
        with open(backup_dict, 'w') as fp:
            json.dump(backup, fp, indent=4)
        return True

    def get_backup(self, backup_name):
        if backup_name not in self.backups:
            return None
        return self.backups[backup_name]

    #
    # backup_dir, backup_dict, backup_root = self.get_backup_paths(backup_name)
    # os.makedirs(backup_root, exist_ok=True)
    # backup = {}
    # for file in file_list:
    #     path_comps = get_path_components(file, self.data_root)
    #     if len(path_comps) > 1
    #
    # backup_lock_file = os.path.join(backup_root, self.BACKUP_DICTIONARY)
    # # now = datetime.now()
    # # filename = filename + '_' + now.strftime('%Y_%m_%d_T_%H_%M_%S_%f')
    # backup = {}
    # for file in file_list:
    #     file_base = os.path.relpath(file, self.data_root)
    #     print(file_base)

    # if os.path.isdir(backup_root) and os.path.exists(backup_lock):

    def get_backup_paths(self, backup_name):
        backup_dir = os.path.join(self.backup_root, backup_name)
        backup_dict = os.path.join(backup_dir, self.BACKUP_DICTIONARY)
        backup_root = os.path.join(backup_dir, self.BACKUP_ROOT)
        return backup_dir, backup_dict, backup_root

    def _get_backups(self):
        backups = {}
        for backup in os.listdir(self.backup_root):
            backup_path = os.path.join(self.backup_root, backup)
            if not os.path.isdir(backup_path):
                raise HedFileError('BadBackupPath', f"{backup_path} is not a backup directory", "")
            next_level = os.listdir(backup_path)
            if len(next_level) > 2 or 'backup_root' not in next_level or 'backup_lock.json' not in next_level:
                raise HedFileError("BadBackFormat", f"Backup {backup_path} should have just "
                                   f"backup_root directory and backup_lock.json file", "")
            (missing_backups, missing_files) = self.check_backup(backup_path)
            if missing_files:
                raise HedFileError("ExtraBackupFile", f"Backup {backup_path} backup_lock.json is missing "
                                   f"backup files {str(missing_files)}", "")
            if missing_backups:
                raise HedFileError("MissingBackupFile", f"Backup {backup_path} backup_lock.json has "
                                   f"backup files {str(missing_backups)} that are not backed up", "")
            backups[backup] = backup_path
        return backups

    def check_backup(self, backup_path, file_paths=None):
        backup_root = os.path.join(backup_path, 'backup_root')
        if not file_paths:
            file_paths = get_file_list(backup_root)
        file_paths = set(file_paths)
        backup_dict = os.path.join(backup_path, 'backup_lock.json')
        with open(backup_dict, 'r') as fp:
            backup_info = json.load(fp)
        backup_paths = set([os.path.realpath(os.path.join(backup_root, backup_key))
                            for backup_key in backup_info.keys()])
        files_not_in_backup = file_paths.difference(backup_paths)
        backups_not_in_files = backup_paths.difference(file_paths)
        return list(files_not_in_backup), list(backups_not_in_files)
        # def get_backup_dict(backup_root):
        #     backup_dict = {}
        #     backup_lock_file = os.path.realpath(os.path.join(backup_root, 'backup_lock.json'))
        #     with open(backup_lock_file, 'r') as fp:
        #         backup_lock = json.load(fp)
        # def compare_backup(self, backup_root, data_root, file_list):
        #     backup_list =  get_file_list(backup_root)
        #     backup_dict = {}
        #     for file in file_list:
        #         base_file = extract_suffix_path(file, data_root)
        #         backup os.path.realpath(os.path.join(backup_root, base_file)
        #         if os.path.realpath(os.path.join(backup_root, base_file))
        # def backup_files(self):
        #     verbose = hasattr(args, 'verbose')
        #     exclude_dirs = args.exclude_dirs.append('remodel')
        #     backup_path = os.path.realpath(os.path.join(args.data_dir, 'derivatives/remodel/backup'))
        #     os.makedirs(backup_path, exist_ok=True)
        #     file_list = get_file_list(args.data_dir, name_suffix=args.file_suffix, extensions=args.extensions,
        #                               exclude_dirs=exclude_dirs)
        #     if verbose:
        #         print(f"Data directory: {args.data_dir}\nBackup path: {backup_path}")
        #         print(f"Processing {len(file_list)} files with suffix {args.file_suffix} "
        #               f"and extensions {str(args.extensions)}")
        #     for orig_file in file_list:
        #         backup_base = extract_suffix_path(orig_file, args.data_dir)
        #         backup_file = os.path.realpath(backup_path + backup_base)
        #         if verbose:
        #             print(f"Original file: {orig_file}\nBackup file: {backup_file}")
        #         os.makedirs(os.path.dirname(backup_file), exist_ok=True)
        #         shutil.copy2(orig_file, backup_file)
