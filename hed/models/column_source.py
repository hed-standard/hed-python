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
from typing import Protocol, runtime_checkable

# Cell texts that mean "no value here". None and float NaN are also missing.
MISSING_VALUES = frozenset(["", "n/a"])


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
    """Return True if a cell value stands for "no value": None, a float NaN, ``""`` or ``"n/a"``."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and value in MISSING_VALUES


@runtime_checkable
class ColumnSource(Protocol):
    """The four questions tabular validation asks of a table.

    Only :meth:`as_base_input` may involve pandas, and it is called only for the assembly stage.
    """

    def column_names(self) -> list:
        """Return the column names in table order (column numbers if the table has no names)."""
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
