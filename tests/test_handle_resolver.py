import pytest
from unittest.mock import patch, MagicMock
import unittest
from requests.exceptions import HTTPError
from blueskysocial.errors import InvalidUserHandleError
from blueskysocial.handle_resolver import resolve_handle
from blueskysocial.api_endpoints import RPC_SLUG, RESOLVE_HANDLE


class TestHandleResolver(unittest.TestCase):
    @patch("blueskysocial.handle_resolver.requests.get")
    def test_resolve_handle_success(self, mock_get):
        mock_get.return_value.json.return_value = {"did": "resolved_did"}
        mock_get.return_value.status_code = 200
        result = resolve_handle("valid_handle", "access_token")
        assert result == "resolved_did"
        mock_get.assert_called_with(
            f"{RPC_SLUG}{RESOLVE_HANDLE}?handle=valid_handle",
            headers={"Authorization": "Bearer access_token"},
        )

    @patch("blueskysocial.handle_resolver.requests.get")
    def test_resolve_handle_invalid_handle(self, mock_get):
        mock_get.return_value.status_code = 400
        with pytest.raises(InvalidUserHandleError):
            resolve_handle("invalid_handle", "access_token")
        mock_get.assert_called_with(
            f"{RPC_SLUG}{RESOLVE_HANDLE}?handle=invalid_handle",
            headers={"Authorization": "Bearer access_token"},
        )

    @patch("blueskysocial.handle_resolver.requests.get")
    def test_resolve_handle_http_error(self, mock_get):
        mock_get.return_value.raise_for_status.side_effect = HTTPError("Error")
        mock_get.return_value.status_code = 500
        with pytest.raises(HTTPError):
            resolve_handle("valid_handle", "access_token")
        mock_get.assert_called_with(
            f"{RPC_SLUG}{RESOLVE_HANDLE}?handle=valid_handle",
            headers={"Authorization": "Bearer access_token"},
        )
