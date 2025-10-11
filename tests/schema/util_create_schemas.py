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
