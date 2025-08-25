"""
Tests for the song upload API endpoint.
"""

import io
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.song_ingestion import IngestionReport


client = TestClient(app)


class TestSongUploadEndpoint:
    """Test suite for song upload endpoint."""

    @pytest.fixture
    def sample_ira_content(self) -> str:
        """Sample IRA file content for testing."""
        return "IRA-UMG-48756-017/0.0048615-*-IRA-Sony_Music-29791-041/0.0030058"

    @patch("app.services.SongIngestionService.load_from_file")
    def test_upload_valid_ira_file(self, mock_load_from_file, sample_ira_content):
        """Test uploading a valid IRA file."""
        # Mock successful ingestion report
        report = IngestionReport()
        report.total_entries = 2
        report.successful_matches = 2
        report.failed_matches = 0
        report.database_errors = 0
        report.songs_created = ["US-XJD-23-48756", "US-ABC-23-29791"]
        report.errors = []
        mock_load_from_file.return_value = report

        # Create file upload
        files = {"file": ("test.ira", io.BytesIO(sample_ira_content.encode()), "text/plain")}
        
        response = client.post("/api/v1/songs/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "File processed successfully"
        assert data["filename"] == "test.ira"
        assert data["summary"]["total_entries"] == 2
        assert data["summary"]["successful_matches"] == 2
        assert data["summary"]["failed_matches"] == 0
        assert data["summary"]["database_errors"] == 0
        assert data["summary"]["songs_created_or_updated"] == 2
        assert data["summary"]["success_rate_percent"] == 100.0
        assert data["songs_processed"] == ["US-XJD-23-48756", "US-ABC-23-29791"]
        assert data["errors"] == []

    @patch("app.services.SongIngestionService.load_from_file")
    def test_upload_with_some_failures(self, mock_load_from_file, sample_ira_content):
        """Test uploading with some processing failures."""
        # Mock report with some failures
        report = IngestionReport()
        report.total_entries = 3
        report.successful_matches = 2
        report.failed_matches = 1
        report.database_errors = 0
        report.songs_created = ["US-XJD-23-48756", "US-ABC-23-29791"]
        report.errors = ["Failed to process entry: 99999"]
        mock_load_from_file.return_value = report

        files = {"file": ("test.ira", io.BytesIO(sample_ira_content.encode()), "text/plain")}
        
        response = client.post("/api/v1/songs/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        
        assert data["summary"]["success_rate_percent"] == 66.7
        assert len(data["errors"]) == 1
        assert "Failed to process entry: 99999" in data["errors"]

    def test_upload_invalid_file_type(self):
        """Test uploading an invalid file type."""
        files = {"file": ("test.pdf", io.BytesIO(b"invalid content"), "application/pdf")}
        
        response = client.post("/api/v1/songs/upload", files=files)

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_txt_file_extension(self, sample_ira_content):
        """Test uploading a .txt file (should be accepted)."""
        files = {"file": ("test.txt", io.BytesIO(sample_ira_content.encode()), "text/plain")}
        
        with patch("app.services.SongIngestionService.load_from_file") as mock_load:
            report = IngestionReport()
            report.total_entries = 1
            report.successful_matches = 1
            report.songs_created = ["US-TEST-23-12345"]
            mock_load.return_value = report

            response = client.post("/api/v1/songs/upload", files=files)

            assert response.status_code == 200
            assert response.json()["filename"] == "test.txt"

    @patch("app.services.SongIngestionService.load_from_file")
    def test_upload_service_error(self, mock_load_from_file, sample_ira_content):
        """Test handling of service errors during upload."""
        mock_load_from_file.side_effect = Exception("Database connection failed")

        files = {"file": ("test.ira", io.BytesIO(sample_ira_content.encode()), "text/plain")}
        
        response = client.post("/api/v1/songs/upload", files=files)

        assert response.status_code == 500
        assert "Error processing file" in response.json()["detail"]

    def test_upload_empty_filename(self, sample_ira_content):
        """Test uploading file with no filename."""
        files = {"file": ("", io.BytesIO(sample_ira_content.encode()), "text/plain")}
        
        response = client.post("/api/v1/songs/upload", files=files)

        assert response.status_code == 422  # FastAPI returns 422 for validation errors
        # The empty filename should trigger a validation error

    @patch("app.services.SongIngestionService.load_from_file")
    def test_upload_zero_entries(self, mock_load_from_file, sample_ira_content):
        """Test uploading file that results in zero entries processed."""
        # Mock empty report
        report = IngestionReport()
        report.total_entries = 0
        report.successful_matches = 0
        report.failed_matches = 0
        report.database_errors = 0
        report.songs_created = []
        report.errors = []
        mock_load_from_file.return_value = report

        files = {"file": ("empty.ira", io.BytesIO(b""), "text/plain")}
        
        response = client.post("/api/v1/songs/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        
        assert data["summary"]["total_entries"] == 0
        assert data["summary"]["success_rate_percent"] == 0
        assert data["songs_processed"] == []