from hed.schema import HedKey, HedSectionKey, from_string


library_schema_start = """HED library="testcomparison" version="1.1.0" withStandard="8.2.0" unmerged="true"

'''Prologue'''

!# start schema

"""

library_schema_end = """
!# end schema

!# end hed
    """

def _get_test_schema(node_lines):
    library_schema_string = library_schema_start + "\n".join(node_lines) + library_schema_end
    test_schema = from_string(library_schema_string, ".mediawiki")

    return test_schema


def load_schema1():
    test_nodes = ["'''TestNode''' <nowiki> [This is a simple test node]</nowiki>\n",
                  " *TestNode2",
                  " *TestNode3",
                  " *TestNode4"
                  ]
    return _get_test_schema(test_nodes)


def load_schema2():
    test_nodes = ["'''TestNode''' <nowiki> [This is a simple test node]</nowiki>\n",
                  " *TestNode2",
                  " **TestNode3",
                  " *TestNode5"
                  ]

    return _get_test_schema(test_nodes)


def load_schema_intensity():
    test_nodes = ["'''IntensityTakesValue'''",
                  " * # {unitClass=intensityUnits}"]
    return _get_test_schema(test_nodes)