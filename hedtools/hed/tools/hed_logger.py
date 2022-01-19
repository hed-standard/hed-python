
""" HedLogger class. """


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
            print(msg)

    def get_log_keys(self):
        return list(self.log.keys())

    def get_log(self, key):
        if key in self.log:
            return self.log[key]
        else:
            return []

    def print_log(self, filename=None):
        for key, item in self.log.items():
            print(f"{key}")
            if item:
                for msg in item:
                    print(f"\t{msg}")
