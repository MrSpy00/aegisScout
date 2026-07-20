import os
import pytest
from unittest.mock import MagicMock, patch

# Use in-memory SQLite for all tests
os.environ["AEGIS_DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("AEGIS_SKIP_PLAYWRIGHT", "1")


@pytest.fixture(autouse=True)
def mock_playwright_import():
    """Auto-mock playwright so tests don't require browser installation."""
    with patch.dict("sys.modules", {
        "playwright": MagicMock(),
        "playwright.sync_api": MagicMock(),
    }):
        yield
