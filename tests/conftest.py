"""Test fixtures and configuration."""

import pytest


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory."""
    from pathlib import Path
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_diff():
    """Sample git diff for testing."""
    return """diff --git a/src/auth.py b/src/auth.py
index 1234567..abcdefg 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,7 +10,7 @@ def authenticate(username, password):
     if not username or not password:
         return False
     
-    query = f"SELECT * FROM users WHERE username='{username}'"
+    query = "SELECT * FROM users WHERE username=%s"
     cursor.execute(query, (username,))
     
     return verify_password(password, user.password)
"""


@pytest.fixture
def sample_ruff_output():
    """Sample ruff JSON output."""
    return """[
    {
        "filename": "src/main.py",
        "location": {"row": 42, "column": 1},
        "code": "E501",
        "message": "Line too long (120 > 100 characters)",
        "url": "https://example.com"
    }
]"""


@pytest.fixture
def sample_semgrep_output():
    """Sample semgrep JSON output."""
    return """{
    "results": [
        {
            "check_id": "python.lang.security.audit.sqli.sqli",
            "path": "src/auth.py",
            "start": {"line": 13},
            "end": {"line": 13},
            "extra": {
                "message": "Potential SQL injection",
                "severity": "ERROR",
                "metadata": {
                    "cwe": "CWE-89"
                }
            }
        }
    ]
}"""

