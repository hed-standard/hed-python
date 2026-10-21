"""Column sources: what tabular validation asks of a table, independent of how the table is stored.

The staged tabular validator (:class:`~hed.validator.spreadsheet_validator.SpreadsheetValidator`) never
reads a table directly. It asks a column source for the column names and for the distinct values of one
column at a time, and only when it reaches the assembly stage does it ask for a
:class:`~hed.models.base_input.BaseInput`. :class:`~hed.models.base_input.BaseInput` is the pandas-backed
source used for BIDS files; :class:`ListColumnSource` wraps plain Python sequences; a caller with its own
table type (an NWB DynamicTable, for example) writes a class with the same four methods and never builds
a DataFrame unless it wants assembly.
"""

from __future__ import annotations

import math
import numbers
from typing import Protocol, runtime_checkable

from hed.models.model_constants import NAME_WHITESPACE

# Cell texts that mean "no value here". None and float NaN are also missing.
MISSING_VALUES = frozenset(["", "n/a"])


def is_padded(name) -> bool:
    """Return True if a column name or sidecar key begins or ends with whitespace (``NAME_WHITESPACE``).

    A name made only of whitespace is padded. A label that is not a string is never padded.
    """
    return isinstance(name, str) and bool(name) and (name[0] in NAME_WHITESPACE or name[-1] in NAME_WHITESPACE)


def is_blank_name(name) -> bool:
    """Return True if a column name is blank: the empty string, None, or a NaN label."""
    if name is None:
        return True
    if isinstance(name, str):
        return name == ""
    return isinstance(name, numbers.Real) and bool(name != name)


def column_name_text(name) -> str:
    """Return a column name as text, as a text header would hold it.

    A blank label (None or NaN) becomes ``""``. A whole number is written without a decimal point (``1`` and
    ``1.0`` both become ``"1"``), as JavaScript writes it; any other number keeps its usual form (``"1.5"``).
    Anything else is converted with ``str``; a string is returned unchanged.

    Parameters:
        name: A column label (an Excel header cell or a DataFrame label, for example).

    Returns:
        str: The name as text.
    """
    if isinstance(name, str):
        return name
    if is_blank_name(name):
        return ""
    if isinstance(name, numbers.Real) and not isinstance(name, bool) and math.isfinite(name) and name == int(name):
        return str(int(name))
    return str(name)


def check_column_names(names) -> tuple[list, list[int], list]:
    """Find the column names that break the column-name rules (TABULAR_INVALID b, c and a).

    Names are compared exactly as given; nothing is trimmed.

    Parameters:
        names (list): The column names exactly as the table holds them, repeats included.

    Returns:
        tuple: Three lists.
            - padded: each distinct name that begins or ends with whitespace, in header order (reason b).
            - blank: the 0-based position of each blank name, in header order (reason c).
            - repeated: each other string name that appears more than once, in order of its second
              appearance (reason a). A padded name that is also repeated is listed only as padded, and
              blank names are never repeats.
    """
    padded = []
    blank = []
    repeated = []
    seen = set()
    for position, name in enumerate(names):
        if is_blank_name(name):
            blank.append(position)
        elif is_padded(name):
            if name not in padded:
                padded.append(name)
        elif isinstance(name, str):
            if name in seen and name not in repeated:
                repeated.append(name)
            seen.add(name)
    return padded, blank, repeated


def distinct_values(values) -> dict[str, list[int]]:
    """Map each distinct non-missing value of a column, as text, to the 0-based rows holding it.

    Missing is ``None``, a float NaN, ``""`` or ``"n/a"``. Bytes are decoded as UTF-8; everything else
    is converted with ``str``. The dictionary preserves first-occurrence order, so the first row listed
    for a value is the first row that holds it.

    Parameters:
        values (iterable): The column's values in row order.

    Returns:
        dict[str, list[int]]: Distinct text -> rows holding it.
    """
    distinct: dict[str, list[int]] = {}
    for row, value in enumerate(values):
        if is_missing(value):
            continue
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        text = str(value)
        if text in MISSING_VALUES:
            continue
        distinct.setdefault(text, []).append(row)
    return distinct


def is_missing(value) -> bool:
    """Return True if a cell value stands for "no value": None, a NaN of any float width, ``""`` or ``"n/a"``.

    The NaN test accepts any real number rather than only ``float``: numpy's float32 and float16 do not
    subclass Python's float (only float64 does), and a numpy-backed table (an NWB column, a pandas
    frame read with a narrow dtype) hands those NaNs over as values. NaN is the one real value that is
    not equal to itself, and that test needs no conversion to float, so an integer too large for a
    float or a Fraction is simply a value.
    """
    if value is None:
        return True
    if isinstance(value, numbers.Real):
        return bool(value != value)
    return isinstance(value, str) and value in MISSING_VALUES


@runtime_checkable
class ColumnSource(Protocol):
    """The four questions tabular validation asks of a table.

    Only :meth:`as_base_input` may involve pandas, and it is called only for the assembly stage.
    """

    def column_names(self) -> list:
        """Return the column names in table order (column numbers if the table has no names).

        The names are exactly as the table holds them: not trimmed and not de-duplicated, so that
        validation can report a padded, blank or repeated name (:func:`check_column_names`).
        """
        ...

    def distinct_values(self, column_name) -> dict[str, list[int]]:
        """Return the distinct non-missing values of one column, as text, mapped to the rows holding them.

        See the module-level :func:`distinct_values` for the missing-value rules. A source may return a
        smaller dictionary when it can prove some values need no checking (an integer column under a
        numeric value class, for example), or ``{}`` for a column it does not have.
        """
        ...

    def column_mapper(self):
        """Return this source's :class:`~hed.models.column_mapper.ColumnMapper`, or None to have the
        validator build one from the sidecar and the column names (the TabularInput conventions: an
        optional ``HED`` column, warnings for columns the sidecar does not describe)."""
        ...

    def as_base_input(self):
        """Return a :class:`~hed.models.base_input.BaseInput` for the assembly stage, or None to skip it."""
        ...


class ListColumnSource:
    """A column source over plain Python sequences, one per column, with no pandas involved.

    Parameters:
        columns (dict): Column name -> sequence of cell values in row order. Every sequence should have
            the same length.
        mapper (ColumnMapper or None): A mapper to use instead of one built from the sidecar.
        base_input (BaseInput or None): What to hand to the assembly stage; None skips it.
    """

    def __init__(self, columns, mapper=None, base_input=None):
        self._columns = dict(columns)
        self._mapper = mapper
        self._base_input = base_input

    def column_names(self) -> list:
        return list(self._columns)

    def distinct_values(self, column_name) -> dict[str, list[int]]:
        values = self._columns.get(column_name)
        if values is None:
            return {}
        return distinct_values(values)

    def column_mapper(self):
        return self._mapper

    def as_base_input(self):
        return self._base_input
