""" Manager for file backups for remodeling tools. """

import os
import json
import shutil
from datetime import datetime
from typing import Union

from hed.errors.exceptions import HedFileError
from hed.tools.util import io_util


class BackupManager:
    """ Manager for file backups for remodeling tools. """
    DEFAULT_BACKUP_NAME = 'default_back'
    RELATIVE_BACKUP_LOCATION = './derivatives/remodel/backups'
    BACKUP_DICTIONARY = 'backup_lock.json'
    BACKUP_ROOT = 'backup_root'

    def __init__(self, data_root, backups_root=None):
        """ Constructor for the backup manager.

        Parameters:
            data_root (str): Full path of the root of the data directory.
            backups_root (str or None):  Full path to the root where backups subdirectory is located.

        Raises:
            HedFileError: If the data_root does not correspond to a real directory.

        Notes: The backup_root will have remodeling/backups appended.
        """
        if not os.path.isdir(data_root):
            raise HedFileError('NonExistentData', f"{data_root} is not an existing directory", "")
        self.data_root = data_root
        if backups_root:
            self.backups_path = backups_root
        else:
            self.backups_path = os.path.join(data_root, self.RELATIVE_BACKUP_LOCATION)
        self.backups_path = os.path.realpath(self.backups_path)
        os.makedirs(self.backups_path, exist_ok=True)
        self.backups_dict = self._get_backups()

    def create_backup(self, file_list, backup_name=None, verbose=False) -> bool:
        """ Create a new backup from file_list.

        Parameters:
            file_list (list):   Full paths of the files to be in the backup.
            backup_name (str or None):  Name of the backup. If None, uses the default
            verbose (bool):     If True, print out the files that are being backed up.

        Returns:
            bool: True if the backup was successful. False if a backup of that name already exists.

        Raises:
            HedFileError: For missing or incorrect files.
            OS-related error: OS-related error when file copying occurs.

        """
        if not backup_name:
            backup_name = self.DEFAULT_BACKUP_NAME
        if self.backups_dict and backup_name in self.backups_dict:
            return False
        backup = {}
        time_stamp = f"{str(datetime.now())}"
        if verbose:
            print(f"Creating backup {backup_name}")
        backup_dir_path = os.path.realpath(os.path.join(self.backups_path, backup_name, BackupManager.BACKUP_ROOT))
        os.makedirs(backup_dir_path, exist_ok=True)
        for file in file_list:
            backup_file = self.get_backup_path(backup_name, file)
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
            if verbose:
                print(f"Copying {file} to {backup_file}")
            shutil.copy2(file, backup_file)
            backup[self.get_file_key(file)] = time_stamp
        self.backups_dict[backup_name] = backup
        backup_dict_path = os.path.realpath(os.path.join(self.backups_path, backup_name,
                                                         self.BACKUP_DICTIONARY))
        with open(backup_dict_path, 'w') as fp:
            json.dump(backup, fp, indent=4)
        return True

    def get_backup(self, backup_name) -> Union[dict, None]:
        """ Return the dictionary corresponding to backup_name.

        Parameters:
            backup_name (str): Name of the backup to be retrieved.

        Returns:
            Union[dict, None]: The dictionary with the backup info.

        Notes:
            The dictionary with backup information has keys that are the paths of
            the backed up files relative to the backup root. The values in this
            dictionary are the dates on which the particular file was backed up.

        """
        if backup_name not in self.backups_dict:
            return None
        return self.backups_dict[backup_name]

    def get_backup_files(self, backup_name, original_paths=False) -> list:
        """ Returns a list of full paths of files contained in the backup.

        Parameters:
            backup_name (str):  Name of the backup.
            original_paths (bool):   If True return the original paths.

        Returns:
            list: Full paths of the original files backed (original_paths=True) or the paths in the backup.

        Raises:
            HedFileError: If not backup named backup_name exists.

        """

        backup_dict = self.backups_dict.get(backup_name, None)
        if not backup_dict:
            raise HedFileError("NoBackup", f"{backup_name} is not a valid backup", "")

        if original_paths:
            return [os.path.realpath(os.path.join(self.data_root, backup_key)) for backup_key in backup_dict.keys()]
        else:
            return [os.path.realpath(os.path.join(self.backups_path, backup_name, self.BACKUP_ROOT, backup_key))
                    for backup_key in backup_dict.keys()]

    def get_backup_path(self, backup_name, file_name) -> str:
        """ Retrieve the file from the backup or throw an error.

        Parameters:
            backup_name (str): Name of the backup.
            file_name (str): Full path of the file to be retrieved.

        Returns:
            str:  Full path of the corresponding file in the backup.

        """
        return os.path.realpath(os.path.join(self.backups_path, backup_name, self.BACKUP_ROOT,
                                             self.get_file_key(file_name)))

    def get_file_key(self, file_name):
        file_comp = io_util.get_path_components(self.data_root, file_name) + [os.path.basename(file_name)]
        return '/'.join(file_comp)

    def restore_backup(self, backup_name=DEFAULT_BACKUP_NAME, task_names=[], verbose=True):
        """ Restore the files from backup_name to the main directory.

        Parameters:
            backup_name (str):  Name of the backup to restore.
            task_names (list):  A list of task names to restore.
            verbose (bool):  If True, print out the file names being restored.

        """
        if verbose:
            print(f"Restoring from backup {backup_name}")
        backup_files = self.get_backup_files(backup_name)
        data_files = self.get_backup_files(backup_name, original_paths=True)
        for index, file in enumerate(backup_files):
            if task_names and not self.get_task(task_names, file):
                continue
            os.makedirs(os.path.dirname(data_files[index]), exist_ok=True)
            if verbose:
                print(f"Copying {file} to {data_files[index]}")
            shutil.copy2(file, data_files[index])

    def _get_backups(self):
        """ Set the manager's backup-dictionary based on backup directory contents.

        Returns:
            dict: dictionary of dictionaries of the valid backups in the backups_path directory.

        Raises:
             HedFileError: If a backup is inconsistent for any reason.

        """
        backups = {}
        for backup in os.listdir(self.backups_path):
            backup_root = os.path.realpath(os.path.join(self.backups_path, backup))
            if not os.path.isdir(backup_root):
                raise HedFileError('BadBackupPath', f"{backup_root} is not a backup directory.", "")
            if len(os.listdir(backup_root)) != 2:
                raise HedFileError("BadBackupFormat",
                                   f"Backup {backup_root} must only contain backup_root and backup_lock.json file.", "")
            backup_dict, files_not_in_backup, backups_not_in_directory = self._check_backup_consistency(backup)
            if files_not_in_backup:
                raise HedFileError("MissingBackupFile", f"Backup {backup} has files not in backup_lock.json.", "")
            if backups_not_in_directory:
                raise HedFileError("ExtraFilesInBackup",
                                   f"Backup {backup} backup_lock.json entries not in backup directory.", "")
            backups[backup] = backup_dict
        return backups

    def _check_backup_consistency(self, backup_name):
        """ Return the consistency of a backup.

        Parameters:
            backup_name (str): Name of the backup.

        Returns:
            tuple[dict, list, list]:
            - Dictionary containing the backup info.
            - Files in backup directory that are not in the backup dict.
            - Files in backup dictionary not in backup directory.

        Notes:
            If file_path is None, this checks against consistency in the backup dictionary.

        """

        backup_dict_path = os.path.realpath(os.path.join(self.backups_path, backup_name, self.BACKUP_DICTIONARY))
        if not os.path.exists(backup_dict_path):
            raise HedFileError("BadBackupDictionaryPath",
                               f"Backup dictionary path {backup_dict_path} for backup "
                               f"{backup_name} does not exist so backup invalid", "")
        backup_root_path = os.path.realpath(os.path.join(self.backups_path, backup_name, self.BACKUP_ROOT))
        if not os.path.isdir(backup_root_path):
            raise HedFileError("BadBackupRootPath",
                               f"Backup root path {backup_root_path} for {backup_name} "
                               f"does not exist so backup invalid", "")
        with open(backup_dict_path, 'r') as fp:
            backup_dict = json.load(fp)
        backup_paths = set([os.path.realpath(os.path.join(backup_root_path, backup_key))
                            for backup_key in backup_dict.keys()])
        file_paths = set(io_util.get_file_list(backup_root_path))
        files_not_in_backup = list(file_paths.difference(backup_paths))
        backups_not_in_directory = list(backup_paths.difference(file_paths))
        return backup_dict, files_not_in_backup, backups_not_in_directory

    @staticmethod
    def get_task(task_names, file_path) -> str:
        """ Return the task if the file name contains a task_xxx where xxx is in task_names.

        Parameters:
            task_names (list):  List of task names (without the `task_` prefix).
            file_path (str):    Path of the filename to be tested.

        Returns:
            str:  the task name or '' if there is no task_xxx or xxx is not in task_names.

        """

        base = os.path.basename(file_path)
        for task in task_names:
            if ('task_' + task) in base:
                return task
        else:
            return ''

    def make_backup(self, task, backup_name=None, verbose=False) -> bool:
        """ Make a backup copy the files in the task file list.

        Parameters:
            task (dict):        Dictionary representing the remodeling task.
            backup_name (str or None):  Name of the backup. If None, uses the default
            verbose (bool):     If True, print out the files that are being backed up.

        Returns:
            bool: True if the backup was successful. False if a backup of that name already exists.

        Raises:
            HedFileError: For missing or incorrect files.
            OS-related error: OS-related error when file copying occurs.

        """
        if not backup_name:
            backup_name = self.DEFAULT_BACKUP_NAME
        if self.backups_dict and backup_name in self.backups_dict:
            return False
        backup = {}
        time_stamp = f"{str(datetime.now())}"
        if verbose:
            print(f"Creating backup {backup_name}")
        backup_dir_path = os.path.realpath(os.path.join(self.backups_path, backup_name, BackupManager.BACKUP_ROOT))
        os.makedirs(backup_dir_path, exist_ok=True)
        file_list = task.get('file_list', [])
        for file in file_list:
            backup_file = self.get_backup_path(backup_name, file)
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
            if verbose:
                print(f"Copying {file} to {backup_file}")
            shutil.copy2(file, backup_file)
            backup[self.get_file_key(file)] = time_stamp
        self.backups_dict[backup_name] = backup
        backup_dict_path = os.path.realpath(os.path.join(self.backups_path, backup_name,
                                                         self.BACKUP_DICTIONARY))
        with open(backup_dict_path, 'w') as fp:
            json.dump(backup, fp, indent=4)
        return True
