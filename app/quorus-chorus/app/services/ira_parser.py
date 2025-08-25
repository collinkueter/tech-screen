"""
IRA File Parser - Handles parsing of proprietary IRA format files.

This module is responsible for parsing IRA (Internal Revenue Accounting) files
that contain song payout information in a specific format.
"""

import re
import logging
from decimal import Decimal
from typing import BinaryIO, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IRAEntry:
    """Represents a parsed IRA entry from the data file."""

    licensing_group: str
    last_5_isrc: str
    song_title_length: int
    payout_rate: Decimal


class IRAFormatError(ValueError):
    """Raised when IRA entry format is invalid."""

    pass


class IRAFileParser:
    """
    Parser for IRA (Internal Revenue Accounting) format files.

    IRA Format Specification:
    IRA-{Licensing Group}-{Last 5 ISRC}-{Song Title Length}/payout_rate

    Example: IRA-The_Orchard-83229-013/0.0048615

    Where:
    - Licensing Group: "The Orchard" (underscores represent spaces)
    - Last 5 digits of ISRC: "83229"
    - Song title length: 13 characters
    - Payout rate: $0.0048615 per play
    """

    # Regex pattern to match IRA format
    IRA_PATTERN = re.compile(r"^IRA-(.+)-(\d{5})-(\d{3})/(-?[0-9.]+)$")

    @classmethod
    def parse_entry(cls, entry_str: str) -> IRAEntry:
        """
        Parse a single IRA entry string into structured data.

        Args:
            entry_str: Raw IRA entry string

        Returns:
            IRAEntry object with parsed data

        Raises:
            IRAFormatError: If the entry format is invalid
        """
        # Remove any whitespace
        entry_str = entry_str.strip()

        if not entry_str:
            raise IRAFormatError("Empty IRA entry")

        match = cls.IRA_PATTERN.match(entry_str)

        if not match:
            raise IRAFormatError(f"Invalid IRA entry format: {entry_str}")

        licensing_group, last_5_isrc, title_length_str, payout_rate_str = match.groups()

        # Convert underscores to spaces in licensing group
        licensing_group = licensing_group.replace("_", " ")

        try:
            song_title_length = int(title_length_str)
            payout_rate = Decimal(payout_rate_str)
        except (ValueError, TypeError) as e:
            raise IRAFormatError(
                f"Invalid numeric values in IRA entry: {entry_str}"
            ) from e

        # Validate ranges
        if song_title_length < 0:
            raise IRAFormatError(
                f"Invalid song title length {song_title_length} in entry: {entry_str}"
            )

        if payout_rate < 0:
            raise IRAFormatError(
                f"Invalid payout rate {payout_rate} in entry: {entry_str}"
            )

        return IRAEntry(
            licensing_group=licensing_group,
            last_5_isrc=last_5_isrc,
            song_title_length=song_title_length,
            payout_rate=payout_rate,
        )

    @classmethod
    def parse_file(cls, ira_file: BinaryIO) -> List[IRAEntry]:
        """
        Parse an entire IRA file into a list of IRAEntry objects.

        Args:
            ira_file: Binary file object containing IRA data

        Returns:
            List of parsed IRAEntry objects

        Raises:
            UnicodeDecodeError: If file cannot be decoded as UTF-8
        """
        try:
            content = ira_file.read().decode("utf-8")
            return cls.parse_content(content)

        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode IRA file: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing IRA file: {e}")
            raise

    @classmethod
    def parse_content(cls, content: str) -> List[IRAEntry]:
        """
        Parse IRA content string into a list of IRAEntry objects.

        Args:
            content: Raw IRA file content as string

        Returns:
            List of parsed IRAEntry objects
        """
        if not content or not content.strip():
            logger.info("Empty or whitespace-only IRA content provided")
            return []

        # Split by delimiter (-*-) and filter out empty entries
        raw_entries = [entry.strip() for entry in content.split("-*-") if entry.strip()]

        entries = []
        parse_errors = []

        for i, raw_entry in enumerate(raw_entries):
            try:
                entry = cls.parse_entry(raw_entry)
                entries.append(entry)
            except IRAFormatError as e:
                parse_errors.append((i + 1, raw_entry, str(e)))
                logger.warning(f"Skipping invalid IRA entry {i + 1}: {e}")
                continue

        if parse_errors:
            logger.warning(
                f"Encountered {len(parse_errors)} parse errors out of {len(raw_entries)} entries"
            )

        logger.info(
            f"Successfully parsed {len(entries)} IRA entries from {len(raw_entries)} total entries"
        )

        return entries

    @classmethod
    def validate_entry(cls, entry: IRAEntry) -> bool:
        """
        Validate an IRAEntry for business rule compliance.

        Args:
            entry: IRAEntry to validate

        Returns:
            True if entry passes validation, False otherwise
        """
        # Basic validation rules
        if not entry.licensing_group or not entry.licensing_group.strip():
            logger.warning(f"Entry has empty licensing group: {entry}")
            return False

        if len(entry.last_5_isrc) != 5 or not entry.last_5_isrc.isdigit():
            logger.warning(f"Entry has invalid ISRC format: {entry.last_5_isrc}")
            return False

        if entry.song_title_length <= 0 or entry.song_title_length > 1000:
            logger.warning(
                f"Entry has suspicious title length: {entry.song_title_length}"
            )
            return False

        if entry.payout_rate <= 0 or entry.payout_rate > 1:
            logger.warning(f"Entry has suspicious payout rate: {entry.payout_rate}")
            return False

        return True
