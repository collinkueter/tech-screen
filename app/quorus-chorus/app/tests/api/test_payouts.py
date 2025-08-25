"""
Tests for the payout API endpoints.
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.song import Song
from app import crud


client = TestClient(app)


class TestPayoutEndpoints:
    """Test suite for payout endpoints."""

    @pytest.fixture
    def mock_song(self):
        """Create a mock song for testing."""
        song = Mock(spec=Song)
        song.isrc = "US-XYZ-23-12345"
        song.title = "Test Song"
        song.artist = "Test Artist"
        song.album = "Test Album"
        song.payout_per_play = Decimal("0.0048615")
        song.licensing_group = "UMG"
        return song

    def test_get_payout_for_song_success(self, mock_song, monkeypatch):
        """Test successful payout calculation for a song."""
        def mock_get_by_isrc(db: Session, isrc: str):
            if isrc == mock_song.isrc:
                return mock_song
            return None
        
        monkeypatch.setattr(crud.song, "get_by_isrc", mock_get_by_isrc)
        
        response = client.get(
            f"/api/v1/payouts/{mock_song.isrc}",
            params={"play_count": 1000}
        )
        
        assert response.status_code == 200
        expected_payout = float(mock_song.payout_per_play * 1000)
        assert response.json() == pytest.approx(expected_payout)

    def test_get_payout_for_song_not_found(self, monkeypatch):
        """Test payout endpoint with non-existent ISRC."""
        def mock_get_by_isrc(db: Session, isrc: str):
            return None
        
        monkeypatch.setattr(crud.song, "get_by_isrc", mock_get_by_isrc)
        
        response = client.get(
            "/api/v1/payouts/INVALID-ISRC",
            params={"play_count": 100}
        )
        
        assert response.status_code == 404
        assert "Song with ISRC INVALID-ISRC not found" in response.json()["detail"]

    def test_get_payout_for_song_zero_plays(self, mock_song, monkeypatch):
        """Test payout calculation with zero plays."""
        def mock_get_by_isrc(db: Session, isrc: str):
            if isrc == mock_song.isrc:
                return mock_song
            return None
        
        monkeypatch.setattr(crud.song, "get_by_isrc", mock_get_by_isrc)
        
        response = client.get(
            f"/api/v1/payouts/{mock_song.isrc}",
            params={"play_count": 0}
        )
        
        assert response.status_code == 200
        assert response.json() == 0.0

    def test_get_payout_for_song_large_play_count(self, mock_song, monkeypatch):
        """Test payout calculation with large play count."""
        def mock_get_by_isrc(db: Session, isrc: str):
            if isrc == mock_song.isrc:
                return mock_song
            return None
        
        monkeypatch.setattr(crud.song, "get_by_isrc", mock_get_by_isrc)
        
        play_count = 1000000
        response = client.get(
            f"/api/v1/payouts/{mock_song.isrc}",
            params={"play_count": play_count}
        )
        
        assert response.status_code == 200
        expected_payout = float(mock_song.payout_per_play * play_count)
        assert response.json() == pytest.approx(expected_payout)

    def test_get_payout_for_song_with_dates(self, mock_song, monkeypatch):
        """Test payout endpoint with date parameters (currently ignored)."""
        def mock_get_by_isrc(db: Session, isrc: str):
            if isrc == mock_song.isrc:
                return mock_song
            return None
        
        monkeypatch.setattr(crud.song, "get_by_isrc", mock_get_by_isrc)
        
        response = client.get(
            f"/api/v1/payouts/{mock_song.isrc}",
            params={
                "play_count": 500,
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-12-31T23:59:59"
            }
        )
        
        assert response.status_code == 200
        expected_payout = float(mock_song.payout_per_play * 500)
        assert response.json() == pytest.approx(expected_payout)

    def test_get_payout_for_song_missing_play_count(self):
        """Test payout endpoint without required play_count parameter."""
        response = client.get("/api/v1/payouts/US-XYZ-23-12345")
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any(error["loc"] == ["query", "play_count"] for error in errors)