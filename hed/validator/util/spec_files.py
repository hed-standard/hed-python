"""File-version gate for the JSON files that hedtools copies verbatim from the HED specification.

Specification Appendix A.6.1: each file carries a specification version and a file version. A validator MUST NOT
apply a file whose file version major number it does not support, and it accepts any minor and patch number under
a major number it supports. The two files spell the key differently, each in the style of its other keys.
"""

import re

from hed.errors.exceptions import HedExceptions, HedFileError

# For each specification file: the key that holds its file version and the major number this hedtools supports.
SUPPORTED_FILE_MAJOR = {
    "reserved_tags.json": ("fileVersion", 1),
    "character_sets.json": ("file_version", 1),
}

# ASCII digits only, matched against the whole string (fullmatch, so a trailing newline does not pass).
_VERSION_PATTERN = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")


def check_file_version(data, filename) -> None:
    """Raise unless the file version of a specification file has a major number this hedtools supports.

    Parameters:
        data (dict): The parsed content of the file.
        filename (str): The file's name, a key of SUPPORTED_FILE_MAJOR (``"reserved_tags.json"``).

    Raises:
        HedFileError: INVALID_FILE_FORMAT if the version key is missing, is not a ``major.minor.patch`` string,
            or has a major number other than the supported one.
    """
    key, supported_major = SUPPORTED_FILE_MAJOR[filename]
    version = data.get(key) if isinstance(data, dict) else None
    match = _VERSION_PATTERN.fullmatch(version) if isinstance(version, str) else None
    if match is None:
        raise HedFileError(
            HedExceptions.INVALID_FILE_FORMAT,
            f"{filename} has no valid '{key}' (expected major.minor.patch, found {version!r}).",
            filename,
        )
    if int(match.group(1)) != supported_major:
        raise HedFileError(
            HedExceptions.INVALID_FILE_FORMAT,
            f"{filename} has {key} {version}; this version of hedtools supports only file version "
            f"{supported_major}.x.x of this file (specification Appendix A.6.1).",
            filename,
        )
