import os
import json
from hed.tools.util.io_util import get_full_extension
import hed.schema.hed_schema_io as hed_schema_io


def get_schema_from_description(root_path):
    try:
        description_path = os.path.abspath(os.path.join(root_path, "dataset_description.json"))
        with open(description_path, "r") as fp:
            dataset_description = json.load(fp)
            version = dataset_description.get("HEDVersion", None)
            return hed_schema_io.load_schema_version(version)
    except Exception as e:
        return None


def group_by_suffix(file_list):
    """ Group files by suffix.

    Parameters:
        file_list (list):  List of file paths.

    Returns:
        dict:  Dictionary with suffixes as keys and file lists as values.

    """
    suffix_groups = {}
    for file_path in file_list:
        name, ext = get_full_extension(file_path)
        result = os.path.basename(name).rsplit('_', 1)
        if len(result) == 2:
            suffix_groups.setdefault(result[1], []).append(file_path)
        else:
            suffix_groups.setdefault(result[0], []).append(file_path)
    return suffix_groups


def parse_bids_filename(file_path):
    """Split a filename into BIDS-relevant components.

    Parameters:
        file_path (str): Path to be parsed.

    Returns:
        dict: Dictionary with keys 'basename', 'suffix', 'prefix', 'ext', 'bad', and 'entities'.

    Notes:
        - Splits into BIDS suffix, extension, and a dictionary of entity name-value pairs.
    """

    name, ext = get_full_extension(file_path.strip())
    basename = os.path.basename(name)
    name_dict = {"basename": basename, "suffix": None, "prefix": None, "ext": ext, "bad": [], "entities": {}}
    if not basename:
        return name_dict

    entity_pieces = basename.rsplit('_', 1)

    # Case: No underscore in filename → could be a single entity (e.g., "task-blech.tsv")
    if len(entity_pieces) == 1:
        entity_count = entity_pieces[0].count('-')
        if entity_count > 1:
            name_dict["bad"].append(entity_pieces[0])
        elif entity_count == 1: # Looks like an entity-type pair
            update_entity(name_dict, entity_pieces[0])
        else:
            name_dict["suffix"] = entity_pieces[0]
        return name_dict

    # Case: Underscore present → split into entities + possible suffix
    rest, suffix = entity_pieces

    # If suffix is a valid entity-type pair (e.g., "task-motor"), move it into the entity dictionary
    if '-' in suffix and suffix.count('-') == 1:
        update_entity(name_dict, suffix)
    else:
        name_dict["suffix"] = suffix

    # Look for prefix - first entity piece without a hyphen
    entity_pieces = rest.split('_')
    if '-' not in entity_pieces[0]:
        name_dict["prefix"] = entity_pieces[0]
        del entity_pieces[0]

    if len(entity_pieces) == 0:
        return name_dict

    # Process entities
    for entity in entity_pieces:
        update_entity(name_dict, entity)

    return name_dict


def update_entity(name_dict, entity):
    """Update the dictionary with a new entity.

    Parameters:
        name_dict (dict): Dictionary of entities.
        entity (str): Entity to be added.
    """
    parts = entity.split('-')

    if len(parts) == 2 and all(parts):  # Valid entity pair
        name_dict["entities"][parts[0]] = parts[1]
    else:
        name_dict["bad"].append(entity)


def get_merged_sidecar(root_path, tsv_file):
    sidecar_files = list(walk_back(root_path, tsv_file))
    merged_sidecar = {}
    while sidecar_files:
        this_sidecar_file = sidecar_files.pop()
        with open(this_sidecar_file, 'r',  encoding='utf-8') as this_sidecar:
            this_sidecar = json.load(this_sidecar)
        merged_sidecar.update(this_sidecar)
    return merged_sidecar


def walk_back(root_path, file_path):
    file_path = os.path.abspath(file_path)
    source_dir = os.path.dirname(file_path)
    root_path = os.path.abspath(root_path)  # Normalize root_path for cross-platform support

    while source_dir and source_dir != root_path:
        candidates = get_candidates(source_dir, file_path)
        if len(candidates) == 1:
            yield candidates[0]
        elif len(candidates) > 1:
            raise Exception({
                "code": "MULTIPLE_INHERITABLE_FILES",
                "location": candidates[0],
                "affects": file_path,
                "issueMessage": f"Candidate files: {candidates}",
            })

            # Stop when we reach the root directory (handling Windows and Unix)
        new_source_dir = os.path.dirname(source_dir)
        if new_source_dir == source_dir or new_source_dir == root_path:
            break
        source_dir = new_source_dir


def get_candidates(source_dir, tsv_file_dict):
    candidates = []
    for file in os.listdir(source_dir):
        this_path = os.path.realpath(os.path.join(source_dir, file))
        if not os.path.isfile(this_path):
            continue
        bids_file_dict = parse_bids_filename(this_path)
        if not bids_file_dict or bids_file_dict["bad"]:
            continue
        if matches_criteria(bids_file_dict, tsv_file_dict):
            candidates.append(this_path)
    return candidates


def matches_criteria(json_file_dict, tsv_file_dict):
    extension_is_valid = json_file_dict["ext"].lower() == ".json"
    suffix_is_valid = (json_file_dict["suffix"] == tsv_file_dict["suffix"]) or not tsv_file_dict["suffix"]
    json_entities = json_file_dict["entities"]
    tsv_entities = tsv_file_dict["entities"]
    entities_match = all(json_entities.get(entity) == tsv_entities.get(entity) for entity in tsv_entities.keys())
    return extension_is_valid and suffix_is_valid and entities_match
