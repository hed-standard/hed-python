import os
from werkzeug.utils import secure_filename


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
        pieces = pieces + [secure_filename(name_prefix)]
    if base_name:
        pieces.append(os.path.splitext(secure_filename(base_name))[0])
    if name_suffix:
        pieces = pieces + [secure_filename(name_suffix)]

    if not pieces:
        return ''
    filename = pieces[0]
    for name in pieces[1:]:
        filename = filename + '_' + name
    if extension:
        filename = filename + '.' + secure_filename(extension)
    return filename


def get_dir_dictionary(dir_path, name_prefix=None, name_suffix=None, extensions=None, skip_empty=True):
    """ Traverses a directory tree and dictionary with keys that are directories.

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
    for r, d, f in os.walk(dir_path):
        file_list = []
        for r_file in f:
            if test_filename(r_file, name_prefix, name_suffix, extensions):
                file_list.append(os.path.abspath(os.path.join(r, r_file)))
        if skip_empty and not file_list:
            continue
        dir_dict[os.path.abspath(r)] = file_list
    return dir_dict


def get_file_list(dir_path, name_prefix=None, name_suffix=None, extensions=None):
    """ Traverses a directory tree and returns a list of paths to files ending with a particular name_suffix.

    Args:
        dir_path (str):              Full path of the directory tree to be traversed (no ending slash)
        name_prefix (str, None):     An optional name_prefix for the base filename
        name_suffix (str, None):     The name_suffix of the paths to be extracted
        extensions (list, None):     A list of extensions to be selected

    Returns:
        list:             A list of full paths
    """
    file_list = []
    for r, d, f in os.walk(dir_path):
        for r_file in f:
            if test_filename(r_file, name_prefix, name_suffix, extensions):
                file_list.append(os.path.join(r, r_file))
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

    base_path = os.path.abspath(root_path)
    cur_path = os.path.abspath(this_path)
    common_path = os.path.commonpath([base_path, cur_path])
    if common_path != base_path:
        return None
    rel_path = os.path.relpath(cur_path, base_path)
    the_dir = os.path.dirname(rel_path)
    if the_dir:
        return [base_path] + os.path.normpath(the_dir).split(os.sep)
    else:
        return [base_path]


def make_file_dict(file_list, indices=(0, -2), separator='_'):
    """ Return a dictionary with keys that are simplified file names and values that are full paths

    This function is used for cross listing BIDS style files for different studies.

    Args:
        file_list (list):      List containing full paths of files of interest
        indices (tuple):       List of indices into base file names of pieces to assemble for the key
        separator (str):       Character used to separate pieces of key name
    Returns:
        dict:  A dictionary of simplified, path-independent key names and full paths values.
    """
    file_dict = {}
    for the_file in file_list:
        the_file = os.path.abspath(the_file)
        base = os.path.basename(the_file)
        key = make_key(base, indices=indices, separator=separator)
        file_dict[key] = the_file
    return file_dict


def make_key(key_string, indices=(0, -2), separator='_'):
    key_value = ''
    pieces = key_string.split(separator)
    for index in list(indices):
        key_value += pieces[index] + separator
    return key_value[:-1]


def parse_bids_filename(file_path):
    filename = os.path.splitext(os.path.basename(file_path))
    ext = filename[1]
    basename = filename[0]
    entity_pieces = basename.split('_')
    suffix = entity_pieces[-1]
    entity_dict = {}
    entity_pieces = entity_pieces[:-1]
    for entity in entity_pieces:
        pieces = entity.split('-')
        entity_dict[pieces[0]] = pieces[1]
    return suffix, ext, entity_dict


def test_filename(test_file, name_prefix=None, name_suffix=None, extensions=None):
    """ Determines whether test_file has correct extension, name_suffix, and name_prefix.

     Args:
         test_file (str) :           Path of filename to test
         name_prefix (str):          An optional name_prefix for the base filename
         name_suffix (str):          An optional name_suffix for the base file name
         extensions (list):     An optional list of file extensions

     Returns:
         tuple (list, list):            Returns two lists one with
     """

    file_split = os.path.splitext(test_file)
    is_name = True
    if extensions and file_split[1] not in extensions:
        is_name = False
    elif name_suffix and not file_split[0].endswith(name_suffix):
        is_name = False
    elif name_prefix and not file_split[0].startswith(name_prefix):
        is_name = False
    return is_name


if __name__ == '__main__':
    path = 'D:\\Research\\HED\\hed-examples\\datasets\\eeg_ds003654s'
    files = get_file_list(path, name_prefix=None, name_suffix="events", extensions=None)
    for file in files:
        get_path_components(file, path)
