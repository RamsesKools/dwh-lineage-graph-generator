"""Pytest configuration file."""

import sys
from pathlib import Path

# Add the parent directory to the Python path so tests can import modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
