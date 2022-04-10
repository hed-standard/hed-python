"""Utilities for generating and handling file names."""

import os
from werkzeug.utils import secure_filename
from hed.errors import HedFileError


def check_filename(test_file, name_prefix=None, name_suffix=None, extensions=None):
    """ Determines whether test_file has correct extension, name_suffix, and name_prefix.

    Everything is converted to lower case prior to testing so this test should be case insensitive.

     Args:
         test_file (str) :           Path of filename to test
         name_prefix (str):          An optional name_prefix for the base filename
         name_suffix (str):          An optional name_suffix for the base file name
         extensions (list):     An optional list of file extensions

     Returns:
         tuple (list, list):            Returns two lists one with
     """

    file_split = os.path.splitext(test_file.lower())
    is_name = True
    if extensions and file_split[1] not in [x.lower() for x in extensions]:
        is_name = False
    elif name_suffix and not file_split[0].endswith(name_suffix.lower()):
        is_name = False
    elif name_prefix and not file_split[0].startswith(name_prefix.lower()):
        is_name = False
    return is_name


def extract_suffix_path(path, prefix_path):
    """ Return the suffix path of path after prefix path has been removed

    Args:
        path (str)   path of the root directory
        prefix_path (str)    sub-path relative to the root directory

    Returns: (str)
        Suffix path.

    Notes: This function is useful for creating files within BIDS datasets

    """

    real_prefix = os.path.realpath(prefix_path).lower()
    suffix_path = os.path.realpath(path).lower()
    return_path = os.path.realpath(path)
    if suffix_path.startswith(real_prefix):
        return_path = return_path[len(real_prefix):]
    return return_path


def generate_filename(base_name, name_prefix=None, name_suffix=None, extension=None):
    """Generates a filename for the attachment of the form prefix_basename_suffix + extension.

    Parameters
    ----------
   base_name: str
        The name of the base, usually the name of the file that the issues were generated from
    name_prefix: str
        The name_prefix prepended to the front of the base_name
    name_suffix: str
        The name_suffix appended to the end of the base_name
    Returns
    -------
    string
        The name of the attachment other containing the issues.
    """

    pieces = []
    if name_prefix:
        pieces = pieces + [name_prefix]
    if base_name:
        pieces.append(os.path.splitext(base_name)[0])
    if name_suffix:
        pieces = pieces + [name_suffix]

    if not pieces:
        return ''
    filename = pieces[0]
    for name in pieces[1:]:
        filename = filename + name
    if extension:
        filename = filename + extension
    return secure_filename(filename)


def get_dir_dictionary(dir_path, name_prefix=None, name_suffix=None, extensions=None, skip_empty=True):
    """ Traverses a directory tree and creates dictionary with keys that are directory paths a.

    Args:
        dir_path (str):               Full path of the directory tree to be traversed (no ending slash)
        name_prefix (str, None):      An optional name_prefix for the base filename
        name_suffix (str, None):      An optional name_suffix for the base file name
        extensions (list, None):      An optional list of file extensions
        skip_empty (bool):            Do not put entry for directories that have no files

    Returns:
        dict:             Dictionary with directories and keys and file lists values
    """
    dir_dict = {}
    for root, dirs, files in os.walk(dir_path, topdown=True):
        file_list = []
        for r_file in files:
            if check_filename(r_file, name_prefix, name_suffix, extensions):
                file_list.append(os.path.join(os.path.realpath(root), r_file))
        if skip_empty and not file_list:
            continue
        dir_dict[os.path.realpath(root)] = file_list
    return dir_dict


def get_filtered_list(file_list, name_prefix=None, name_suffix=None, extensions=None):
    """ Returns a new list with the filenames in file_list satisfying the criteria

    Everything is converted to lower case prior to testing so this test should be case insensitive.

     Args:
         file_list (list):           List of files to test
         name_prefix (str):          An optional name_prefix for the base filename
         name_suffix (str):          An optional name_suffix for the base filename
         extensions (list):     An optional list of file extensions

     Returns:
         tuple (list, list):            Returns two lists one with
     """
    filtered_files = []
    for r_file in file_list:
        file_split = os.path.splitext(r_file.lower())
        if extensions and file_split[1] not in [x.lower() for x in extensions]:
            continue
        elif name_suffix and not file_split[0].endswith(name_suffix.lower()):
            continue
        elif name_prefix and not file_split[0].startswith(name_prefix.lower()):
            continue
        filtered_files.append(r_file)
    return filtered_files


def get_file_list(root_path, name_prefix=None, name_suffix=None, extensions=None, exclude_dirs=[]):
    """ Traverses a directory tree and returns a list of paths to files ending with a particular name_suffix.

    Args:
        root_path (str):              Full path of the directory tree to be traversed (no ending slash)
        name_prefix (str, None):     An optional name_prefix for the base filename
        name_suffix (str, None):     The name_suffix of the paths to be extracted
        extensions (list, None):     A list of extensions to be selected
        exclude_dirs (list, None):    A list of paths to be excluded

    Returns:
        list:             A list of full paths
    """
    file_list = []
    for root, dirs, files in os.walk(root_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for r_file in files:
            if check_filename(r_file, name_prefix, name_suffix, extensions):
                file_list.append(os.path.join(os.path.realpath(root), r_file))
    return file_list


def get_path_components(this_path, root_path):
    """ Return a list with root_path and remaining components

    this_path must be a descendant of root_path

    Args:
        this_path (str):      The path of a file or directory descendant of root_path
        root_path (str):      A path (no trailing separator)

    Returns:
        list or None:         A list with the first element being root_path and the
                              remaining elements directory components to the file.
    """

    base_path = os.path.realpath(root_path)
    cur_path = os.path.realpath(this_path)
    common_path = os.path.commonpath([base_path, cur_path])
    if common_path != base_path:
        return None
    rel_path = os.path.relpath(cur_path, base_path)
    the_dir = os.path.dirname(rel_path)
    if the_dir:
        return [base_path] + os.path.normpath(the_dir).split(os.sep)
    else:
        return [base_path]


def make_path(root_path, sub_path, filename):
    """ Return the complete path for a file, making sure all path components exist.

    Args:
        root_path (str)   path of the root directory
        sub_path (str)    sub-path relative to the root directory
        filename (str)    filename of the file

    Returns: (str)
        A valid realpath for the specified file.

    Notes: This function is useful for creating files within BIDS datasets

    """

    dir_path = os.path.realpath(os.path.join(root_path, sub_path))
    os.makedirs(dir_path, exist_ok=True)
    return os.path.realpath(os.path.join(dir_path, filename))


def parse_bids_filename(file_path):
    """ Split a filename into its BIDS suffix, extension, and entity_dict

        Args:
            file_path (str)     Path to be parsed

        Returns: dict
            suffix (str)        BIDS suffix name
            ext (str)           File extension (including the .)
            entity_dict (dict)  Dictionary with key-value pair being (entity type, entity value)

        Raises HedFileError when filename does not conform to name-value_suffix format.

    """

    filename = os.path.splitext(os.path.basename(file_path))
    ext = filename[1].lower()
    basename = filename[0].strip()
    entity_dict = {}

    if len(basename) == 0:
        raise HedFileError("BlankFileName", f"The basename for {file_path} is blank", "")
    entity_pieces = basename.split('_')
    split_dict = _split_entity(entity_pieces[-1])
    if "bad" in split_dict:
        raise HedFileError("BadSuffixPiece", f"The basename for {entity_pieces[-1]} has bad {ent_dict['bad']}", "")
    if "suffix" in split_dict:
        suffix = split_dict["suffix"]
    else:
        suffix = None
        entity_dict[split_dict["key"]] = split_dict["value"]
    for pos, entity in reversed(list(enumerate(entity_pieces[:-1]))):
        split_dict = _split_entity(entity)
        if "key" not in split_dict:
            raise HedFileError("BadKeyValue", f"The piece {entity} is not in key-value form", "")
        entity_dict[split_dict["key"]] = split_dict["value"]
    return suffix, ext, entity_dict


def _split_entity(piece):
    """Splits an piece into an entity or suffix

        Returns: dict
    """
    piece = piece.strip()
    if not piece:
        return {"bad": ""}
    split_piece = piece.split('-')
    if len(split_piece) == 1:
        return {"suffix": piece}
    if len(split_piece) == 2:
        return {"key": split_piece[0].strip(), "value": split_piece[1].strip()}
    else:
        return {"bad": piece}
