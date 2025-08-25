import logging
from typing import BinaryIO, List, Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.schemas.song import SongCreate
from app.crud import crud_song
from app.db.session import SessionLocal
from app.services.ira_parser import IRAFileParser, IRAEntry
from app.services.external_api import ExternalAPIService

logger = logging.getLogger(__name__)


@dataclass
class IngestionReport:
    """Report of the ingestion process results."""

    total_entries: int = 0
    successful_matches: int = 0
    failed_matches: int = 0
    database_errors: int = 0
    songs_created: List[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.songs_created is None:
            self.songs_created = []
        if self.errors is None:
            self.errors = []

    def get_summary(self) -> str:
        """Generate a human-readable summary of the ingestion results."""
        success_rate = (
            (self.successful_matches / self.total_entries * 100)
            if self.total_entries > 0
            else 0
        )

        return f"""
Ingestion Summary:
==================
Total entries processed: {self.total_entries}
Successful matches: {self.successful_matches}
Failed matches: {self.failed_matches}
Database errors: {self.database_errors}
Songs created/updated: {len(self.songs_created)}
Success rate: {success_rate:.1f}%

{f'Errors encountered: {len(self.errors)}' if self.errors else 'No errors encountered'}
        """.strip()


class SongIngestionService:
    """Service for ingesting song data from IRA files and external APIs."""

    @staticmethod
    def parse_ira_file(ira_file: BinaryIO) -> List[IRAEntry]:
        """
        Parse an entire IRA file into a list of IRAEntry objects.

        This method delegates to IRAFileParser for the actual parsing logic.

        Args:
            ira_file: Binary file object containing IRA data

        Returns:
            List of parsed IRAEntry objects
        """
        return IRAFileParser.parse_file(ira_file)




    @staticmethod
    def create_song_from_entry_and_metadata(
        ira_entry: IRAEntry, metadata: Optional[dict]
    ) -> SongCreate:
        """
        Create a SongCreate object from IRA entry and optional API metadata.

        Args:
            ira_entry: Parsed IRA entry with validation data
            metadata: Optional metadata from external API containing full song data

        Returns:
            SongCreate object ready for database insertion
        """
        if metadata:
            return SongCreate(
                isrc=metadata.get("isrc", f"PARTIAL-{ira_entry.last_5_isrc}"),
                title=metadata.get("title"),
                artist=metadata.get("artist"),
                album=metadata.get("album"),
                payout_per_play=metadata.get("payout_per_play"),
                licensing_group=metadata.get("licensing_group"),
            )
        else:
            # Fallback: Create song with only IRA data
            return SongCreate(
                isrc=f"PARTIAL-{ira_entry.last_5_isrc}",
                title=None,
                artist=None,
                album=None,
                payout_per_play=ira_entry.payout_rate,
                licensing_group=ira_entry.licensing_group,
            )

    @staticmethod
    def process_ira_entry(ira_entry: IRAEntry) -> Optional[SongCreate]:
        """
        Process a single IRA entry to find matching song and create SongCreate object.

        The process involves:
        1. Fetch song metadata from external API using partial ISRC
        2. Validate the match using title length from IRA entry
        3. Create SongCreate object with API data (preferred) or IRA fallback

        Args:
            ira_entry: Parsed IRA entry containing partial ISRC and validation data

        Returns:
            SongCreate object if processing successful, None otherwise
        """
        logger.debug(f"Processing IRA entry for partial ISRC: {ira_entry.last_5_isrc}")

        try:
            # Fetch song metadata from external API
            metadata = ExternalAPIService.find_song_by_partial_match(
                ira_entry.last_5_isrc, ira_entry.song_title_length
            )

            if metadata:
                logger.debug(
                    f"Found matching song for partial ISRC {ira_entry.last_5_isrc}: "
                    f"{metadata.get('isrc')} - '{metadata.get('title')}'"
                )
                
                # Validate that licensing groups match (optional validation)
                api_licensing_group = metadata.get('licensing_group')
                if api_licensing_group and api_licensing_group != ira_entry.licensing_group:
                    logger.warning(
                        f"Licensing group mismatch for {ira_entry.last_5_isrc}: "
                        f"IRA='{ira_entry.licensing_group}' vs API='{api_licensing_group}'. Using API value."
                    )
            else:
                logger.warning(
                    f"No matches found for partial ISRC: {ira_entry.last_5_isrc}. "
                    f"Will create song with IRA data only."
                )

            # Create song with API metadata (preferred) or IRA fallback data
            return SongIngestionService.create_song_from_entry_and_metadata(
                ira_entry, metadata
            )

        except Exception as e:
            logger.error(f"Error processing IRA entry {ira_entry.last_5_isrc}: {e}")
            return None

    @staticmethod
    def load_from_file(
        songs_file: BinaryIO, db: Optional[Session] = None
    ) -> IngestionReport:
        """
        Load and process songs from an IRA file.

        Args:
            songs_file: Binary file object containing IRA data
            db: Optional database session (will create new one if not provided)

        Returns:
            IngestionReport with processing results
        """
        report = IngestionReport()

        # Use provided session or create new one
        if db is None:
            db = SessionLocal()
            should_close_db = True
        else:
            should_close_db = False

        try:
            # Parse IRA file
            logger.info("Starting IRA file parsing...")
            ira_entries = SongIngestionService.parse_ira_file(songs_file)
            report.total_entries = len(ira_entries)

            if not ira_entries:
                logger.warning("No valid IRA entries found in file")
                return report

            logger.info(f"Processing {report.total_entries} IRA entries...")

            # Process each IRA entry
            for i, ira_entry in enumerate(ira_entries):
                logger.debug(f"Processing entry {i+1}/{report.total_entries}")

                try:
                    # Process IRA entry to get SongCreate object
                    song_create = SongIngestionService.process_ira_entry(ira_entry)

                    if song_create:
                        report.successful_matches += 1

                        # Persist to database
                        try:
                            created_song = crud_song.song.create_or_update(
                                db=db, obj_in=song_create
                            )
                            report.songs_created.append(created_song.isrc)
                            logger.debug(
                                f"Successfully saved song: {created_song.isrc}"
                            )

                        except Exception as db_error:
                            report.database_errors += 1
                            error_msg = f"Database error for song {song_create.isrc}: {db_error}"
                            logger.error(error_msg)
                            report.errors.append(error_msg)
                    else:
                        report.failed_matches += 1
                        error_msg = (
                            f"Failed to process IRA entry: {ira_entry.last_5_isrc}"
                        )
                        logger.warning(error_msg)
                        report.errors.append(error_msg)

                except Exception as process_error:
                    report.failed_matches += 1
                    error_msg = f"Error processing entry {i+1}: {process_error}"
                    logger.error(error_msg)
                    report.errors.append(error_msg)

            logger.info(f"Ingestion completed. {report.get_summary()}")
            return report

        except Exception as e:
            error_msg = f"Fatal error during ingestion: {e}"
            logger.error(error_msg)
            report.errors.append(error_msg)
            return report

        finally:
            if should_close_db:
                db.close()
