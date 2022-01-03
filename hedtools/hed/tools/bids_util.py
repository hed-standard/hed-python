import os


def parse_bids_filename(file_path):
    filename = os.path.splitext(os.path.basename(file_path))
    ext = filename[1].lower()
    basename = filename[0].lower()
    entity_pieces = basename.split('_')
    suffix = entity_pieces[-1]
    entity_dict = {}
    entity_pieces = entity_pieces[:-1]
    for entity in entity_pieces:
        pieces = entity.split('-')
        entity_dict[pieces[0]] = pieces[1]
    return suffix, ext, entity_dict
