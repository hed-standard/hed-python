
class HedLogger:

    def __init__(self):
        self.status = {}

    def add(self, key, msg, also_print=False):
        if key not in self.status:
            self.status[key] = []
        self.status[key].append(msg)
        if also_print:
            print(msg)

    def print_log(self, filename=None):
        for key, status_item in self.status.items():
            print(f"{key}")
            if status_item:
                for msg in status_item:
                    print(f"\t{msg}")
