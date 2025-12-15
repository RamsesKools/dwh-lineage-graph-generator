"""Pytest configuration file."""

import sys
from pathlib import Path

# Add the src directory to the Python path so tests can import modules
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))
