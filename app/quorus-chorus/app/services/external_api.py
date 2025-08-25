"""
External API Service - Handles all external HTTP API interactions.

This service is responsible for making HTTP calls to external services
to retrieve song metadata and related information.
"""

import logging
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)


class ExternalAPIService:
    """Service for interacting with external song metadata APIs."""

    # External API configuration
    BASE_URL = "http://external-api:4001/api/songs"
    DEFAULT_TIMEOUT = 10.0

    @classmethod
    def fetch_song_by_partial_isrc(
        cls, partial_isrc: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch song metadata from the external API using partial ISRC.

        The external API accepts the last 5 digits of the ISRC.

        Args:
            partial_isrc: Last 5 digits of ISRC

        Returns:
            Dictionary containing song metadata, or None if not found/error
        """
        try:
            url = f"{cls.BASE_URL}/{partial_isrc}"

            with httpx.Client(timeout=cls.DEFAULT_TIMEOUT) as client:
                response = client.get(url)

            if response.status_code == 200:
                logger.debug(f"Successfully fetched metadata for partial ISRC: {partial_isrc}")
                return response.json()
            elif response.status_code == 404:
                logger.debug(f"No metadata found for partial ISRC: {partial_isrc}")
                return None
            else:
                logger.warning(
                    f"API returned status {response.status_code} for partial ISRC: {partial_isrc}"
                )
                return None

        except httpx.RequestError as e:
            logger.error(f"Network error fetching metadata for {partial_isrc}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching metadata for {partial_isrc}: {e}")
            return None

    @classmethod
    def find_song_by_partial_match(
        cls, partial_isrc: str, expected_title_length: int
    ) -> Optional[Dict[str, Any]]:
        """
        Find a song that matches the partial ISRC and title length.

        The external API returns a complete song payload with:
        - isrc: Full ISRC code
        - iswc: International Standard Musical Work Code
        - title: Song title
        - artist: Artist name
        - album: Album name
        - payout_per_play: Decimal payout rate
        - licensing_group: Licensing organization

        Args:
            partial_isrc: Last 5 digits of ISRC
            expected_title_length: Expected length of the song title

        Returns:
            Complete song metadata if found and title length matches, None otherwise
        """
        # Fetch metadata using the partial ISRC
        metadata = cls.fetch_song_by_partial_isrc(partial_isrc)
        
        if not metadata:
            logger.debug(f"No song found for partial ISRC: {partial_isrc}")
            return None
        
        # Validate the API response structure
        required_fields = ["isrc", "title", "artist", "album", "payout_per_play", "licensing_group"]
        missing_fields = [field for field in required_fields if field not in metadata]
        
        if missing_fields:
            logger.warning(
                f"API response for {partial_isrc} missing required fields: {missing_fields}"
            )
            # Continue processing even with missing fields
        
        # Check if title length matches exactly
        title = metadata.get("title")
        if title:
            title_length = len(title)
            
            if title_length == expected_title_length:
                logger.debug(
                    f"Found matching song for partial ISRC {partial_isrc}: "
                    f"'{title}' (length {title_length})"
                )
                return metadata
            else:
                logger.debug(
                    f"Song found but title length mismatch for partial ISRC {partial_isrc}: "
                    f"actual {title_length}, expected {expected_title_length}. "
                    f"Title: '{title}'"
                )
                return None
        else:
            logger.warning(f"Song found but no title in metadata for partial ISRC: {partial_isrc}")
            return None

