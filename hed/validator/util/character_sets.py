"""The HED character sets of specification section 2.2, loaded from the specification's own file.

``hed/validator/data/character_sets.json`` is a verbatim copy of ``character_sets.json`` as published by
hed-specification (``docs/source/_static/character_sets.json``). Both validators load the same file, so the
named sets, the per-class defaults, the whole-value rules and the string-level exclusions cannot drift between
them or from the specification text, which is generated from the file. Update the copy; never edit it.
"""

import json
import os
import re

from semantic_version import Version

CHARACTER_SETS_FILENAME = "../data/character_sets.json"


def code_point(character) -> str:
    """Return the ``U+XXXX`` form of a single character, for messages and the ``code_point`` issue key."""
    return f"U+{ord(character):04X}"


class CharacterSets:
    """Read-only view of ``character_sets.json``: named sets, aliases, defaults, word rules and exclusions.

    One instance is shared by every validator (``CharacterSets.load()``); the file is read once per process.
    """

    _shared = None

    def __init__(self, data):
        """Wrap the parsed JSON. Use ``CharacterSets.load()`` for the packaged file.

        Parameters:
            data (dict): The parsed content of a ``character_sets.json`` file.
        """
        self._data = data
        self.sets = data["sets"]
        self.aliases = data.get("aliases", {})
        self.value_class_defaults = data.get("value_class_defaults", {})
        self.value_class_words = data.get("value_class_words", {})
        hed_string = data.get("hed_string", {})
        self.forbidden = hed_string.get("forbidden", {})
        self.structural = hed_string.get("structural", {})
        self.tag_chars = list(hed_string.get("tag_chars", {}).get("sets", ["name"]))
        self.declaration_wins_from = data.get("declaration_wins_from", {}).get("standard_version", "8.5.0")
        self._regex_cache = {}

    @classmethod
    def load(cls):
        """Return the shared instance built from the packaged copy of the specification file."""
        if cls._shared is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.realpath(os.path.join(current_dir, CHARACTER_SETS_FILENAME))
            with open(json_path, encoding="utf-8") as f:
                cls._shared = cls(json.load(f))
        return cls._shared

    # ------------------------------------------------------------------
    # Names
    # ------------------------------------------------------------------
    def canonical_name(self, name) -> str:
        """Resolve an alias (``slash`` -> ``forward-slash``); any other name is returned unchanged."""
        return self.aliases.get(name, name)

    def is_known_name(self, name) -> bool:
        """Return True when *name* is a set, an alias, or a single literal character (section 2.2, literal names)."""
        return self.canonical_name(name) in self.sets or len(name) == 1

    def known_names(self) -> list[str]:
        """Return every set name and alias, sorted, for messages that list what ``allowedCharacter`` accepts."""
        return sorted(set(self.sets) | set(self.aliases))

    def _regex_part(self, name) -> str:
        canonical = self.canonical_name(name)
        if canonical in self.sets:
            return self.sets[canonical]["regex"]
        if len(name) == 1:
            return re.escape(name)
        raise KeyError(name)

    def regex_for(self, names):
        """Return a compiled regex matching exactly one character allowed by any of *names*.

        Parameters:
            names (list of str): Set names, aliases or single literal characters.

        Returns:
            re.Pattern: Matches one allowed character.

        Raises:
            KeyError: A name is none of a set, an alias or a single character.
        """
        key = tuple(names)
        if key not in self._regex_cache:
            parts = [self._regex_part(name) for name in names]
            self._regex_cache[key] = re.compile("|".join(f"(?:{part})" for part in parts))
        return self._regex_cache[key]

    def problem_characters(self, text, names) -> list[tuple[int, str]]:
        """Return ``(index, character)`` for every character of *text* that none of *names* allows."""
        if not names:
            return []
        regex = self.regex_for(names)
        return [(index, char) for index, char in enumerate(text) if not regex.fullmatch(char)]

    def describe(self, names) -> str:
        """Say what *names* allow, for an error message.

        A single named set is followed by its description from the file, without the markdown backticks:
        ``value-text (text excluding left and right parentheses, number sign, and tilde)``. Several names are
        listed as written: ``letters, digits, hyphen, underscore, nonascii``. A literal punctuation character is
        quoted (``"+"``); a literal letter or digit is not (``T``).

        Parameters:
            names (list of str): Set names, aliases or single literal characters.

        Returns:
            str: The description.
        """
        if len(names) == 1:
            canonical = self.canonical_name(names[0])
            entry = self.sets.get(canonical)
            if entry is None:
                return self._literal_name(names[0])
            description = entry.get("description", "").replace("`", "").rstrip(".")
            return f"{names[0]} ({description})" if description else names[0]
        return ", ".join(self._literal_name(name) for name in names)

    def _literal_name(self, name) -> str:
        """Quote a single punctuation character used as its own name; leave set names, letters and digits alone."""
        if len(name) == 1 and name not in self.sets and not name.isalnum():
            return f'"{name}"'
        return name

    # ------------------------------------------------------------------
    # Value classes
    # ------------------------------------------------------------------
    def defaults_for(self, class_name, standard_version=None) -> list[str]:
        """Return the default ``allowedCharacter`` names of a standard value class for a standard version.

        Parameters:
            class_name (str): A value class name, for example ``nameClass``.
            standard_version (str or None): The standard schema version in force. None picks the newest entry.

        Returns:
            list[str]: The names; empty when the file has no defaults for *class_name*.
        """
        entries = self.value_class_defaults.get(class_name, [])
        chosen = []
        for entry in entries:
            if standard_version is None or Version(standard_version) >= Version(entry["from"]):
                chosen = entry["sets"]
        return list(chosen)

    def word_rule(self, class_name):
        """Return the compiled whole-value regex of a value class, or None when the class has none."""
        entry = self.value_class_words.get(class_name)
        if entry is None:
            return None
        key = ("word", class_name)
        if key not in self._regex_cache:
            self._regex_cache[key] = re.compile(entry["regex"])
        return self._regex_cache[key]

    def word_rule_description(self, class_name) -> str:
        """Return the description of a value class's whole-value rule, or an empty string."""
        entry = self.value_class_words.get(class_name)
        return entry.get("description", "") if entry else ""

    # ------------------------------------------------------------------
    # HED strings
    # ------------------------------------------------------------------
    @property
    def forbidden_characters(self) -> set[str]:
        """The characters no HED string may contain (``[``, ``]``, ``~``, ``"``); the control ranges are separate."""
        return set(self.forbidden.get("characters", []))

    def describe_forbidden(self) -> str:
        """Say what a HED string may never contain, for an error message."""
        chars = " ".join(self.forbidden.get("characters", []))
        ranges = ", ".join(f"{low}-{high}" for low, high in self.forbidden.get("code_ranges", []))
        return f"no HED string may contain {chars} or a control character (codes {ranges})"

    @property
    def column_braces(self) -> set[str]:
        """The curly braces of a sidecar column reference, allowed only where placeholders are."""
        return {self.structural.get("column_open", "{"), self.structural.get("column_close", "}")}
