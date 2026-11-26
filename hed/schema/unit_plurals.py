"""The plurals of HED unit names, loaded from the specification's own file (specification 3.1.4.4 and A.8).

``hed/validator/data/unit_plurals.json`` is a verbatim copy of ``unit_plurals.json`` as published by
hed-specification (``docs/source/_static/unit_plurals.json``). No plural is derived by a rule: a unit name that is
not a key of the file has no plural, a unit symbol never takes one, and a value equal to its key (``hertz``) is the
name's own plural. Update the copy; never edit it. The loader refuses a file whose file version major number it
does not support (specification Appendix A.6.1).
"""

from __future__ import annotations

import json
import os

UNIT_PLURALS_FILENAME = "../validator/data/unit_plurals.json"

_plurals = None


def load_unit_plurals() -> dict[str, str]:
    """Return the ``plurals`` mapping of the packaged ``unit_plurals.json``, read once per process.

    Returns:
        dict[str, str]: Unit name -> its one plural, both case-sensitive.

    Raises:
        HedFileError: INVALID_FILE_FORMAT if the file's ``file_version`` is missing or has an unsupported major
            number.
    """
    global _plurals
    if _plurals is None:
        # hed.validator imports hed.schema, so the version gate is imported when first needed, not at module load.
        from hed.validator.util.spec_files import check_file_version  # noqa: PLC0415 (avoids an import cycle)

        json_path = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), UNIT_PLURALS_FILENAME))
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        check_file_version(data, "unit_plurals.json")
        _plurals = dict(data["plurals"])
    return _plurals


def unit_name_forms(unit_name) -> set[str]:
    """Return a unit name and, if the plurals file lists one, its plural.

    Call this only for a unit of the schema in use that has no ``unitSymbol`` attribute; a unit symbol is written
    exactly as listed (specification A.8.1).

    Parameters:
        unit_name (str): The unit name exactly as the schema lists it (``Volt`` and ``volt`` differ).

    Returns:
        set[str]: ``{unit_name}`` or ``{unit_name, plural}``.
    """
    plural = load_unit_plurals().get(unit_name)
    return {unit_name} if plural is None else {unit_name, plural}
