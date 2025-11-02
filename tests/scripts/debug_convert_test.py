"""Debug test to see what's failing."""
import os
import unittest
from hed import load_schema_version
from hed.scripts.convert_and_update_schema import convert_and_update

class DebugTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas_update", "prerelease")
        if not os.path.exists(cls.base_path):
            os.makedirs(cls.base_path)

    def test_debug(self):
        schema = load_schema_version("8.3.0")
        original_name = os.path.join(self.base_path, "test_schema.mediawiki")
        schema.save_as_mediawiki(original_name)

        filenames = [original_name]
        # Don't redirect stdout so we can see errors
        result = convert_and_update(filenames, set_ids=False)
        
        print(f"\nResult: {result}")
        self.assertEqual(result, 0)

if __name__ == "__main__":
    unittest.main()
