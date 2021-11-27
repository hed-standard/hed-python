import os

def get_dir_dictionary(path, prefix=None, types=None, suffix=None):
    """ Traverses a directory tree and dictionary with keys that are directories.

    Args:
        path (str):       The full path of the directory tree to be traversed (no ending slash)
        prefix (str):     An optional prefix for the base filename
        types (list):     A list of extensions to be selected
        suffix (str):     The suffix of the paths to be extracted

    Returns:
        list:             A list of full paths
    """
    file_list = []
    for r, d, f in os.walk(path):
        for r_file in f:
            file_split = os.path.splitext(r_file)
            if types and file_split[1] not in types:
                continue
            elif suffix and not file_split[0].endswith(suffix):
                continue
            elif prefix and not file_split[0].startswith(prefix):
                continue
            file_list.append(os.path.join(r, r_file))
    return file_list

class BIDSFiles:
    """Represents the files of a BIDS dataset."""

    def __init__(self, root_path):
        self.dataset_description = ''
