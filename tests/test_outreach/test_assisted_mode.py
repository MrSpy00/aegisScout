import pytest
from unittest.mock import patch, MagicMock
from aegisScout.core.models import Lead
from aegisScout.outreach.assisted_mode import send_assisted_message

def test_send_assisted_message_with_handle():
    lead = Lead(id=1, business_name="Test Business", instagram_handle="test_ig")
    draft = "Hello Test Business"

    with patch("pyperclip.copy") as mock_copy, \
         patch("webbrowser.open") as mock_open:
        
        success = send_assisted_message(lead, draft)
        
        assert success is True
        mock_copy.assert_called_once_with(draft)
        mock_open.assert_called_once_with("https://www.instagram.com/test_ig/")

def test_send_assisted_message_without_handle():
    lead = Lead(id=2, business_name="Test Business No Handle", instagram_handle=None)
    draft = "Hello Test Business No Handle"

    with patch("pyperclip.copy") as mock_copy, \
         patch("webbrowser.open") as mock_open:
        
        success = send_assisted_message(lead, draft)
        
        assert success is True
        mock_copy.assert_called_once_with(draft)
        # Should open Google search for the business
        mock_open.assert_called_once()
        called_url = mock_open.call_args[0][0]
        assert "google.com" in called_url
        assert "Test%20Business%20No%20Handle" in called_url

def test_send_assisted_message_exception_handling():
    lead = Lead(id=3, business_name="Fail Business")
    draft = "Hello fail"

    # Force pyperclip to raise an exception
    with patch("pyperclip.copy", side_effect=Exception("clipboard error")):
        success = send_assisted_message(lead, draft)
        assert success is False
