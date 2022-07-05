from hed.errors import HedFileError
from hed.schema import load_schema_version
from hed.models import HedString, HedTag, HedGroup, DefinitionEntry
from hed.tools.analysis.onset_manager import OnsetManager


class ConditionVariable:
    def __init__(self, name):
        self.name = name
        self.levels = {}
        self.direct = []

    def __str__(self):
        return f"{self.name}:{self.levels} levels {len(self.direct)} references"


class DefinitionManager:

    def __init__(self, hed_strings, hed_schema, definitions):
        """ Create a condition manager for an events file.

        Args:
            onset_manager (OnsetManager): An Onset manager
            definitions (dict): A dictionary of DefinitionEntry objects

        """

        onset_manager = OnsetManager(hed_strings, hed_schema)
        self.hed_strings = onset_manager.hed_strings
        self.event_contexts = onset_manager.event_contexts
        self.hed_schema = hed_schema
        self.definitions = definitions
        self.condition_variables = {}
        self.def_groups = []
        self._extract_def_groups()

    def _extract_def_groups(self):
        """ This removes any def """
        def_groups = [0] * len(self.hed_strings)
        for i in range(len(self.hed_strings)):
            def_groups[i] = []
        for i, hed in enumerate(self.hed_strings):
            def_groups[i] = self._extract_event_defs(hed)
        self.def_groups = def_groups

    @staticmethod
    def _extract_event_defs(hed):
        to_remove = []
        to_append = []
        tups = hed.find_def_tags(recursive=True, include_groups=3)
        for tup in tups:
            if len(tup[2].children) == 1:
                to_append.append(tup[0])
            else:
                to_append.append(tup[2])
            to_remove.append(tup[2])
        hed.remove(to_remove)
        return to_append


if __name__ == '__main__':
    schema = load_schema_version(xml_version="8.1.0")
    test_strings1 = [HedString('Sensory-event,(Def/Cond1,(Red, Blue),Onset),(Def/Cond2,Onset),Green,Yellow',
                               hed_schema=schema),
                     HedString('(Def/Cond1, Offset)', hed_schema=schema),
                     HedString('White, Black', hed_schema=schema),
                     HedString('', hed_schema=schema),
                     HedString('(Def/Cond2, Onset)', hed_schema=schema),
                     HedString('(Def/Cond3/4.3, Onset)', hed_schema=schema),
                     HedString('Arm, Leg', hed_schema=schema)]

    onset_man = OnsetManager(test_strings1, schema)
    def1 = HedGroup('(Definition/Cond1, (Condition-variable/Var1, Circle, Square))')
    def2 = HedGroup('(Definition/Cond2, (Condition-variable/Var2, Triangle, Sphere))')
    def3 = HedGroup('(Definition/Cond3/#, (Condition-variable/Var3, Physical-length/#, Ellipse, Cross))')
    defs = {'Cond1', DefinitionEntry('Cond1', def1, False, None),
            'Cond2', DefinitionEntry('Cond2', def2, False, None),
            'Cond3', DefinitionEntry('Cond3', def3, True, None)}

    conditions = ConditionManager(test_strings1, schema, defs)
    print("to Here")