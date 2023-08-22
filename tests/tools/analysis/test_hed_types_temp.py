import os
import unittest
from pandas import DataFrame
from hed.errors.exceptions import HedFileError
from hed.models import DefinitionDict
from hed.models.hed_string import HedString
from hed.models.hed_tag import HedTag
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.event_manager import EventManager
from hed.tools.analysis.hed_types import HedTypes
from hed.models.df_util import get_assembled


class Test(unittest.TestCase):

    def test_1(self):
        schema = load_schema_version(xml_version="8.1.0")
        # Set up the definition dictionary
        defs = [HedString('(Definition/Cond1, (Condition-variable/Var1, Circle, Square))', hed_schema=schema),
                HedString('(Definition/Cond2, (condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere))', 
                          hed_schema=schema),
                HedString('(Definition/Cond3, (Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross))',
                          hed_schema=schema),
                HedString('(Definition/Cond4, (Condition-variable, Apple, Banana))', hed_schema=schema),
                HedString('(Definition/Cond5, (Condition-variable/Lumber, Apple, Banana))', hed_schema=schema),
                HedString('(Definition/Cond6/#, (Condition-variable/Lumber, Label/#, Apple, Banana))', 
                          hed_schema=schema)]
        def_dict = DefinitionDict()
        for value in defs:
            def_dict.check_for_definitions(value)

        test_strings1 = ["Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset)",
                         "(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4",
                         "(Def/Cond1, Offset)",
                         "White, Black, Condition-variable/Wonder, Condition-variable/Fast",
                         "",
                         "(Def/Cond2, Onset)",
                         "(Def/Cond3/4.3, Onset)",
                         "Arm, Leg, Condition-variable/Fast"]
        test_onsets1 = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        df1 = DataFrame(test_onsets1, columns=['onset'])
        df1['HED'] = test_strings1
        input_data = TabularInput(df1)
        defs = input_data.get_def_dict(schema,extra_def_dicts=def_dict)
        self.assertIsInstance(input_data, TabularInput)
        print(defs)
 

if __name__ == '__main__':
    unittest.main()
