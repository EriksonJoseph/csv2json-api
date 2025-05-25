"""
Root conftest.py for pytest.
This file ensures that the project root is in the Python path for all tests.
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
