import io
from decimal import Decimal
from unittest.mock import Mock, patch
import pytest

from app.services.song_ingestion import SongIngestionService, IngestionReport
from app.services.ira_parser import IRAEntry
from app.schemas.song import SongCreate


class TestSongIngestionService:
    """Test suite for SongIngestionService."""

    @pytest.fixture
    def sample_ira_content(self) -> str:
        """Sample IRA file content for testing."""
        return (
            "IRA-UMG-48756-017/0.0048615-*-"
            "IRA-The_Orchard-29791-041/0.0030058-*-"
            "IRA-Sony_Music-68787-024/0.004852-*-"
            "IRA-WMG_Global-34349-012/0.0045614"
        )

    @pytest.fixture
    def sample_ira_file(self, sample_ira_content: str) -> io.BytesIO:
        """Create a sample IRA file for testing."""
        return io.BytesIO(sample_ira_content.encode("utf-8"))

    @pytest.fixture
    def mock_external_api_response(self) -> dict:
        """Mock response from external API with new payload format."""
        return {
            "isrc": "US-XJD-23-48756",
            "iswc": "T-34.989.316-0",
            "title": "Value Million Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "payout_per_play": 0.0048615,
            "licensing_group": "UMG",
        }

    def test_parse_ira_file_integration(self, sample_ira_file: io.BytesIO):
        """Test parsing entire IRA file through SongIngestionService wrapper."""
        entries = SongIngestionService.parse_ira_file(sample_ira_file)

        assert len(entries) == 4
        assert entries[0].licensing_group == "UMG"
        assert entries[0].last_5_isrc == "48756"
        assert entries[1].licensing_group == "The Orchard"
        assert entries[2].licensing_group == "Sony Music"
        assert entries[3].licensing_group == "WMG Global"

    @patch("app.services.external_api.ExternalAPIService.find_song_by_partial_match")
    def test_external_api_integration(self, mock_find, mock_external_api_response):
        """Test that SongIngestionService properly delegates to ExternalAPIService."""
        mock_find.return_value = mock_external_api_response

        # Test through process_ira_entry which uses ExternalAPIService
        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="48756",
            song_title_length=17,
            payout_rate=Decimal("0.0048615"),
        )

        song_create = SongIngestionService.process_ira_entry(entry)

        assert song_create is not None
        assert song_create.title == "Value Million Song"
        mock_find.assert_called_once_with("48756", 17)

    @patch("app.services.external_api.ExternalAPIService.find_song_by_partial_match")
    def test_process_entry_no_match(self, mock_find):
        """Test processing entry when no matching song is found."""
        mock_find.return_value = None

        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="99999",
            song_title_length=17,
            payout_rate=Decimal("0.0048615"),
        )

        song_create = SongIngestionService.process_ira_entry(entry)

        assert song_create is not None
        assert song_create.isrc == "PARTIAL-99999"
        assert song_create.title is None
        assert song_create.artist is None

    @patch("app.services.external_api.ExternalAPIService.find_song_by_partial_match")
    def test_process_entry_with_metadata(self, mock_find, mock_external_api_response):
        """Test processing entry with successful metadata retrieval."""
        mock_find.return_value = mock_external_api_response

        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="48756",
            song_title_length=17,
            payout_rate=Decimal("0.0048615"),
        )

        song_create = SongIngestionService.process_ira_entry(entry)

        assert song_create is not None
        assert song_create.isrc == "US-XJD-23-48756"
        assert song_create.title == "Value Million Song"
        assert song_create.artist == "Test Artist"
        assert song_create.payout_per_play == 0.0048615  # Now from API
        assert song_create.licensing_group == "UMG"  # Now from API

    def test_create_song_from_entry_and_metadata(
        self, mock_external_api_response
    ):
        """Test creating SongCreate object from IRA entry and API metadata."""
        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="48756",
            song_title_length=17,
            payout_rate=Decimal("0.0048615"),
        )

        song_create = SongIngestionService.create_song_from_entry_and_metadata(
            entry, mock_external_api_response
        )

        assert isinstance(song_create, SongCreate)
        assert song_create.isrc == mock_external_api_response["isrc"]
        assert song_create.title == mock_external_api_response["title"]
        assert song_create.artist == mock_external_api_response["artist"]
        assert song_create.album == mock_external_api_response["album"]
        assert song_create.payout_per_play == mock_external_api_response["payout_per_play"]  # Now from API
        assert song_create.licensing_group == mock_external_api_response["licensing_group"]  # Now from API

    def test_create_song_from_entry_only(self):
        """Test creating SongCreate object from IRA entry only (no API metadata)."""
        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="48756",
            song_title_length=17,
            payout_rate=Decimal("0.0048615"),
        )

        song_create = SongIngestionService.create_song_from_entry_and_metadata(
            entry, None
        )

        assert isinstance(song_create, SongCreate)
        assert song_create.isrc == f"PARTIAL-48756"  # Placeholder ISRC
        assert song_create.title is None
        assert song_create.artist is None
        assert song_create.album is None
        assert song_create.payout_per_play == entry.payout_rate
        assert song_create.licensing_group == entry.licensing_group

    @patch("app.services.external_api.ExternalAPIService.find_song_by_partial_match")
    def test_process_ira_entry_exception_handling(self, mock_find):
        """Test processing IRA entry with exception during API call."""
        mock_find.side_effect = Exception("API Error")

        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="48756",
            song_title_length=17,
            payout_rate=Decimal("0.0048615"),
        )

        song_create = SongIngestionService.process_ira_entry(entry)

        assert song_create is None  # Should return None on exception

    @patch("app.crud.crud_song.song.create_or_update")
    @patch.object(SongIngestionService, "parse_ira_file")
    @patch.object(SongIngestionService, "process_ira_entry")
    def test_load_from_file_success(
        self, mock_process, mock_parse, mock_create_or_update, sample_ira_file
    ):
        """Test full load_from_file process with successful ingestion."""
        # Mock parsed entries
        entries = [
            IRAEntry("UMG", "48756", 17, Decimal("0.0048615")),
            IRAEntry("Sony Music", "68787", 24, Decimal("0.004852")),
        ]
        mock_parse.return_value = entries

        # Mock processed songs
        songs = [
            SongCreate(
                isrc="US-XJD-23-48756",
                title="Song 1",
                artist="Artist 1",
                album="Album 1",
                payout_per_play=0.0048615,  # From API
                licensing_group="UMG",  # From API
            ),
            SongCreate(
                isrc="US-ABC-23-68787",
                title="Song 2",
                artist="Artist 2",
                album="Album 2",
                payout_per_play=0.004852,  # From API
                licensing_group="Sony Music",  # From API
            ),
        ]
        mock_process.side_effect = songs

        # Mock successful database operations
        mock_create_or_update.return_value = Mock(id=1)

        report = SongIngestionService.load_from_file(sample_ira_file)

        assert isinstance(report, IngestionReport)
        assert report.total_entries == 2
        assert report.successful_matches == 2
        assert report.failed_matches == 0
        assert report.database_errors == 0
        assert len(report.songs_created) == 2

    @patch("app.crud.crud_song.song.create_or_update")
    @patch.object(SongIngestionService, "parse_ira_file")
    @patch.object(SongIngestionService, "process_ira_entry")
    def test_load_from_file_with_failures(
        self, mock_process, mock_parse, mock_create_or_update, sample_ira_file
    ):
        """Test load_from_file with some failures."""
        entries = [
            IRAEntry("UMG", "48756", 17, Decimal("0.0048615")),
            IRAEntry("Sony Music", "99999", 24, Decimal("0.004852")),  # Will fail
        ]
        mock_parse.return_value = entries

        # First succeeds, second returns None (no match)
        songs = [
            SongCreate(
                isrc="US-XJD-23-48756",
                title="Song 1",
                artist="Artist 1",
                album="Album 1",
                payout_per_play=0.0048615,  # From API
                licensing_group="UMG",  # From API
            ),
            None,  # Failed match
        ]
        mock_process.side_effect = songs

        # Mock database operations - first succeeds, second not called
        mock_create_or_update.return_value = Mock(id=1)

        report = SongIngestionService.load_from_file(sample_ira_file)

        assert report.total_entries == 2
        assert report.successful_matches == 1
        assert report.failed_matches == 1
        assert report.database_errors == 0

    @patch("app.crud.crud_song.song.create_or_update")
    @patch.object(SongIngestionService, "parse_ira_file")
    @patch.object(SongIngestionService, "process_ira_entry")
    def test_load_from_file_database_error(
        self, mock_process, mock_parse, mock_create_or_update, sample_ira_file
    ):
        """Test load_from_file with database errors."""
        entries = [IRAEntry("UMG", "48756", 17, Decimal("0.0048615"))]
        mock_parse.return_value = entries

        song = SongCreate(
            isrc="US-XJD-23-48756",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            payout_per_play=0.0048615,  # From API
            licensing_group="UMG",  # From API
        )
        mock_process.return_value = song

        # Mock database error
        mock_create_or_update.side_effect = Exception("Database error")

        report = SongIngestionService.load_from_file(sample_ira_file)

        assert report.total_entries == 1
        assert report.successful_matches == 1
        assert report.failed_matches == 0
        assert report.database_errors == 1

    def test_ingestion_report_summary(self):
        """Test IngestionReport summary functionality."""
        report = IngestionReport()
        report.total_entries = 100
        report.successful_matches = 85
        report.failed_matches = 10
        report.database_errors = 5
        report.songs_created = ["song1", "song2", "song3"]

        summary = report.get_summary()

        assert "Total entries processed: 100" in summary
        assert "Successful matches: 85" in summary
        assert "Failed matches: 10" in summary
        assert "Database errors: 5" in summary
        assert "Songs created/updated: 3" in summary
        assert "Success rate: 85.0%" in summary

