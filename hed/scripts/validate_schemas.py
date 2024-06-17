import sys
from hed.schema import load_schema_version
from hed.scripts.script_util import validate_all_schemas, sort_base_schemas


def main(arg_list=None):
    # Trigger a local cache hit
    _ = load_schema_version("8.2.0")

    if not arg_list:
        arg_list = sys.argv[1:]

    schema_files = sort_base_schemas(arg_list)
    issues = validate_all_schemas(schema_files)

    if issues:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
