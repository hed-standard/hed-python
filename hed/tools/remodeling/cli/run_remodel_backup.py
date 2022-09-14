import argparse
import os
import shutil
from hed.tools.util.io_util import get_file_list, extract_suffix_path


def get_parser():
    parser = argparse.ArgumentParser(description="Converts event files based on a json file specifying operations.")
    parser.add_argument("data_dir", help="Full path of dataset root directory.")
    parser.add_argument("-x", "--exclude-dirs", nargs="*", default=[], dest="exclude_dirs",
                        help="Directories names to exclude from search for files." +
                             "Note data_dir/remodel/backup will always be excluded.")
    parser.add_argument("-f", "--file-suffix", dest="file_suffix", default='events',
                        help="Filename suffix of files to be backed up.")
    parser.add_argument("-e", "--extensions", nargs="*", default=['.tsv'], dest="extensions",
                        help="File extensions to allow in locating files.")
    parser.add_argument("-w", "--write-over-backup", action='store_true',
                        help="If present then overwrite existing backup files.")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="If present, output informative messages as computation progresses.")
    return parser


def backup_files(args):
    verbose = hasattr(args, 'verbose')
    exclude_dirs = args.exclude_dirs.append('remodel')
    backup_path = os.path.realpath(os.path.join(args.data_dir, 'derivatives/remodel/backup'))
    os.makedirs(backup_path, exist_ok=True)
    file_list = get_file_list(args.data_dir, name_suffix=args.file_suffix, extensions=args.extensions,
                              exclude_dirs=exclude_dirs)
    if verbose:
        print(f"Data directory: {args.data_dir}\nBackup path: {backup_path}")
        print(f"Processing {len(file_list)} files with suffix {args.file_suffix} "
              f"and extensions {str(args.extensions)}")
    for orig_file in file_list:
        backup_base = extract_suffix_path(orig_file, args.data_dir)
        backup_file = os.path.realpath(backup_path + backup_base)
        if verbose:
            print(f"Original file: {orig_file}\nBackup file: {backup_file}")
        os.makedirs(os.path.dirname(backup_file), exist_ok=True)
        shutil.copy2(orig_file, backup_file)


def main():
    parser = get_parser()
    args = parser.parse_args()
    backup_files(args)


if __name__ == '__main__':
    main()
