"""
Run the temporal neurotransmitter test directly.
"""
import sys
import pytest
import os

# Get the directory of the test file
test_file = "app/tests/venv/test_temporal_neurotransmitter_analysis.py"
test_file_path = os.path.join(os.path.dirname(__file__), test_file)

# Run pytest on this specific file
if __name__ == "__main__":
    print(f"Running test: {test_file_path}")
    # Use -xvs flags:
        # x: exit on first failure
        # v: verbose
        # s: show output
        sys.exit(pytest.main(["-xvs", test_file_path]))
