"""Pytest configuration and shared fixtures for unit tests."""

import sys
from pathlib import Path

# Use src/ as the single import root for the bda package.
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


