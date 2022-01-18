import os


def parse_bids_filename(file_path):
    """ Split a filename into its BIDS suffix, extension, and entities

        Args:
            file_path (str)     Path to be parsed

        Returns:
            suffix (str)        BIDS suffix name
            ext (str)           File extension (including the .)
            entities (dict)     Dictionary with key-value pair being (entity type, entity value)
            unmatched (list)    List of unmatched pieces of the filename

    """

    filename = os.path.splitext(os.path.basename(file_path))
    ext = filename[1].lower()
    basename = filename[0]
    if '-' not in basename:
        return basename, ext, {}, []
    entity_pieces = basename.split('_')
    if len(entity_pieces) < 2:
        return '', ext, {}, [basename]
    suffix = entity_pieces[-1]
    entities = {}
    unmatched = []
    entity_pieces = entity_pieces[:-1]
    for entity in reversed(list(enumerate(entity_pieces))):
        pieces = entity[1].split('-')
        if len(pieces) != 2:
            unmatched.append(entity[1])
        else:
            entities[pieces[0]] = pieces[1]
    return suffix, ext, entities, unmatched
