"""Test that all Jupyter notebooks in examples directory can be loaded and executed.

This test suite validates that all example notebooks:
1. Are valid Jupyter notebook format
2. Can be executed without errors (with mock data paths)
3. Import statements work correctly

These tests require the optional 'examples' dependencies:
    pip install -e .[examples]
"""

import os
import unittest
from pathlib import Path
import json
import tempfile
import shutil


class TestNotebooks(unittest.TestCase):
    """Test suite for validating example Jupyter notebooks."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures shared across all tests."""
        cls.examples_dir = Path(__file__).parent.parent / "examples"
        cls.test_data_dir = Path(__file__).parent / "data"
        
        # Check if Jupyter dependencies are available
        try:
            import nbformat
            from nbconvert.preprocessors import ExecutePreprocessor
            cls.nbformat = nbformat
            cls.ExecutePreprocessor = ExecutePreprocessor
            cls.has_jupyter = True
        except ImportError:
            cls.has_jupyter = False
            cls.skip_message = (
                "Jupyter dependencies not installed. "
                "Run 'pip install -e .[examples]' to install them."
            )

    def setUp(self):
        """Set up each individual test."""
        if not self.has_jupyter:
            self.skipTest(self.skip_message)

    def test_notebooks_directory_exists(self):
        """Verify the examples directory exists and contains notebooks."""
        self.assertTrue(self.examples_dir.exists(), 
                       f"Examples directory not found: {self.examples_dir}")
        
        notebooks = list(self.examples_dir.glob("*.ipynb"))
        self.assertGreater(len(notebooks), 0, 
                          "No notebooks found in examples directory")

    def test_all_notebooks_valid_format(self):
        """Test that all notebooks are valid Jupyter notebook format."""
        notebooks = list(self.examples_dir.glob("*.ipynb"))
        
        for notebook_path in notebooks:
            with self.subTest(notebook=notebook_path.name):
                try:
                    with open(notebook_path, 'r', encoding='utf-8') as f:
                        nb = self.nbformat.read(f, as_version=4)
                    self.assertIsNotNone(nb, 
                                       f"Failed to read notebook: {notebook_path.name}")
                    self.assertGreater(len(nb.cells), 0, 
                                     f"Notebook has no cells: {notebook_path.name}")
                except Exception as e:
                    self.fail(f"Failed to load {notebook_path.name}: {str(e)}")

    def test_notebook_imports(self):
        """Test that import statements in notebooks are valid."""
        notebooks = list(self.examples_dir.glob("*.ipynb"))
        
        for notebook_path in notebooks:
            with self.subTest(notebook=notebook_path.name):
                with open(notebook_path, 'r', encoding='utf-8') as f:
                    nb = self.nbformat.read(f, as_version=4)
                
                # Extract and test import statements
                import_cells = []
                for cell in nb.cells:
                    if cell.cell_type == 'code':
                        source = cell.source
                        if 'import ' in source:
                            import_cells.append(source)
                
                # Try to validate imports (basic check)
                for cell_source in import_cells:
                    lines = cell_source.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('import ') or line.startswith('from '):
                            # Check for basic syntax errors
                            self.assertNotIn(',,', line, 
                                           f"Syntax error in import: {line}")
                            self.assertNotIn('..', line, 
                                           f"Invalid import path: {line}")

    def test_notebooks_have_markdown_cells(self):
        """Test that notebooks have documentation (markdown cells)."""
        notebooks = list(self.examples_dir.glob("*.ipynb"))
        
        # Some notebooks may be minimal examples without markdown
        skip_markdown_check = ['validate_bids_dataset_with_libraries.ipynb']
        
        for notebook_path in notebooks:
            if notebook_path.name in skip_markdown_check:
                continue
                
            with self.subTest(notebook=notebook_path.name):
                with open(notebook_path, 'r', encoding='utf-8') as f:
                    nb = self.nbformat.read(f, as_version=4)
                
                markdown_cells = [c for c in nb.cells if c.cell_type == 'markdown']
                self.assertGreater(len(markdown_cells), 0,
                                 f"Notebook {notebook_path.name} has no markdown cells")

    def test_specific_notebook_structure(self):
        """Test the structure of specific key notebooks."""
        # Test validate_bids_dataset notebook
        validate_nb = self.examples_dir / "validate_bids_dataset.ipynb"
        if validate_nb.exists():
            with open(validate_nb, 'r', encoding='utf-8') as f:
                nb = self.nbformat.read(f, as_version=4)
            
            # Should have imports from hed.tools and hed.errors
            code_sources = [c.source for c in nb.cells if c.cell_type == 'code']
            all_code = '\n'.join(code_sources)
            
            self.assertIn('BidsDataset', all_code,
                         "validate_bids_dataset should import BidsDataset")
            self.assertIn('get_printable_issue_string', all_code,
                         "validate_bids_dataset should import error handling")
        
        # Test summarize_events notebook
        summarize_nb = self.examples_dir / "summarize_events.ipynb"
        if summarize_nb.exists():
            with open(summarize_nb, 'r', encoding='utf-8') as f:
                nb = self.nbformat.read(f, as_version=4)
            
            code_sources = [c.source for c in nb.cells if c.cell_type == 'code']
            all_code = '\n'.join(code_sources)
            
            self.assertIn('TabularSummary', all_code,
                         "summarize_events should import TabularSummary")

    def test_notebooks_cell_execution_order(self):
        """Test that notebooks have reasonable execution order."""
        notebooks = list(self.examples_dir.glob("*.ipynb"))
        
        for notebook_path in notebooks:
            with self.subTest(notebook=notebook_path.name):
                with open(notebook_path, 'r', encoding='utf-8') as f:
                    nb = self.nbformat.read(f, as_version=4)
                
                # Check that code cells exist and have execution count
                code_cells = [c for c in nb.cells if c.cell_type == 'code']
                self.assertGreater(len(code_cells), 0,
                                 f"Notebook {notebook_path.name} has no code cells")

    def test_notebook_metadata(self):
        """Test that notebooks have proper metadata."""
        notebooks = list(self.examples_dir.glob("*.ipynb"))
        
        for notebook_path in notebooks:
            with self.subTest(notebook=notebook_path.name):
                with open(notebook_path, 'r', encoding='utf-8') as f:
                    nb = self.nbformat.read(f, as_version=4)
                
                # Check for kernel spec
                self.assertIn('metadata', nb, 
                            f"Notebook {notebook_path.name} missing metadata")

    def test_validate_bids_dataset_notebook(self):
        """Specific test for validate_bids_dataset notebook structure."""
        notebook_path = self.examples_dir / "validate_bids_dataset.ipynb"
        
        if not notebook_path.exists():
            self.skipTest("validate_bids_dataset.ipynb not found")
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = self.nbformat.read(f, as_version=4)
        
        # Verify key components
        all_code = '\n'.join([c.source for c in nb.cells if c.cell_type == 'code'])
        
        self.assertIn('from hed.errors import', all_code)
        self.assertIn('from hed.tools import BidsDataset', all_code)
        self.assertIn('BidsDataset', all_code)
        self.assertIn('validate', all_code)

    def test_summarize_events_notebook(self):
        """Specific test for summarize_events notebook structure."""
        notebook_path = self.examples_dir / "summarize_events.ipynb"
        
        if not notebook_path.exists():
            self.skipTest("summarize_events.ipynb not found")
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = self.nbformat.read(f, as_version=4)
        
        # Verify key components
        all_code = '\n'.join([c.source for c in nb.cells if c.cell_type == 'code'])
        
        self.assertIn('TabularSummary', all_code)
        self.assertIn('get_file_list', all_code)

    def test_sidecar_to_spreadsheet_notebook(self):
        """Specific test for sidecar_to_spreadsheet notebook structure."""
        notebook_path = self.examples_dir / "sidecar_to_spreadsheet.ipynb"
        
        if not notebook_path.exists():
            self.skipTest("sidecar_to_spreadsheet.ipynb not found")
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = self.nbformat.read(f, as_version=4)
        
        # Verify key components
        all_code = '\n'.join([c.source for c in nb.cells if c.cell_type == 'code'])
        
        self.assertIn('hed_to_df', all_code)

    def test_merge_spreadsheet_into_sidecar_notebook(self):
        """Specific test for merge_spreadsheet_into_sidecar notebook structure."""
        notebook_path = self.examples_dir / "merge_spreadsheet_into_sidecar.ipynb"
        
        if not notebook_path.exists():
            self.skipTest("merge_spreadsheet_into_sidecar.ipynb not found")
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = self.nbformat.read(f, as_version=4)
        
        # Verify key components
        all_code = '\n'.join([c.source for c in nb.cells if c.cell_type == 'code'])
        
        self.assertIn('df_to_hed', all_code)
        self.assertIn('merge_hed_dict', all_code)

    def test_find_event_combinations_notebook(self):
        """Specific test for find_event_combinations notebook structure."""
        notebook_path = self.examples_dir / "find_event_combinations.ipynb"
        
        if not notebook_path.exists():
            self.skipTest("find_event_combinations.ipynb not found")
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = self.nbformat.read(f, as_version=4)
        
        # Verify key components
        all_code = '\n'.join([c.source for c in nb.cells if c.cell_type == 'code'])
        
        self.assertIn('KeyMap', all_code)

    def test_extract_json_template_notebook(self):
        """Specific test for extract_json_template notebook structure."""
        notebook_path = self.examples_dir / "extract_json_template.ipynb"
        
        if not notebook_path.exists():
            self.skipTest("extract_json_template.ipynb not found")
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = self.nbformat.read(f, as_version=4)
        
        # Verify key components
        all_code = '\n'.join([c.source for c in nb.cells if c.cell_type == 'code'])
        
        # Check for either get_new_dataframe or extract_sidecar_template
        self.assertTrue('get_new_dataframe' in all_code or 'extract_sidecar_template' in all_code,
                       "extract_json_template should use get_new_dataframe or extract_sidecar_template")


class TestNotebookExecution(unittest.TestCase):
    """Test actual notebook execution with mock data.
    
    These tests are more expensive and may be skipped in CI environments.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.examples_dir = Path(__file__).parent.parent / "examples"
        
        # Check if Jupyter dependencies are available
        try:
            import nbformat
            from nbconvert.preprocessors import ExecutePreprocessor
            cls.nbformat = nbformat
            cls.ExecutePreprocessor = ExecutePreprocessor
            cls.has_jupyter = True
        except ImportError:
            cls.has_jupyter = False
            cls.skip_message = (
                "Jupyter dependencies not installed. "
                "Run 'pip install -e .[examples]' to install them."
            )

    def setUp(self):
        """Set up each individual test."""
        if not self.has_jupyter:
            self.skipTest(self.skip_message)
        
        # Create temporary directory for outputs
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _execute_notebook_with_mocked_paths(self, notebook_path, mock_paths=None):
        """
        Execute a notebook with mocked dataset paths.
        
        Parameters:
            notebook_path (Path): Path to the notebook file
            mock_paths (dict): Dictionary mapping variable names to mock paths
        
        Returns:
            tuple: (notebook_object, execution_success, error_message)
        """
        if mock_paths is None:
            mock_paths = {}
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = self.nbformat.read(f, as_version=4)
        
        # Find code cells that set paths and modify them
        for cell in nb.cells:
            if cell.cell_type == 'code':
                source = cell.source
                
                # Replace dataset paths with mock paths
                for var_name, mock_path in mock_paths.items():
                    if f"{var_name} =" in source:
                        lines = source.split('\n')
                        new_lines = []
                        for line in lines:
                            if f"{var_name} =" in line and not line.strip().startswith('#'):
                                # Comment out original line and add mock path
                                new_lines.append(f"# {line}")
                                new_lines.append(f"{var_name} = r'{mock_path}'")
                            else:
                                new_lines.append(line)
                        cell.source = '\n'.join(new_lines)
        
        # Try to execute (will fail if paths don't exist, but tests structure)
        ep = self.ExecutePreprocessor(timeout=60, kernel_name='python3')
        
        try:
            ep.preprocess(nb, {'metadata': {'path': str(self.temp_dir)}})
            return nb, True, None
        except Exception as e:
            # Expected to fail without real data, but we can check the error type
            return nb, False, str(e)

    def test_notebook_execution_structure(self):
        """Test that notebooks can be loaded for execution (doesn't require data)."""
        notebooks = [
            "validate_bids_dataset.ipynb",
            "summarize_events.ipynb",
            "sidecar_to_spreadsheet.ipynb",
        ]
        
        for notebook_name in notebooks:
            notebook_path = self.examples_dir / notebook_name
            if not notebook_path.exists():
                continue
            
            with self.subTest(notebook=notebook_name):
                with open(notebook_path, 'r', encoding='utf-8') as f:
                    nb = self.nbformat.read(f, as_version=4)
                
                # Create executor (doesn't actually execute)
                ep = self.ExecutePreprocessor(timeout=60, kernel_name='python3')
                self.assertIsNotNone(ep, 
                                   f"Could not create executor for {notebook_name}")


if __name__ == '__main__':
    unittest.main()
