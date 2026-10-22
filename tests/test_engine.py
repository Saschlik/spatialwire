import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to the path so we can import engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from engine import run_cmd

class TestEngineRunCmd(unittest.TestCase):
    @patch('engine.subprocess.run')
    def test_run_cmd_success(self, mock_run):
        """Test that run_cmd returns stripped stdout on success."""
        # Setup mock response
        mock_result = MagicMock()
        mock_result.stdout = "  expected output  \n"
        mock_run.return_value = mock_result

        # Call function
        result = run_cmd(["echo", "expected output"])

        # Assertions
        self.assertEqual(result, "expected output")
        mock_run.assert_called_once_with(["echo", "expected output"], capture_output=True, text=True, check=False, timeout=5)

    @patch('engine.subprocess.run')
    def test_run_cmd_exception(self, mock_run):
        """Test that run_cmd returns empty string when an exception occurs."""
        # Setup mock to raise Exception
        mock_run.side_effect = Exception("Command failed")

        # Call function
        result = run_cmd(["invalid_command"])

        # Assertions
        self.assertEqual(result, "")
        mock_run.assert_called_once_with(["invalid_command"], capture_output=True, text=True, check=False, timeout=5)

if __name__ == '__main__':
    unittest.main()
