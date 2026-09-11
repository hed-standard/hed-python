from hed.schema import from_string

library_schema_start = """HED library="testcomparison" version="1.1.0" withStandard="8.3.0" unmerged="true"

'''Prologue'''

!# start schema

"""

library_schema_end = """


!# end hed
    """

default_end_lines = """
!# end schema
"""

required_non_tag = [
    "'''Unit classes'''",
    "'''Unit modifiers'''",
    "'''Value classes'''",
    "'''Schema attributes'''",
    "'''Properties'''",
    "'''Epilogue'''",
]


def _get_test_schema(node_lines, other_lines=(default_end_lines,)):
    node_section = "\n".join(node_lines)
    non_tag_section = "\n".join(other_lines)
    for name in required_non_tag:
        if name not in other_lines:
            non_tag_section += f"\n{name}\n"
    library_schema_string = library_schema_start + node_section + non_tag_section + library_schema_end
    test_schema = from_string(library_schema_string, ".mediawiki")

    return test_schema


def load_schema1():
    test_nodes = [
        "'''TestNode''' <nowiki> [This is a simple test node]</nowiki>\n",
        " *TestNode2",
        " *TestNode3",
        " *TestNode4",
    ]
    return _get_test_schema(test_nodes)


def load_schema2():
    test_nodes = [
        "'''TestNode''' <nowiki> [This is a simple test node]</nowiki>\n",
        " *TestNode2",
        " **TestNode3",
        " *TestNode5",
    ]

    return _get_test_schema(test_nodes)


def load_schema_intensity():
    test_nodes = ["'''IntensityTakesValue'''", " * # {unitClass=intensityUnits}"]
    return _get_test_schema(test_nodes)


def load_schema_derived_default():
    """A unit class whose defaultUnits (mV) is a derived form of its only listed unit (V), as HED 8.5.0 allows.

    As in hed-schemas 8.5.0 (A has conversionFactor=1000 against defaultUnits=mA), the listed unit's factor
    converts to the derived default, so 1 V = 1000 mV and the default's own factor (m x V) is 1.0.
    """
    test_nodes = ["'''VoltageTakesValue'''", " * # {takesValue, unitClass=testVoltageUnits, valueClass=numericClass}"]
    unit_class_lines = (
        default_end_lines,
        "'''Unit classes'''",
        "* testVoltageUnits <nowiki>{defaultUnits=mV}</nowiki>",
        "** V <nowiki>{SIUnit, unitSymbol, conversionFactor=1000}</nowiki>",
    )
    return _get_test_schema(test_nodes, unit_class_lines)


def load_schema_any_units(extra_unit_class_lines=(), any_units_attributes=""):
    """A Quantity tag whose # takes a unit from any unit class through the anyUnits pseudo class (HED 8.5.0).

    Parameters:
        extra_unit_class_lines (tuple[str]): Further Unit classes section lines, appended after anyUnits.
        any_units_attributes (str): Attribute text for the anyUnits line, e.g. "{defaultUnits=s}" (invalid).
    """
    test_nodes = ["'''Quantity'''", " * # {takesValue, unitClass=anyUnits, valueClass=numericClass}"]
    any_units_line = "* anyUnits <nowiki>" + any_units_attributes
    any_units_line += "[Pseudo unit class: a placeholder with unitClass=anyUnits accepts any unit.]</nowiki>"
    unit_class_lines = (
        default_end_lines,
        "'''Unit classes'''",
        any_units_line,
        *extra_unit_class_lines,
    )
    return _get_test_schema(test_nodes, unit_class_lines)
