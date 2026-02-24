"""Debug the 7 remaining deprecation test failures."""

import sys

sys.path.insert(0, ".")

from hed.schema.hed_schema_io import from_string
from hed.schema.hed_schema_constants import HedKey, HedSectionKey


def load_and_check(label, lines, expect_fail=True):
    print("\n" + "=" * 60)
    print(f"{label}")
    print("=" * 60)
    schema_str = "\n".join(lines)
    schema = from_string(schema_str, schema_format=".mediawiki")
    issues = schema.check_compliance()
    if issues:
        for i in issues:
            print(f"  {i['code']}: {i.get('message', str(i))[:150]}")
        if not expect_fail:
            print(f"  ** PROBLEM: {len(issues)} issues but test expects PASS **")
    else:
        if expect_fail:
            print("  ** PROBLEM: NO ISSUES but test expects FAIL **")
        else:
            print("  OK: No issues (expected)")
    return schema, issues


# Test #1 fail[2]: deprecatedFrom=1.0.0 at version 1.0.0
schema, issues = load_and_check(
    "Test #1 fail[2]: deprecatedFrom=1.0.0 at version 1.0.0",
    [
        'HED version="1.0.0" library="score" withStandard="8.3.0" unmerged="True"',
        "'''Prologue'''",
        "!# start schema",
        "'''BaseTag'''",
        "* Extension {deprecatedFrom=1.0.0}",
        "!# end schema",
        "'''Unit classes'''",
        "'''Unit modifiers'''",
        "'''Value classes'''",
        "'''Schema attributes'''",
        "'''Properties'''",
        "'''Epilogue'''",
        "!# end hed",
    ],
    expect_fail=True,
)
# Check what InLibrary looks like for Extension
tags = schema[HedSectionKey.Tags]
for e in tags.all_entries:
    if "Extension" in e.name:
        print(f"  Extension InLibrary: {e.has_attribute(HedKey.InLibrary, return_value=True)}")
        print(f"  Extension deprecatedFrom: {e.attributes.get('deprecatedFrom')}")
        break

# Test #2 fail[1]: deprecated parent, non-deprecated child
schema, issues = load_and_check(
    "Test #2 fail[1]: deprecated parent with non-deprecated child",
    [
        'HED version="1.1.0" library="score" withStandard="8.3.0" unmerged="True"',
        "'''Prologue'''",
        "!# start schema",
        "'''BaseTag''' {deprecatedFrom=1.0.0}",
        "* Extension",
        "!# end schema",
        "'''Unit classes'''",
        "'''Unit modifiers'''",
        "'''Value classes'''",
        "'''Schema attributes'''",
        "'''Properties'''",
        "'''Epilogue'''",
        "!# end hed",
    ],
    expect_fail=True,
)
# Check BaseTag's children
tags = schema[HedSectionKey.Tags]
for e in tags.all_entries:
    if e.name == "BaseTag":
        print(f"  BaseTag children: {list(e.children.keys())}")
        print(f"  BaseTag deprecatedFrom: {e.attributes.get('deprecatedFrom')}")
        print(f"  BaseTag InLibrary: {e.has_attribute(HedKey.InLibrary, return_value=True)}")
        break

# Test #7 fail[1]: Extension with deprecatedAttribute (custom attribute)
schema, issues = load_and_check(
    "Test #7 fail[1]: tag with deprecated custom attribute (should FAIL)",
    [
        'HED version="1.1.0" library="score" withStandard="8.3.0" unmerged="True"',
        "'''Prologue'''",
        "!# start schema",
        "'''BaseTag'''",
        "* Extension{deprecatedAttribute}",
        "!# end schema",
        "'''Unit classes'''",
        "'''Unit modifiers'''",
        "'''Value classes'''",
        "'''Schema attributes'''",
        "* deprecatedAttribute {deprecatedFrom=1.0.0, elementProperty}",
        "'''Properties'''",
        "'''Epilogue'''",
        "!# end hed",
    ],
    expect_fail=True,
)
# Check what attributes section contains
print("  Schema attributes defined:")
attr_section = schema[HedSectionKey.Attributes]
for name, entry in attr_section.items():
    if "deprecated" in name.lower():
        print(f"    {name}: {entry.attributes}")

# Check properties section
print("  Properties defined:")
props = schema[HedSectionKey.Properties]
for name, entry in props.items():
    if "element" in name.lower() or "property" in name.lower():
        print(f"    {name}: {entry.attributes}")

# Test #7 pass[1]: Extension with deprecatedAttribute AND deprecatedFrom
schema, issues = load_and_check(
    "Test #7 pass[1]: tag with deprecated custom attribute + deprecatedFrom (should PASS)",
    [
        'HED version="1.1.0" library="score" withStandard="8.3.0" unmerged="True"',
        "'''Prologue'''",
        "!# start schema",
        "'''BaseTag'''",
        "* Extension{deprecatedAttribute, deprecatedFrom=1.0.0}",
        "!# end schema",
        "'''Unit classes'''",
        "'''Unit modifiers'''",
        "'''Value classes'''",
        "'''Schema attributes'''",
        "* deprecatedAttribute {deprecatedFrom=1.0.0, elementProperty}",
        "'''Properties'''",
        "'''Epilogue'''",
        "!# end hed",
    ],
    expect_fail=False,
)
