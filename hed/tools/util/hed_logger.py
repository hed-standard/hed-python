""" Logger class with messages organized by key """


class HedLogger:
    """ Log status messages organized by key. """
    def __init__(self, name=None):
        """ Constructor for the HED logger.

        Parameters:
            name (str): Identifying name of the logger.

        """
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
        """ Return the log as a string, with entries separated by newlines.

        Parameters:
            level (str or None): Include only the entries from this level. If None, do all.

        Returns:
            str: The log as a string separated by newlines.

        """

        log_lines = [f"Name:{str(self.name)} Level:{str(level)}"]
        for key, item in self.log.items():
            log_lines.append(f"{key}:")
            if item:
                for entry in item:
                    if not level or (entry["level"] == level):
                        log_lines.append(f"\t[{entry['level']} {entry['msg']}]")
        return "\n".join(log_lines)
