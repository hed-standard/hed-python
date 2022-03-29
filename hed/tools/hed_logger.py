
""" HedLogger class. """

import os
import json



class HedLogger:
    """ Class to log status messages organized by key

    """
    def __init__(self):
        self.log = {}

    def add(self, key, msg, also_print=False):
        if key not in self.log:
            self.log[key] = []
        self.log[key].append(msg)
        if also_print:
            print(f"{key}: {msg}")

    def get_log_keys(self):
        return list(self.log.keys())

    def get_log(self, key):
        if key in self.log:
            return self.log[key]
        else:
            return []

    def load_log(self, root_path, sub_path='code', log_name='hed_log.json'):
        filename = os.path.realpath(os.path.join(os.path.join(root_path, sub_path)), log_name)
        if os.path.isfile(filename):
            with open(filename, "r") as fp:
                self.log = json.load(fp)
        else:
            self.log = {}

    def print_log(self):
        for key, item in self.log.items():
            print(f"{key}")
            if item:
                for msg in item:
                    print(f"\t{msg}")

    def save_log(self, root_path, sub_path='code', log_name='hed_log.json'):
        path_name = make_path(root_path, sub_path, log_name)
        log_string = json.dumps(self.log, indent=4)
        with open(path_name, "w") as fp:
            fp.write(log_string)
