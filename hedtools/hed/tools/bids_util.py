import os


def parse_bids_filename(file_path):
    """ Split a filename into its BIDS suffix, extension, and entities

        Args:
            file_path (str)     Path to be parsed

        Returns:
            suffix (str)        BIDS suffix name
            ext (str)           File extension (including the .)
            entities (dict)     Dictionary with key-value pair being (entity type, entity value)

    """
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
