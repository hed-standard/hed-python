from hed.errors.error_reporter import get_printable_issue_string
from hed.errors import HedFileError
from hed.schema.hed_schema_io import load_schema, load_schema_version
from hed.scripts.script_util import add_extension, validate_schema, validate_schema_object
from hed.schema.schema_comparer import SchemaComparer


if __name__ == "__main__":
    basename = 'h:\\HED8.4.0_test'
    schema = load_schema_version("8.4.0")
    schema.save_as_json(add_extension(basename, ".json"))
    schema1 = load_schema(add_extension(basename, ".json"))
    print(f"Schemas equal: {schema == schema1}")
    
    if schema != schema1:
        print("\nDifferences:")
        comparer = SchemaComparer(schema, schema1)
        print(comparer.compare_differences())
# def get_schema_issues(full_path):
#     base_schema = ModuleNotFoundError
#     validation_issues = []
#     try:
#         base_schema = load_schema(full_path)
#         validation_issues = validate_schema_object(base_schema, full_path)
#     except HedFileError as e:
#         print(f"Saving/loading error: {full_path} {e.message}")
#         error_text = e.message
#         if e.issues:
#             error_text = get_printable_issue_string(e.issues, title=full_path)
#         validation_issues.append(error_text)
    
#     return base_schema, validation_issues

# if __name__ == "__main__":
#     # Hard-coded basename to test
#     # Change this to test different schemas
#     basename = "h:\\prerelease\\HED8.5.0"
#     all_extensions = [".tsv", ".mediawiki", ".xml", ".json"]
#     all_extensions = [".json"]
#     all_schema_issues = []
#     schemas = {}
#     for extension in all_extensions:
#         full_path = add_extension(basename, extension)
#         print(full_path)
#         schema, validation_issues = get_schema_issues(full_path)
#         print(f"{extension}: issues {validation_issues}")
#         schemas[extension] = schema