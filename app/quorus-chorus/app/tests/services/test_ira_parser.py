import io
from decimal import Decimal

import pytest

from app.services.ira_parser import IRAFileParser, IRAEntry, IRAFormatError


class TestIRAFileParser:
    """Test suite for IRAFileParser class."""

    def test_parse_entry_valid_basic(self):
        """Test parsing a basic valid IRA entry."""
        entry_str = "IRA-UMG-48756-017/0.0048615"
        entry = IRAFileParser.parse_entry(entry_str)

        assert entry.licensing_group == "UMG"
        assert entry.last_5_isrc == "48756"
        assert entry.song_title_length == 17
        assert entry.payout_rate == Decimal("0.0048615")

    def test_parse_entry_with_underscores(self):
        """Test parsing IRA entry with underscores in licensing group."""
        entry_str = "IRA-The_Orchard-29791-041/0.0030058"
        entry = IRAFileParser.parse_entry(entry_str)

        assert entry.licensing_group == "The Orchard"  # Underscores converted to spaces
        assert entry.last_5_isrc == "29791"
        assert entry.song_title_length == 41
        assert entry.payout_rate == Decimal("0.0030058")

    def test_parse_entry_complex_licensing_group(self):
        """Test parsing entry with complex licensing group name."""
        entry_str = "IRA-Sony_Music_Entertainment-12345-025/0.0045000"
        entry = IRAFileParser.parse_entry(entry_str)

        assert entry.licensing_group == "Sony Music Entertainment"
        assert entry.last_5_isrc == "12345"
        assert entry.song_title_length == 25
        assert entry.payout_rate == Decimal("0.0045000")

    def test_parse_entry_with_whitespace(self):
        """Test parsing entry with leading/trailing whitespace."""
        entry_str = "  IRA-UMG-48756-017/0.0048615  "
        entry = IRAFileParser.parse_entry(entry_str)

        assert entry.licensing_group == "UMG"
        assert entry.last_5_isrc == "48756"

    def test_parse_entry_empty_string(self):
        """Test parsing empty string raises appropriate error."""
        with pytest.raises(IRAFormatError, match="Empty IRA entry"):
            IRAFileParser.parse_entry("")

    def test_parse_entry_whitespace_only(self):
        """Test parsing whitespace-only string raises appropriate error."""
        with pytest.raises(IRAFormatError, match="Empty IRA entry"):
            IRAFileParser.parse_entry("   \n\t  ")

    def test_parse_entry_invalid_format_no_ira_prefix(self):
        """Test parsing entry without IRA prefix."""
        with pytest.raises(IRAFormatError, match="Invalid IRA entry format"):
            IRAFileParser.parse_entry("NOT-IRA-48756-017/0.0048615")

    def test_parse_entry_invalid_format_missing_parts(self):
        """Test parsing entry with missing parts."""
        with pytest.raises(IRAFormatError, match="Invalid IRA entry format"):
            IRAFileParser.parse_entry("IRA-UMG-48756/0.0048615")  # Missing title length

    def test_parse_entry_invalid_format_extra_parts(self):
        """Test parsing entry with extra parts."""
        with pytest.raises(IRAFormatError, match="Invalid IRA entry format"):
            IRAFileParser.parse_entry("IRA-UMG-48756-017-EXTRA/0.0048615")

    def test_parse_entry_invalid_isrc_digits(self):
        """Test parsing entry with invalid ISRC digits."""
        with pytest.raises(IRAFormatError, match="Invalid IRA entry format"):
            IRAFileParser.parse_entry("IRA-UMG-4875-017/0.0048615")  # Only 4 digits

        with pytest.raises(IRAFormatError, match="Invalid IRA entry format"):
            IRAFileParser.parse_entry("IRA-UMG-487567-017/0.0048615")  # 6 digits

        with pytest.raises(IRAFormatError, match="Invalid IRA entry format"):
            IRAFileParser.parse_entry("IRA-UMG-ABCDE-017/0.0048615")  # Letters

    def test_parse_entry_invalid_title_length(self):
        """Test parsing entry with invalid title length."""
        with pytest.raises(IRAFormatError, match="Invalid IRA entry format"):
            IRAFileParser.parse_entry("IRA-UMG-48756-17/0.0048615")  # Only 2 digits

        with pytest.raises(IRAFormatError, match="Invalid IRA entry format"):
            IRAFileParser.parse_entry("IRA-UMG-48756-ABC/0.0048615")  # Letters

    def test_parse_entry_invalid_payout_rate(self):
        """Test parsing entry with invalid payout rate."""
        with pytest.raises(IRAFormatError, match="Invalid IRA entry format"):
            IRAFileParser.parse_entry("IRA-UMG-48756-017/INVALID")

    def test_parse_entry_negative_title_length(self):
        """Test parsing entry with negative title length after parsing."""
        # This would pass regex but fail validation
        with pytest.raises(IRAFormatError, match="Invalid IRA entry format"):
            IRAFileParser.parse_entry("IRA-UMG-48756--17/0.0048615")  # Invalid format due to --

    def test_parse_entry_negative_payout_rate(self):
        """Test parsing entry with negative payout rate."""
        with pytest.raises(IRAFormatError, match="Invalid payout rate"):
            IRAFileParser.parse_entry("IRA-UMG-48756-017/-0.0048615")

    def test_parse_content_single_entry(self):
        """Test parsing content with single entry."""
        content = "IRA-UMG-48756-017/0.0048615"
        entries = IRAFileParser.parse_content(content)

        assert len(entries) == 1
        assert entries[0].licensing_group == "UMG"

    def test_parse_content_multiple_entries(self):
        """Test parsing content with multiple entries."""
        content = (
            "IRA-UMG-48756-017/0.0048615-*-"
            "IRA-The_Orchard-29791-041/0.0030058-*-"
            "IRA-Sony_Music-68787-024/0.004852"
        )
        entries = IRAFileParser.parse_content(content)

        assert len(entries) == 3
        assert entries[0].licensing_group == "UMG"
        assert entries[1].licensing_group == "The Orchard"
        assert entries[2].licensing_group == "Sony Music"

    def test_parse_content_empty_string(self):
        """Test parsing empty content."""
        entries = IRAFileParser.parse_content("")
        assert entries == []

    def test_parse_content_whitespace_only(self):
        """Test parsing whitespace-only content."""
        entries = IRAFileParser.parse_content("   \n\t  ")
        assert entries == []

    def test_parse_content_with_invalid_entries(self):
        """Test parsing content with some invalid entries."""
        content = (
            "IRA-UMG-48756-017/0.0048615-*-"  # Valid
            "INVALID-ENTRY-*-"  # Invalid
            "IRA-Sony_Music-68787-024/0.004852"  # Valid
        )
        entries = IRAFileParser.parse_content(content)

        # Should skip invalid entries but parse valid ones
        assert len(entries) == 2
        assert entries[0].licensing_group == "UMG"
        assert entries[1].licensing_group == "Sony Music"

    def test_parse_content_empty_entries_filtered(self):
        """Test that empty entries between delimiters are filtered out."""
        content = (
            "IRA-UMG-48756-017/0.0048615-*-"
            "-*-"  # Empty entry
            "   -*--*-"  # Whitespace entry
            "IRA-Sony_Music-68787-024/0.004852"
        )
        entries = IRAFileParser.parse_content(content)

        assert len(entries) == 2
        assert entries[0].licensing_group == "UMG"
        assert entries[1].licensing_group == "Sony Music"

    def test_parse_file_valid(self):
        """Test parsing a valid IRA file."""
        content = (
            "IRA-UMG-48756-017/0.0048615-*-"
            "IRA-The_Orchard-29791-041/0.0030058-*-"
            "IRA-Sony_Music-68787-024/0.004852"
        )
        file_obj = io.BytesIO(content.encode("utf-8"))

        entries = IRAFileParser.parse_file(file_obj)

        assert len(entries) == 3
        assert entries[0].licensing_group == "UMG"
        assert entries[1].licensing_group == "The Orchard"
        assert entries[2].licensing_group == "Sony Music"

    def test_parse_file_empty(self):
        """Test parsing empty file."""
        file_obj = io.BytesIO(b"")
        entries = IRAFileParser.parse_file(file_obj)
        assert entries == []

    def test_parse_file_invalid_encoding(self):
        """Test parsing file with invalid UTF-8 encoding."""
        # Create invalid UTF-8 bytes
        invalid_bytes = b"\xff\xfe\x00\x00"
        file_obj = io.BytesIO(invalid_bytes)

        with pytest.raises(UnicodeDecodeError):
            IRAFileParser.parse_file(file_obj)

    def test_validate_entry_valid(self):
        """Test validating a valid IRA entry."""
        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="48756",
            song_title_length=17,
            payout_rate=Decimal("0.0048615"),
        )

        assert IRAFileParser.validate_entry(entry) is True

    def test_validate_entry_empty_licensing_group(self):
        """Test validating entry with empty licensing group."""
        entry = IRAEntry(
            licensing_group="",
            last_5_isrc="48756",
            song_title_length=17,
            payout_rate=Decimal("0.0048615"),
        )

        assert IRAFileParser.validate_entry(entry) is False

    def test_validate_entry_invalid_isrc_length(self):
        """Test validating entry with invalid ISRC length."""
        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="4875",  # Too short
            song_title_length=17,
            payout_rate=Decimal("0.0048615"),
        )

        assert IRAFileParser.validate_entry(entry) is False

    def test_validate_entry_non_digit_isrc(self):
        """Test validating entry with non-digit ISRC."""
        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="4875A",  # Contains letter
            song_title_length=17,
            payout_rate=Decimal("0.0048615"),
        )

        assert IRAFileParser.validate_entry(entry) is False

    def test_validate_entry_zero_title_length(self):
        """Test validating entry with zero title length."""
        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="48756",
            song_title_length=0,
            payout_rate=Decimal("0.0048615"),
        )

        assert IRAFileParser.validate_entry(entry) is False

    def test_validate_entry_excessive_title_length(self):
        """Test validating entry with excessive title length."""
        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="48756",
            song_title_length=1001,  # Too long
            payout_rate=Decimal("0.0048615"),
        )

        assert IRAFileParser.validate_entry(entry) is False

    def test_validate_entry_zero_payout_rate(self):
        """Test validating entry with zero payout rate."""
        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="48756",
            song_title_length=17,
            payout_rate=Decimal("0.0"),
        )

        assert IRAFileParser.validate_entry(entry) is False

    def test_validate_entry_excessive_payout_rate(self):
        """Test validating entry with excessive payout rate."""
        entry = IRAEntry(
            licensing_group="UMG",
            last_5_isrc="48756",
            song_title_length=17,
            payout_rate=Decimal("1.5"),  # > $1 per play seems excessive
        )

        assert IRAFileParser.validate_entry(entry) is False

    def test_ira_entry_dataclass_attributes(self):
        """Test that IRAEntry dataclass has expected attributes."""
        entry = IRAEntry(
            licensing_group="Test Group",
            last_5_isrc="12345",
            song_title_length=20,
            payout_rate=Decimal("0.005"),
        )

        assert hasattr(entry, "licensing_group")
        assert hasattr(entry, "last_5_isrc")
        assert hasattr(entry, "song_title_length")
        assert hasattr(entry, "payout_rate")
        assert entry.licensing_group == "Test Group"
        assert entry.last_5_isrc == "12345"
        assert entry.song_title_length == 20
        assert entry.payout_rate == Decimal("0.005")
