import unittest
import os
import io
import shutil

from hed.errors import HedFileError, ValidationErrors
from hed.models import ColumnMetadata, HedString, Sidecar
from hed.validator import HedValidator
from hed import schema
from hed.models import DefinitionDict
from hed.errors import ErrorHandler
from hed.validator.sidecar_validator import SidecarValidator


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        cls.base_data_dir = base_data_dir
        hed_xml_file = os.path.join(base_data_dir, "schema_tests/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls._refs_json_filename = os.path.join(base_data_dir, "sidecar_tests/basic_refs_test.json")
        cls._bad_refs_json_filename = os.path.join(base_data_dir, "sidecar_tests/bad_refs_test2.json")
        cls._malformed_refs_json_filename = os.path.join(base_data_dir, "sidecar_tests/malformed_refs_test.json")

    def test_basic_refs(self):
        sidecar = Sidecar(self._refs_json_filename)
        issues = sidecar.validate(self.hed_schema)

        self.assertEqual(len(issues), 0)
        refs = sidecar.get_column_refs()
        self.assertEqual(len(refs), 2)

    def test_bad_refs(self):
        sidecar = Sidecar(self._bad_refs_json_filename)
        issues = sidecar.validate(self.hed_schema)

        self.assertEqual(len(issues), 2)

    def test_malformed_refs(self):
        sidecar = Sidecar(self._malformed_refs_json_filename)
        issues = sidecar.validate(self.hed_schema)

        self.assertEqual(len(issues), 4)

    def test_malformed_braces(self):
        hed_strings = [
            "column2}, Event, Action",
             "{column, Event, Action",
             "This is a {malformed {input string}} with extra {opening brackets",
             "{Event{Action}}",
             "Event, Action}"
        ]
        error_counts = [
            1,
            1,
            3,
            2,
            1
        ]

        for string, error_count in zip(hed_strings, error_counts):
            issues = SidecarValidator._find_non_matching_braces(string)

            self.assertEqual(len(issues), error_count)


    def test_bad_structure_na(self):
        sidecar_with_na_json = '''
{
  "column3": {
       "HED": {
         "cat1": "Event",
         "n/a": "Description/invalid category name"
       }
   }
}
'''
        sidecar = Sidecar(io.StringIO(sidecar_with_na_json))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 1)

    def test_bad_structure_HED_in_ignored(self):
        sidecar_with_na_json = '''
    {
      "column3": {
           "other": {
             "HED": "Event",
             "n/a": "Description/invalid category name"
           }
       },
       "HED": {
       
       },
       "OtherBad": {
           "subbad": ["thing1", "HED", "Other"]
       }
    }
    '''
        sidecar = Sidecar(io.StringIO(sidecar_with_na_json))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 2)

    def test_bad_pound_signs(self):
        sidecar_json = '''
    {
      "columnCat": {
           "HED": {
             "cat1": "Event",
             "cat2": "Weight/# g"
           }
       },
       "columnVal": {
            "HED": "Description/Invalid"
       },
       "columnVal2": {
            "HED": "Description/#, Weight/# g"
       }
    }
    '''
        sidecar = Sidecar(io.StringIO(sidecar_json))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 3)

    def test_invalid_list(self):
        sidecar_json = '''
        {
          "columnInvalidList": {
               "HED": ["This", "should", "be", "a", "dictionary", "not", "a", "list"]
           }
        }
        '''
        self.run_test(sidecar_json, expected_number_of_issues=1)

    def test_invalid_number(self):
        sidecar_json = '''
        {
          "columnInvalidNumber": {
               "HED": 12345
           }
        }
        '''
        self.run_test(sidecar_json, expected_number_of_issues=1)

    def test_invalid_boolean(self):
        sidecar_json = '''
        {
          "columnInvalidBoolean": {
               "HED": true
           }
        }
        '''
        self.run_test(sidecar_json, expected_number_of_issues=1)

    def test_mixed_category(self):
        sidecar_json = '''
        {
          "columnMixedCategory": {
               "HED": {
                 "cat1": "Event",
                 "cat2": ["Invalid", "data", "type"]
               }
           }
        }
        '''
        self.run_test(sidecar_json, expected_number_of_issues=1)

    def run_test(self, sidecar_json, expected_number_of_issues):
        sidecar = Sidecar(io.StringIO(sidecar_json))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), expected_number_of_issues)
