import os
import json
import shutil
from datetime import datetime
from hed.errors.exceptions import HedFileError
from hed.tools.util.io_util import get_file_list, get_path_components


class BackupManager:
    DEFAULT_BACKUP_NAME = 'default_back'
    RELATIVE_BACKUP_LOCATION = 'derivatives/remodel/backups'
    BACKUP_DICTIONARY = 'backup_lock.json'
    BACKUP_ROOT = 'backup_root'

    def __init__(self, data_root):
        if not os.path.isdir(data_root):
            raise HedFileError('NonExistentData', f"{data_root} is not an existing directory", "")
        self.data_root = data_root
        self.backups_root = os.path.join(data_root, self.RELATIVE_BACKUP_LOCATION)
        os.makedirs(self.backups_root, exist_ok=True)
        self.backups_dict = self._get_backups()

    def check_backup_files(self, backup_name, file_paths=None):
        """ Return the files in file_paths that are not backed up and vice-versa.

        Parameters:
            backup_name (str): Name of the backup.
            file_paths (list):  List of full paths of files to be checked against the backup.

        Returns:
            list:  Files in file_paths that are not in the backup.
            list:  Files in backup not in file_paths

        Notes:
            If file_path is None, this checks against consistency in the backup dictionary.

        """

        backup_paths = self.get_backup_files(backup_name)
        if not file_paths:
            return [], backup_paths
        backup_path_set = set(backup_paths)
        file_path_set = set(file_paths)
        files_not_in_backup = list(file_path_set.difference(backup_path_set))
        backups_not_in_files = list(backup_path_set.difference(file_path_set))
        return files_not_in_backup, backups_not_in_files

    def create_backup(self, backup_name, file_list, verbose=True):
        """ Create a new backup from file_list.

        Parameters:
            backup_name (str or None):  Name of the backup.
            file_list (list):   Full paths of the files to be in the backup.
            verbose (bool):     If True, print out the files that are being backed up.

        Returns:
            bool:  True if the backup was successful. False if a backup of that name already exists.

        Raises:
            Exceptions when file errors of any kind occur during the creation of a backup.

        """
        if not backup_name:
            backup_name = self.DEFAULT_BACKUP_NAME
        if self.backups_dict:
            return False
        backup = {}
        time_stamp = f"{str(datetime.now())}"
        if verbose:
            print(f"Creating backup {backup_name}")
        for file in file_list:
            backup_file = self.get_backup_path(backup_name, file)
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
            if verbose:
                print(f"Copying {file} to {backup_file}")
            shutil.copy2(file, backup_file)
            backup[self.get_file_key(file)] = time_stamp
        self.backups_dict[backup_name] = backup
        backup_dir_path = os.path.join(self.backups_root, backup_name)
        backup_dict_path = os.path.join(self.backups_root, backup_name, backup_dir_path, self.BACKUP_DICTIONARY)
        with open(os.path.realpath(backup_dict_path), 'w') as fp:
            json.dump(backup, fp, indent=4)
        return True

    def get_backup(self, backup_name):
        """ Return the dictionary corresponding to backup_name.

        Args:
            backup_name (str): Name of the backup to be retrieved.

        Returns:
            The dictionary with the backup info.

        """
        if backup_name not in self.backups_dict:
            return None
        return self.backups_dict[backup_name]

    def get_backup_files(self, backup_name, original_paths=False):
        """ Returns a list of full paths of files contained in the backup.

        Args:
            backup_name (str):       Name of the backup.
            original_paths (bool):   If true return the original paths.

        Returns:
            list:  Full paths of the original files backed (original_paths=True) or the paths in the backup.

        Raises:
            HedFileError - if not backup named backup_name exists.

        """

        backup_dict = self.backups_dict.get(backup_name, None)
        if not backup_dict:
            raise HedFileError("NoBackup", f"{backup_name} is not a valid backup", "")
        if original_paths:
            return [os.path.realpath(os.path.join(self.data_root, backup_key)) for backup_key in backup_dict.keys()]
        return [os.path.realpath(os.path.join(self.backups_root, backup_name, self.BACKUP_ROOT, backup_key))
                for backup_key in backup_dict.keys()]

    def get_backup_path(self, backup_name, file_name):
        """ Retrieve the file from the backup or throw an error.

        Args:
            backup_name (str): Name of the backup
            file_name (str): Full path of the file to be retrieved.

        Returns:
            str:  Full path of the corresponding file in the backup.

        """
        return os.path.realpath(os.path.join(self.backups_root, backup_name, self.BACKUP_ROOT,
                                             self.get_file_key(file_name)))

    def get_file_key(self, file_name):
        file_comp = get_path_components(self.data_root, file_name) + [os.path.basename(file_name)]
        return '/'.join(file_comp)

    def restore_backup(self, backup_name=DEFAULT_BACKUP_NAME, verbose=True):
        """ Restore the files from backup_name to the main directory.

        Args:
            backup_name (str):  Name of the backup to restore
            verbose (bool):  If true, print out the file names being restored.

        """
        if verbose:
            print(f"Restoring from backup {backup_name}")
        backup_files = self.get_backup_files(backup_name)
        data_files = self.get_backup_files(backup_name, original_paths=True)
        for index, file in enumerate(backup_files):
            os.makedirs(os.path.dirname(data_files[index]), exist_ok=True)
            if verbose:
                print(f"Copying {file} to {data_files[index]}")
            shutil.copy2(file, data_files[index])

    def _get_backups(self):
        """ Set the manager's backup-dictionary based on backup directory contents.

        Raises:
            HedFileError - if a backup is inconsistent for any reason.
        """
        backups = {}
        for backup in os.listdir(self.backups_root):
            backup_root = os.path.realpath(os.path.join(self.backups_root, backup))
            if not os.path.isdir(backup_root):
                raise HedFileError('BadBackupPath', f"{backup_root} is not a backup directory.", "")
            if len(os.listdir(backup_root)) != 2:
                raise HedFileError("BadBackFormat",
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

        Args:
            backup_name (str): Name of the backup.

        Returns:
            dict:  dictionary containing the backup info.
            list:  Files in backup directory that are not in the backup dict.
            list:  Files in backup dictionary not in backup directory

        Notes:
            If file_path is None, this checks against consistency in the backup dictionary.

        """

        backup_dict_path = os.path.realpath(os.path.join(self.backups_root, backup_name, self.BACKUP_DICTIONARY))
        if not os.path.exists(backup_dict_path):
            raise HedFileError("BadBackupDictionary",
                               f"Backup dictionary for {backup_name} does not exist so backup invalid", "")
        backup_root_path = os.path.realpath(os.path.join(self.backups_root, backup_name, self.BACKUP_ROOT))
        if not os.path.isdir(backup_root_path):
            raise HedFileError("BadBackupDictionary",
                               f"Backup dictionary for {backup_name} does not exist so backup invalid", "")
        with open(backup_dict_path, 'r') as fp:
            backup_dict = json.load(fp)
        backup_paths = set([os.path.realpath(os.path.join(backup_root_path, backup_key))
                            for backup_key in backup_dict.keys()])
        file_paths = set(get_file_list(backup_root_path))
        files_not_in_backup = list(file_paths.difference(backup_paths))
        backups_not_in_directory = list(backup_paths.difference(file_paths))
        return backup_dict, files_not_in_backup, backups_not_in_directory