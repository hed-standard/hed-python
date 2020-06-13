from tests.test_translation_hed import TestHed

local_hed_schema_file = 'tests/data/HED.xml'
local_hed_schema_version = 'v1.6.0-restruct'


class RemoteHedSchemas(TestHed):
    def test_load_from_central_git_repo(self):
        remote_hed_schema_file = '7.0.4'
