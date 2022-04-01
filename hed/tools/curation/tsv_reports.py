

def report_tsv_diffs(tsv_dict1, tsv_dict2, logger):
    """ Reports and logs the contents and differences of two equivalent BidsTsvDictionary objects

    Args:
        tsv_dict1 (BidsTsvDictionary): A dictionary representing BIDS-keyed tsv files
        tsv_dict2 (BidsTsvDictionary): A dictionary representing BIDS-keyed tsv files
        logger (HedLogger):            A HedLogger object for reporting the values by key

    Returns:

    """
    logger.add("overall", f"{tsv_dict1.name} has {len(tsv_dict1.file_list)} event files")
    logger.add("overall", f"{tsv_dict2.name} has {len(tsv_dict2.file_list)} event files")
    print(f"Summarizing {tsv_dict1.name}...")
    tsv_dict1.output_files(title=f"\n{tsv_dict1.name} event files", logger=logger)
    tsv_dict2.output_files(title=f"\n{tsv_dict2.name} event files", logger=logger)

    # Make sure there are the same number of files in both collections
    if len(tsv_dict1.key_list) != len(tsv_dict2.key_list):
        msg = f"{tsv_dict1.name} has {len(tsv_dict1.file_list)} files and " +\
              f"{tsv_dict2.name} has {len(tsv_dict2.file_list)} files"
        logger.add("overall", msg, level="ERROR", also_print=True)

    # Compare keys from the two dictionaries to make sure they have the same keys
    key_diff = tsv_dict1.key_diffs(tsv_dict2)
    if key_diff:
        logger.add("overall", f"File key differences {str(key_diff)}", level="ERROR", also_print=True)

    # Output the column names for each type of event file
    print(f"\n{tsv_dict1.name} event file columns:")
    for key, file, rowcount, columns in tsv_dict1.iter_tsv_info():
        logger.add(key, f"{tsv_dict1.name}: [{rowcount} events] {str(columns)}", also_print=True)

    print(f"\n{tsv_dict2.name} event file columns:")
    for key, file, rowcount, columns in tsv_dict2.iter_tsv_info():
        logger.add(key, f"{tsv_dict2.name}: [{rowcount} events] {str(columns)}", also_print=True)

    # Output keys for files in which the BIDS and EEG.events have different numbers of events
    count_diffs = tsv_dict1.count_diffs(tsv_dict2)
    if count_diffs:
        print(f"\nThe number of {tsv_dict1.name} events and {tsv_dict2.name} events differ for the following files:")
        for item in count_diffs:
            msg = f"The {tsv_dict1.name} file has {item[1]} rows and " +\
                  f"the {tsv_dict2.name} event file has {item[2]} rows"
            logger.add(item[0], msg, level="ERROR", also_print=True)
    else:
        logger.add("overall",
                   f"The {tsv_dict1.name} event files and the {tsv_dict2.name} files have the same number of rows",
                   also_print=True)


