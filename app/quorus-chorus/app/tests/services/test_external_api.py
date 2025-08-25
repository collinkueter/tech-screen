"""
Tests for the ExternalAPIService module.
"""

from unittest.mock import Mock, patch, MagicMock

import httpx
import pytest

from app.services.external_api import ExternalAPIService


class TestExternalAPIService:
    """Test suite for ExternalAPIService."""

    def test_fetch_song_by_partial_isrc_success(self):
        """Test fetching song metadata successfully using partial ISRC."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "isrc": "US-ABC-23-12345",
            "iswc": "T-123.456.789-0",
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "payout_per_play": 0.0050000,
            "licensing_group": "UMG",
        }

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )

            result = ExternalAPIService.fetch_song_by_partial_isrc("12345")

            assert result is not None
            assert result["isrc"] == "US-ABC-23-12345"
            assert result["title"] == "Test Song"

    def test_fetch_song_by_partial_isrc_not_found(self):
        """Test fetching song metadata when not found."""
        mock_response = Mock()
        mock_response.status_code = 404

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )

            result = ExternalAPIService.fetch_song_by_partial_isrc("99999")

            assert result is None

    def test_fetch_song_by_partial_isrc_server_error(self):
        """Test fetching song metadata with server error."""
        mock_response = Mock()
        mock_response.status_code = 500

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = (
                mock_response
            )

            result = ExternalAPIService.fetch_song_by_partial_isrc("12345")

            assert result is None

    def test_fetch_song_by_partial_isrc_network_error(self):
        """Test fetching song metadata with network error."""
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = (
                httpx.RequestError("Network error")
            )

            result = ExternalAPIService.fetch_song_by_partial_isrc("12345")

            assert result is None


    def test_find_song_by_partial_match_found(self):
        """Test finding song by partial ISRC match."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "isrc": "US-ABC-23-12345",
            "iswc": "T-123.456.789-0",
            "title": "Test Song Title",  # 15 characters
            "artist": "Test Artist",
            "album": "Test Album",
            "payout_per_play": 0.0050000,
            "licensing_group": "UMG",
        }

        with patch("httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.return_value = mock_response

            result = ExternalAPIService.find_song_by_partial_match("12345", 15)

            assert result is not None
            assert result["isrc"] == "US-ABC-23-12345"
            assert result["title"] == "Test Song Title"

    def test_find_song_by_partial_match_wrong_title_length(self):
        """Test finding song with mismatched title length."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "isrc": "US-ABC-23-12345",
            "title": "Short",  # 5 characters, expecting 20
            "artist": "Test Artist",
        }

        with patch("httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            # All responses return songs with wrong title length
            mock_get.return_value = mock_response

            result = ExternalAPIService.find_song_by_partial_match("12345", 20)

            assert result is None

    def test_find_song_by_partial_match_exact_length_required(self):
        """Test finding song requires exact title length match."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "isrc": "US-ABC-23-12345",
            "title": "Test Song",  # 9 characters, expecting 10 (no tolerance)
            "artist": "Test Artist",
        }

        with patch("httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.return_value = mock_response

            result = ExternalAPIService.find_song_by_partial_match("12345", 10)

            assert result is None  # Should not match due to length difference

    def test_find_song_by_partial_match_not_found(self):
        """Test finding song when no matches exist."""
        mock_response = Mock()
        mock_response.status_code = 404

        with patch("httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.return_value = mock_response

            result = ExternalAPIService.find_song_by_partial_match("99999", 15)

            assert result is None



    def test_base_url_configuration(self):
        """Test that BASE_URL is correctly configured."""
        assert ExternalAPIService.BASE_URL == "http://localhost:4001/api/songs"

    def test_timeout_configuration(self):
        """Test that DEFAULT_TIMEOUT is correctly configured."""
        assert ExternalAPIService.DEFAULT_TIMEOUT == 10.0

    def test_fetch_song_by_partial_isrc_uses_correct_url(self):
        """Test that fetch_song_by_partial_isrc constructs correct URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"isrc": "US-ABC-23-12345"}

        with patch("httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.return_value = mock_response

            ExternalAPIService.fetch_song_by_partial_isrc("12345")

            # Verify the URL was constructed correctly
            mock_get.assert_called_once_with(
                "http://localhost:4001/api/songs/12345"
            )

    def test_find_song_by_partial_match_no_title(self):
        """Test find_song_by_partial_match when metadata has no title."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "isrc": "US-ABC-23-12345",
            "artist": "Test Artist",
            # No title field
        }

        with patch("httpx.Client") as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.return_value = mock_response

            result = ExternalAPIService.find_song_by_partial_match("12345", 10)

            # Should return None when no title is present
            assert result is None