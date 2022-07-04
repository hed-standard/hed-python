from hed.errors import HedFileError
from hed.schema import load_schema_version


class ConditionVariable:
    def __init__(self, name):
        self.name = name
        self.levels = {}
        self.direct = []

    def __str__(self):
        return f"{self.name}:{self.levels} levels {len(self.direct)} references"


class ConditionManager:

    def __init__(self, onset_manager, definitions):
        """ Create a condition manager for an events file.

        Args:
            onset_manager (OnsetManager): An onset manager for the conditions.
            definitions (dict): A dictionary of DefinitionEntrys

        """

        self.manager = onset_manager
        self.definitions = definitions
        self.condition_variables = {}


if __name__ == '__main__':
    schema = load_schema_version(xml_version="8.1.0")
