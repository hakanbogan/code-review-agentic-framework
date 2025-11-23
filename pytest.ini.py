"""Pytest configuration."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "e2e: end-to-end tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "unit: unit tests")

