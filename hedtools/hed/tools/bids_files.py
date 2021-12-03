import os
from hed.tools.io_utils import get_dir_dictionary, get_file_list, get_path_components
from hed.tools.bids_file import BIDSFile


class BIDSFiles:
    """Represents the event files and their sidecars in a BIDS dataset."""

    def __init__(self, root_path, suffix='events', extensions=['.tsv']):
        self.root_path = root_path
        self.suffix = suffix
        self.dataset_description = ''
        self.json_files = self.get_file_dict()
        self.data_files = self.get_file_dict(extensions=extensions)
        self.set_sidecars()

    def get_file_dict(self, extensions=['.json']):
        files = get_file_list(self.root_path, name_suffix='_'+self.suffix, extensions=extensions)
        file_dict = {}
        for file in files:
            file_dict[os.path.abspath(file)] = BIDSFile(file)
        return file_dict

    def get_sidecar(self, file, sidecars):
        if not sidecars:
            return None
        bids_file = self.data_files[file]
        for sidecar in sidecars:
            sidecar_obj = self.json_files[sidecar]
            if sidecar_obj.is_parent(bids_file):
                return sidecar
        return None

    def set_sidecars(self):
        dir_dict = get_dir_dictionary(self.root_path, name_suffix=self.suffix, extensions=['.json'], skip_empty=True)
        for file, obj in self.data_files.items():
            sidecar_list = []
            current_path = ''
            for comp in get_path_components(file, self.root_path):
                current_path = os.path.abspath(os.path.join(current_path, comp))
                sidecars = dir_dict.get(current_path, None)
                sidecar = self.get_sidecar(file, sidecars)
                if sidecar:
                    sidecar_list.append(sidecar)
            obj.set_sidecars(sidecar_list)


if __name__ == '__main__':
    path = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s'
    bids = BIDSFiles(path)
    for this_file, file_obj in bids.json_files.items():
        print(file_obj)

    for this_file, file_obj in bids.data_files.items():
        print(file_obj)
