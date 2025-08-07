"""Utilities for generating and handling file names. """

import os
import re
from datetime import datetime

TIME_FORMAT = '%Y_%m_%d_T_%H_%M_%S_%f'


def check_filename(test_file, name_prefix=None, name_suffix=None, extensions=None):
    """ Return True if correct extension, suffix, and prefix.

    Parameters:
        test_file (str):  Path of filename to test.
        name_prefix (list, str, None):  An optional name_prefix or list of prefixes to accept for the base filename.
        name_suffix (list, str, None):  An optional name_suffix or list of suffixes to accept for the base file name.
        extensions (list, str, None):   An optional extension or list of extensions to accept for the extensions.

    Returns:
        bool: True if file has the appropriate format.

    Notes:
        - Everything is converted to lower case prior to testing so this test should be case-insensitive.
        - None indicates that all are accepted.


    """
    basename = os.path.basename(test_file.lower())
    if name_prefix and not get_allowed(basename, allowed_values=name_prefix, starts_with=True):
        return False
    if extensions:
        ext = get_allowed(basename, allowed_values=extensions, starts_with=False)
        if not ext:
            return False
        basename = basename[:-len(ext)]
    else:
        basename = os.path.splitext(basename)[0]
    if name_suffix and not get_allowed(basename, allowed_values=name_suffix, starts_with=False):
        return False
    return True


def get_allowed(value, allowed_values=None, starts_with=True):
    """ Return the portion of the value that matches a value in allowed_values or None if no match.

    Parameters:
        value (str): value to be matched.
        allowed_values (list, str, or None):  Values to match.
        starts_with (bool):  If True match is done at beginning of string, otherwise the end.

    Returns:
        Union[str,list]:  portion of value that matches the various allowed_values.

    Notes:
        - match is done in lower case.

    """
    if not allowed_values:
        return value
    elif not isinstance(allowed_values, list):
        allowed_values = [allowed_values]
    allowed_values = [item.lower() for item in allowed_values]
    lower_value = value.lower()
    if starts_with:
        result = list(filter(lower_value.startswith, allowed_values))
    else:
        result = list(filter(lower_value.endswith, allowed_values))
    if result:
        result = result[0]
    return result


def get_alphanumeric_path(pathname, replace_char='_'):
    """ Replace sequences of non-alphanumeric characters in string (usually a path) with specified character.

        Parameters:
            pathname (str): A string usually representing a pathname, but could be any string.
            replace_char (str): Replacement character(s).

        Returns:
            str: New string with characters replaced.

    """
    return re.sub(r'[^a-zA-Z0-9]+', replace_char, pathname)


def get_full_extension(filename):
    """ Return the full extension of a file, including the period.

    Parameters:
        filename (str):   The filename to be parsed.

    Returns:
        Tuple[str, str]:
        - File name without extension
        - Full extension

    """
    name, ext = os.path.splitext(filename)
    full_ext = ext
    while ext: # Keep splitting if there's another extension
        name, ext = os.path.splitext(name)
        if not ext:
            break
        full_ext = ext + full_ext
    return name, full_ext


def get_unique_suffixes(file_paths, extensions=['.json', '.tsv']):
    suffixes = set()
    extension_set = set(extensions)
    for file_path in file_paths:
        name, ext = get_full_extension(file_path)
        if ext not in extension_set:
            continue

        result = os.path.basename(name).split('_')
        if len(result) == 2:
            suffixes.add(result[1])
    return suffixes


def extract_suffix_path(path, prefix_path):
    """ Return the suffix of path after prefix path has been removed.

    Parameters:
        path (str)           path of the root directory.
        prefix_path (str)    sub-path relative to the root directory.

    Returns:
        str:   Suffix path.

    Notes:
        - This function is useful for creating files within BIDS datasets.

    """

    real_prefix = os.path.normpath(os.path.realpath(prefix_path).lower())
    suffix_path = os.path.normpath(os.path.realpath(path).lower())
    return_path = os.path.normpath(os.path.realpath(path))
    if suffix_path.startswith(real_prefix):
        return_path = return_path[len(real_prefix):]
    return return_path


def clean_filename(filename):
    """ Replace invalid characters with under-bars.

    Parameters:
        filename (str):   source filename.

    Returns:
        str:  The filename with anything but alphanumeric, period, hyphens, and under-bars removed.
    """
    if not filename:
        return ""
    out_name = re.sub(r'[^a-zA-Z0-9._-]+', '_', filename)
    return out_name


def get_basename(file_path):
    return get_full_extension(file_path)[0]


def get_filtered_by_element(file_list, elements):
    """ Filter a file list by whether the base names have a substring matching any of the members of elements.

    Parameters:
        file_list (list):  List of file paths to be filtered.
        elements (list):  List of strings to use as filename filters.

    Returns:
        list:  The list only containing file paths whose filenames match a filter.

    """
    new_list = [file for file in file_list if any(substring in os.path.basename(file) for substring in elements)]
    return new_list


def get_filtered_list(file_list, name_prefix=None, name_suffix=None, extensions=None):
    """ Get list of filenames satisfying the criteria.

    Everything is converted to lower case prior to testing so this test should be case-insensitive.

    Parameters:
        file_list (list):      List of files to test.
        name_prefix (str):     Optional name_prefix for the base filename.
        name_suffix (str):     Optional name_suffix for the base filename.
        extensions (list):     Optional list of file extensions (allows two periods (.tsv.gz)).

     Returns:
         list:  The filtered file names.

     """
    filtered_files = [file for file in file_list if
                      check_filename(file, name_prefix=name_prefix, name_suffix=name_suffix, extensions=extensions)]
    return filtered_files


def get_file_list(root_path, name_prefix=None, name_suffix=None, extensions=None, exclude_dirs=None):
    """ Return paths satisfying various conditions.

    Parameters:
        root_path (str):              Full path of the directory tree to be traversed (no ending slash).
        name_prefix (list, str, None):      An optional prefix for the base filename.
        name_suffix (list, str, None):  An optional suffix for the base filename.
        extensions (list, None):      A list of extensions to be selected.
        exclude_dirs (list, None):    A list of paths to be excluded.

    Returns:
        list:   The full paths.

    Notes: Exclude directories are paths relative to the root path.

    """
    file_list = []
    if not exclude_dirs:
        exclude_dirs = []
    for root, dirs, files in os.walk(root_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for r_file in files:
            if check_filename(r_file, name_prefix, name_suffix, extensions):
                file_list.append(os.path.realpath(os.path.join(root, r_file)))
    return file_list


def get_path_components(root_path, this_path):
    """ Get a list of the remaining components after root path.

    Parameters:
        root_path (str):      A path (no trailing separator).
        this_path (str):      The path of a file or directory descendant of root_path.

    Returns:
        Union[list, None]:   A list with the remaining elements directory components to the file.

    Notes: this_path must be a descendant of root_path.

    """

    base_path = os.path.normpath(os.path.realpath(root_path))
    cur_path = os.path.normpath(os.path.realpath(this_path))
    common_prefix = os.path.commonprefix([base_path, cur_path])
    if not common_prefix:
        raise ValueError("NoPathInCommon", f"Paths {base_path} and {cur_path} must have items in common")
    common_path = os.path.commonpath([base_path, cur_path])
    if common_path != base_path:
        return None
    rel_path = os.path.relpath(cur_path, base_path)
    the_dir = os.path.dirname(rel_path)
    if the_dir:
        return os.path.normpath(the_dir).split(os.sep)
    else:
        return []


def get_timestamp():
    """ Return a timestamp string suitable for using in filenames.

    Returns:
        str:  Represents the current time.

    """
    now = datetime.now()
    return now.strftime(TIME_FORMAT)[:-3]


def make_path(root_path, sub_path, filename):
    """ Get path for a file, verifying all components exist.

    Parameters:
        root_path (str):   path of the root directory.
        sub_path (str):    sub-path relative to the root directory.
        filename (str):    filename of the file.

    Returns:
        str: A valid realpath for the specified file.

    Notes: This function is useful for creating files within BIDS datasets.

    """

    dir_path = os.path.realpath(os.path.join(root_path, sub_path))
    os.makedirs(dir_path, exist_ok=True)


def get_task_from_file(file_path):
    """ Returns the task name entity from a BIDS-type file path.

    Parameters:
        file_path (str):  File path.

    Returns:
        str:  The task name or an empty string.

    """
    filename = os.path.splitext(os.path.basename(file_path))
    basename = filename[0].strip()
    position = basename.lower().find("task-")
    if position == -1:
        return ""
    splits = re.split(r'[_.]', basename[position+5:])
    return splits[0]


def get_task_dict(files):
    """ Return a dictionary of the tasks that appear in the file names of a list of files.

    Parameters:
        files (list): List of filenames to be separated by task.

    Returns:
        dict:  dictionary of filenames keyed by task name.

    """
    task_dict = {}
    for my_file in files:
        task = get_task_from_file(my_file)
        if not task:
            continue
        task_entry = task_dict.get(task, [])
        task_entry.append(my_file)
        task_dict[task] = task_entry
    return task_dict


def separate_by_ext(file_paths):
    """ Separate a list of files into tsv and json files.

    Parameters:
        file_paths (list):  A list of file paths.

    Returns:
        dict:  key is extension and value is list of files with that extension.

    """
    ext_dict = {}
    for file_path in file_paths:
        basename, ext = get_full_extension(file_path)
        if ext not in ext_dict:
            ext_dict[ext] = [file_path]
        else:
            ext_dict[ext].append(file_path)
    return ext_dict
