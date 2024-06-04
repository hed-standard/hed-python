from hed.schema import load_schema_version
from hed.schema.schema_io.df2schema import load_dataframes
from hed.schema.schema_io.ontology_util import convert_df_to_omn
from hed.scripts.script_util import get_prerelease_path, get_schema_filename
import argparse
import os


def create_ontology(repo_path, schema_name, schema_version, dest):
    final_source = get_prerelease_path(repo_path, schema_name, schema_version)

    dataframes = load_dataframes(final_source)
    _, omn_dict = convert_df_to_omn(dataframes)

    base = get_schema_filename(schema_name, schema_version)
    output_dest = os.path.join(dest, base)
    os.makedirs(output_dest, exist_ok=True)
    for suffix, omn_text in omn_dict.items():
        filename = os.path.join(output_dest, f"{base}_{suffix}.omn")
        with open(filename, mode='w', encoding='utf-8') as opened_file:
            opened_file.writelines(omn_text)

    return 0


def main():
    parser = argparse.ArgumentParser(description='Convert a specified schema in the prerelease folder to an ontology.')
    parser.add_argument('repo_path', help='The location of the hed-schemas directory')
    parser.add_argument('schema_name', help='The name of the schema to convert("standard" for standard schema)')
    parser.add_argument('schema_version', help='The location of the hed-schemas directory')
    parser.add_argument('--dest', default=os.path.join("src", "ontology"), help='The base location to save to')

    args = parser.parse_args()

    repo_path = args.repo_path
    schema_name = args.schema_name
    schema_version = args.schema_version
    dest = args.dest

    # Trigger a local cache hit (this ensures trying to load withStandard schemas will work properly)
    _ = load_schema_version("8.2.0")

    return create_ontology(repo_path, schema_name, schema_version, dest)


if __name__ == "__main__":
    exit(main())
