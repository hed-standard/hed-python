"""Test that CLI wrapper parameters match original script parsers."""

import unittest
import click.core
from click.testing import CliRunner

from hed.cli.cli import cli
from hed.scripts.validate_bids import get_parser as get_validate_bids_parser
from hed.scripts.validate_hed_string import get_parser as get_validate_hed_string_parser
from hed.scripts.hed_extract_bids_sidecar import get_parser as get_extract_sidecar_parser
from hed.scripts.extract_tabular_summary import get_parser as get_extract_summary_parser
from hed.scripts.validate_schemas import get_parser as get_validate_schemas_parser


class TestCLIParameterParity(unittest.TestCase):
    """Test that CLI wrapper parameters match original script parsers."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def _get_parser_options(self, parser):
        """Extract option names from argparse parser.

        Parameters:
            parser: argparse.ArgumentParser instance

        Returns:
            dict: Dictionary with 'positional', 'optional', and 'flags' keys
        """
        positional = []
        optional = {}
        flags = []

        for action in parser._actions:
            if action.dest == "help":
                continue

            if action.option_strings:
                # It's an optional argument
                short_opts = [opt for opt in action.option_strings if opt.startswith("-") and not opt.startswith("--")]
                long_opts = [opt for opt in action.option_strings if opt.startswith("--")]

                if action.nargs == 0:  # It's a flag
                    flags.append((action.dest, short_opts, long_opts))
                else:
                    optional[action.dest] = {
                        "short": short_opts,
                        "long": long_opts,
                        "nargs": action.nargs,
                        "default": action.default,
                    }
            else:
                # It's a positional argument
                positional.append(action.dest)

        return {"positional": positional, "optional": optional, "flags": flags}

    def _get_click_options(self, command):
        """Extract option names from Click command.

        Parameters:
            command: Click command instance

        Returns:
            dict: Dictionary with 'positional', 'optional', and 'flags' keys
        """
        positional = []
        optional = {}
        flags = []

        for param in command.params:
            if isinstance(param, click.core.Argument):
                positional.append(param.name)
            elif isinstance(param, click.core.Option):
                if param.is_flag:
                    flags.append(
                        (param.name, [opt for opt in param.opts if len(opt) == 2], [opt for opt in param.opts if len(opt) > 2])
                    )
                else:
                    optional[param.name] = {
                        "short": [opt for opt in param.opts if len(opt) == 2],
                        "long": [opt for opt in param.opts if len(opt) > 2],
                        "multiple": param.multiple,
                        "default": param.default,
                    }

        return {"positional": positional, "optional": optional, "flags": flags}

    def test_validate_bids_parameters(self):
        """Test validate bids-dataset CLI parameters match validate_bids.py parser."""
        # Get original parser
        original_parser = get_validate_bids_parser()
        original_opts = self._get_parser_options(original_parser)

        # Get CLI command - now it's validate bids-dataset
        validate_group = cli.commands.get("validate")
        self.assertIsNotNone(validate_group, "validate command group not found")
        cli_command = validate_group.commands.get("bids-dataset")

        self.assertIsNotNone(cli_command, "validate bids-dataset command not found in CLI")
        cli_opts = self._get_click_options(cli_command)

        # Check positional arguments
        self.assertEqual(
            len(cli_opts["positional"]),
            len(original_opts["positional"]),
            f"Positional argument count mismatch: CLI has {cli_opts['positional']}, "
            f"original has {original_opts['positional']}",
        )

        # Check that key optional parameters exist
        original_dests = set(original_opts["optional"].keys())
        cli_dests = set(cli_opts["optional"].keys())

        # Some mappings between argparse dest and click param names
        dest_mappings = {
            "error_limit": "error_limit",
            "format": "format",
            "log_file": "log_file",
            "output_file": "output_file",
            "suffixes": "suffixes",
        }

        for orig_dest, cli_dest in dest_mappings.items():
            if orig_dest in original_dests:
                self.assertIn(
                    cli_dest, cli_dests, f"Parameter '{orig_dest}' from original parser not found in CLI as '{cli_dest}'"
                )

        # Check flags
        original_flags = {flag[0] for flag in original_opts["flags"]}
        cli_flags = {flag[0] for flag in cli_opts["flags"]}

        # Key flags that should exist
        required_flags = {"errors_by_file", "log_quiet", "print_output", "verbose", "check_for_warnings"}
        for flag in required_flags:
            if flag in original_flags:
                self.assertIn(flag, cli_flags, f"Flag '{flag}' from original parser not found in CLI")

    def test_extract_bids_sidecar_parameters(self):
        """Test extract bids-sidecar CLI parameters match hed_extract_bids_sidecar.py parser."""
        original_parser = get_extract_sidecar_parser()
        original_opts = self._get_parser_options(original_parser)

        extract_group = cli.commands.get("extract")
        self.assertIsNotNone(extract_group, "extract command group not found")
        extract_command = extract_group.commands.get("bids-sidecar")
        self.assertIsNotNone(extract_command, "extract bids-sidecar command not found")

        cli_opts = self._get_click_options(extract_command)

        # Check positional count matches
        self.assertEqual(
            len(cli_opts["positional"]),
            len(original_opts["positional"]),
            f"Positional argument count mismatch: CLI has {len(cli_opts['positional'])}, original has {len(original_opts['positional'])}",
        )

        # Check optional parameters from original parser exist in CLI
        original_dests = set(original_opts["optional"].keys())
        cli_dests = set(cli_opts["optional"].keys())

        for orig_dest in original_dests:
            self.assertIn(orig_dest, cli_dests, f"Parameter '{orig_dest}' from original parser not found in CLI")

        # Check flags from original parser exist in CLI
        original_flags = {flag[0] for flag in original_opts["flags"]}
        cli_flags = {flag[0] for flag in cli_opts["flags"]}

        for orig_flag in original_flags:
            self.assertIn(orig_flag, cli_flags, f"Flag '{orig_flag}' from original parser not found in CLI")

    def test_extract_tabular_summary_parameters(self):
        """Test extract tabular-summary CLI parameters match extract_tabular_summary.py parser."""
        original_parser = get_extract_summary_parser()
        original_opts = self._get_parser_options(original_parser)

        extract_group = cli.commands.get("extract")
        self.assertIsNotNone(extract_group, "extract command group not found")
        extract_command = extract_group.commands.get("tabular-summary")
        self.assertIsNotNone(extract_command, "extract tabular-summary command not found")

        cli_opts = self._get_click_options(extract_command)

        # Check positional count matches
        self.assertEqual(
            len(cli_opts["positional"]),
            len(original_opts["positional"]),
            f"Positional argument count mismatch: CLI has {len(cli_opts['positional'])}, original has {len(original_opts['positional'])}",
        )

        # Check optional parameters from original parser exist in CLI
        original_dests = set(original_opts["optional"].keys())
        cli_dests = set(cli_opts["optional"].keys())

        for orig_dest in original_dests:
            self.assertIn(orig_dest, cli_dests, f"Parameter '{orig_dest}' from original parser not found in CLI")

        # Check flags from original parser exist in CLI
        original_flags = {flag[0] for flag in original_opts["flags"]}
        cli_flags = {flag[0] for flag in cli_opts["flags"]}

        for orig_flag in original_flags:
            self.assertIn(orig_flag, cli_flags, f"Flag '{orig_flag}' from original parser not found in CLI")

    def test_schema_validate_parameters(self):
        """Test schema validate CLI parameters match validate_schemas.py parser."""
        original_parser = get_validate_schemas_parser()
        original_opts = self._get_parser_options(original_parser)

        schema_group = cli.commands.get("schema")
        validate_command = schema_group.commands.get("validate")
        self.assertIsNotNone(validate_command, "validate command not found in schema group")

        cli_opts = self._get_click_options(validate_command)

        # Check positional count matches (both should have 1)
        self.assertEqual(
            len(cli_opts["positional"]),
            len(original_opts["positional"]),
            f"Positional argument count mismatch: CLI has {len(cli_opts['positional'])}, original has {len(original_opts['positional'])}",
        )

        # Check flags from original parser exist in CLI
        original_flags = {flag[0] for flag in original_opts["flags"]}
        cli_flags = {flag[0] for flag in cli_opts["flags"]}

        for orig_flag in original_flags:
            self.assertIn(orig_flag, cli_flags, f"Flag '{orig_flag}' from original parser not found in CLI")

    def test_validate_hed_string_parameters(self):
        """Test validate hed-string CLI parameters match validate_hed_string.py parser."""
        # Get original parser
        original_parser = get_validate_hed_string_parser()
        self._get_parser_options(original_parser)

        # Get CLI command
        validate_group = cli.commands.get("validate")
        self.assertIsNotNone(validate_group, "validate command group not found")
        cli_command = validate_group.commands.get("hed-string")

        self.assertIsNotNone(cli_command, "validate hed-string command not found in CLI")
        cli_opts = self._get_click_options(cli_command)

        # Check positional arguments (should have hed_string)
        self.assertEqual(
            len(cli_opts["positional"]), 1, f"Should have 1 positional argument, got {len(cli_opts['positional'])}"
        )
        self.assertEqual(cli_opts["positional"][0], "hed_string", "Positional should be hed_string")

        # Check that key optional parameters exist
        required_params = ["schema_version", "definitions", "format", "output_file", "log_level", "log_file"]
        cli_dests = set(cli_opts["optional"].keys())

        for param in required_params:
            self.assertIn(param, cli_dests, f"Parameter '{param}' not found in CLI")

        # Check flags
        required_flags = {"check_for_warnings", "log_quiet", "no_log", "verbose"}
        cli_flags = {flag[0] for flag in cli_opts["flags"]}

        for flag in required_flags:
            self.assertIn(flag, cli_flags, f"Flag '{flag}' not found in CLI")

    def test_schema_add_ids_parameters(self):
        """Test schema add-ids uses positional arguments."""
        schema_group = cli.commands.get("schema")
        add_ids_command = schema_group.commands.get("add-ids")
        self.assertIsNotNone(add_ids_command, "add-ids command not found")

        cli_opts = self._get_click_options(add_ids_command)

        # Should have 3 positional arguments
        self.assertEqual(
            len(cli_opts["positional"]), 3, f"Should have 3 positional arguments, got {len(cli_opts['positional'])}"
        )
        self.assertEqual(cli_opts["positional"][0], "repo_path", "First positional should be repo_path")
        self.assertEqual(cli_opts["positional"][1], "schema_name", "Second positional should be schema_name")
        self.assertEqual(cli_opts["positional"][2], "schema_version", "Third positional should be schema_version")

    def test_all_legacy_commands_have_cli_equivalents(self):
        """Test that all legacy script entry points have CLI equivalents."""
        # Legacy commands from pyproject.toml
        legacy_to_cli = {
            "validate_bids": "validate bids-dataset",
            "hed_extract_bids_sidecar": "extract bids-sidecar",
            "hed_validate_schemas": "schema validate",
            "hed_update_schemas": "schema convert",
            "hed_add_ids": "schema add-ids",
        }

        for legacy, cli_path in legacy_to_cli.items():
            parts = cli_path.split()
            if len(parts) == 1:
                # Top-level command
                self.assertIn(parts[0], cli.commands, f"CLI command '{parts[0]}' not found for legacy '{legacy}'")
            else:
                # Subcommand
                group = cli.commands.get(parts[0])
                self.assertIsNotNone(group, f"CLI group '{parts[0]}' not found for legacy '{legacy}'")
                if hasattr(group, "commands"):
                    self.assertIn(
                        parts[1],
                        group.commands,
                        f"CLI subcommand '{parts[1]}' not found in group '{parts[0]}' for legacy '{legacy}'",
                    )


if __name__ == "__main__":
    unittest.main()
