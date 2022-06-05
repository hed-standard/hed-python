

def report_diffs(tsv_dict1, tsv_dict2, logger):
    """ Reports and logs the contents and differences of two equivalent BidsTabularDictionary objects

    Args:
        tsv_dict1 (BidsTabularDictionary):  A dictionary representing BIDS-keyed tsv files.
        tsv_dict2 (BidsTabularDictionary):  A dictionary representing BIDS-keyed tsv files.
        logger (HedLogger):                 A HedLogger object for reporting the values by key.

    Returns:
        str:  A string with the differences.

    """
    report_list = [f"{tsv_dict1.name} has {len(tsv_dict1.file_list)} event files"]
    logger.add("overall", f"{report_list[-1]}")
    report_list.append(f"{tsv_dict2.name} has {len(tsv_dict2.file_list)} event files")
    logger.add("overall", f"{report_list[-1]}")

    report_list.append(tsv_dict1.output_files(title=f"\n{tsv_dict1.name} event files", logger=logger))
    report_list.append(tsv_dict2.output_files(title=f"\n{tsv_dict2.name} event files", logger=logger))

    # Make sure there are the same number of files in both collections
    if len(tsv_dict1.key_list) != len(tsv_dict2.key_list):
        report_list.append(f"{tsv_dict1.name} has {len(tsv_dict1.file_list)} files and " +
                           f"{tsv_dict2.name} has {len(tsv_dict2.file_list)} files")
        logger.add("overall", f"{report_list[-1]}", level="ERROR")

    # Compare keys from the two dictionaries to make sure they have the same keys
    key_diff = tsv_dict1.key_diffs(tsv_dict2)
    if key_diff:
        report_list.append(f"File key differences {str(key_diff)}")
        logger.add("overall", f"{report_list[-1]}", level="ERROR")

    # Output the column names for each type of event file
    report_list.append(f"\n{tsv_dict1.name} event file columns:")
    for key, file, rowcount, columns in tsv_dict1.iter_files():
        report_list.append(f"{tsv_dict1.name}: [{rowcount} events] {str(columns)}")
        logger.add(key, f"{report_list[-1]}")

    for key, file, rowcount, columns in tsv_dict2.iter_files():
        report_list.append(f"{tsv_dict2.name}: [{rowcount} events] {str(columns)}")
        logger.add(key, f"{report_list[-1]}")

    # Output keys for files in which the BIDS and EEG.events have different numbers of events
    count_diffs = tsv_dict1.count_diffs(tsv_dict2)
    if count_diffs:
        report_list.append(f"\nThe number of {tsv_dict1.name} events and {tsv_dict2.name} events" +
                           f"differ for the following files:")
        for item in count_diffs:
            report_list.append(f"The {tsv_dict1.name} file has {item[1]} rows and " +
                               f"the {tsv_dict2.name} event file has {item[2]} rows")
            logger.add(item[0], f"{report_list[-1]}", level="ERROR")
    else:
        report_list.append(f"\nThe {tsv_dict1.name} and {tsv_dict2.name} files have the same number of rows")
        logger.add("overall", f"{report_list[-1]}")

    return "\n".join(report_list)
