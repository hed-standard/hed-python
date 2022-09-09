
import os
import json


class HedLogger:
    """ Log status messages organized by key. """
    def __init__(self, name=""):
        self.log = {}
        self.name = name

    def add(self, key, msg, level="", also_print=False):
        if key not in self.log:
            self.log[key] = []
        self.log[key].append({"key": key, "msg": msg, "level": level})
        if also_print:
            print(f"{key} [{level}]: {msg}")

    def get_log(self, key):
        if key in self.log:
            return self.log[key]
        else:
            return []

    def get_log_keys(self):
        return list(self.log.keys())

    def get_log_string(self, level=None):
        """ Return the log as a string, with entries separated by newlines. """
        log_lines = [f"{self.name}: Level {str(level)}"]
        for key, item in self.log.items():
            log_lines.append(f"{key}:")
            if item:
                for entry in item:
                    if not level or (entry["level"] == level):
                        log_lines.append(f"\t[{entry['level']} {entry['msg']}]")
        return "\n".join(log_lines)

    def load_log(self, root_path, sub_path='code', log_name='hed_log.json'):
        filename = os.path.realpath(os.path.join(os.path.join(root_path, sub_path), log_name))
        if os.path.isfile(filename):
            with open(filename, "r") as fp:
                self.log = json.load(fp)
        else:
            self.log = {}

    def print_log(self, level=None):
        for key, item in self.log.items():
            print(f"{key}:")
            if item:
                for entry in item:
                    if not level or (entry["level"] == level):
                        print(f"\t[{entry['level']} {entry['msg']}]")

    def save_log(self, save_path, log_name="hed_log.json"):
        os.makedirs(os.path.realpath(save_path), exist_ok=True)
        path_name = os.path.join(save_path, log_name)
        log_string = json.dumps(self.log, indent=4)
        with open(path_name, "w") as fp:
            fp.write(log_string)
