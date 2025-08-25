from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.crud import crud_song
from app.models.song import Song
from app.schemas.song import SongCreate, SongUpdate


class TestSongCRUD:
    """Test suite for Song CRUD operations."""

    @pytest.fixture
    def sample_song_data(self) -> SongCreate:
        """Create sample song data for testing."""
        return SongCreate(
            isrc="US-TEST-23-12345",
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            payout_per_play=Decimal("0.005000"),
            licensing_group="Test Group",
        )

    @pytest.fixture
    def sample_song(self, db: Session, sample_song_data: SongCreate) -> Song:
        """Create a sample song in the database."""
        return crud_song.song.create(db=db, obj_in=sample_song_data)

    def test_create_song(self, db: Session, sample_song_data: SongCreate):
        """Test creating a song."""
        song = crud_song.song.create(db=db, obj_in=sample_song_data)

        assert song.isrc == sample_song_data.isrc
        assert song.title == sample_song_data.title
        assert song.artist == sample_song_data.artist
        assert song.album == sample_song_data.album
        assert song.payout_per_play == sample_song_data.payout_per_play
        assert song.licensing_group == sample_song_data.licensing_group
        assert song.id is not None

    def test_get_song_by_id(self, db: Session, sample_song: Song):
        """Test retrieving a song by ID."""
        retrieved = crud_song.song.get(db=db, id=sample_song.id)

        assert retrieved is not None
        assert retrieved.id == sample_song.id
        assert retrieved.isrc == sample_song.isrc
        assert retrieved.title == sample_song.title

    def test_get_song_by_isrc(self, db: Session, sample_song: Song):
        """Test retrieving a song by ISRC."""
        retrieved = crud_song.song.get_by_isrc(db=db, isrc=sample_song.isrc)

        assert retrieved is not None
        assert retrieved.id == sample_song.id
        assert retrieved.isrc == sample_song.isrc

    def test_get_song_by_isrc_not_found(self, db: Session):
        """Test retrieving a song by non-existent ISRC."""
        retrieved = crud_song.song.get_by_isrc(db=db, isrc="NON-EXISTENT-ISRC")
        assert retrieved is None

    def test_update_song(self, db: Session, sample_song: Song):
        """Test updating a song."""
        update_data = SongUpdate(
            title="Updated Song Title",
            artist="Updated Artist",
            payout_per_play=Decimal("0.010000"),
        )

        updated = crud_song.song.update(db=db, db_obj=sample_song, obj_in=update_data)

        assert updated.title == "Updated Song Title"
        assert updated.artist == "Updated Artist"
        assert updated.payout_per_play == Decimal("0.010000")
        assert updated.isrc == sample_song.isrc  # Should remain unchanged
        assert updated.album == sample_song.album  # Should remain unchanged

    def test_delete_song(self, db: Session, sample_song: Song):
        """Test deleting a song."""
        deleted = crud_song.song.remove(db=db, id=sample_song.id)
        retrieved = crud_song.song.get(db=db, id=sample_song.id)

        assert deleted.id == sample_song.id
        assert retrieved is None

    def test_get_multi_songs(self, db: Session):
        """Test retrieving multiple songs."""
        # Create multiple songs
        songs_data = [
            SongCreate(
                isrc=f"US-TEST-23-1234{i}",
                title=f"Test Song {i}",
                artist=f"Artist {i}",
                album=f"Album {i}",
                payout_per_play=Decimal(f"0.00{i}000"),
                licensing_group=f"Group {i}",
            )
            for i in range(1, 4)
        ]

        for song_data in songs_data:
            crud_song.song.create(db=db, obj_in=song_data)

        # Test pagination
        retrieved = crud_song.song.get_multi(db=db, skip=0, limit=2)
        assert len(retrieved) == 2

        retrieved_all = crud_song.song.get_multi(db=db, skip=0, limit=100)
        assert len(retrieved_all) >= 3  # At least our created songs

    def test_create_or_update_song_create(self, db: Session):
        """Test create_or_update method - create case."""
        song_data = SongCreate(
            isrc="US-NEW-23-99999",
            title="New Song",
            artist="New Artist",
            album="New Album",
            payout_per_play=Decimal("0.007500"),
            licensing_group="New Group",
        )

        result = crud_song.song.create_or_update(db=db, obj_in=song_data)

        assert result.isrc == song_data.isrc
        assert result.title == song_data.title
        assert result.id is not None

    def test_create_or_update_song_update(self, db: Session, sample_song: Song):
        """Test create_or_update method - update case."""
        update_data = SongCreate(
            isrc=sample_song.isrc,  # Same ISRC
            title="Updated Title",
            artist="Updated Artist",
            album="Updated Album",
            payout_per_play=Decimal("0.012000"),
            licensing_group="Updated Group",
        )

        result = crud_song.song.create_or_update(db=db, obj_in=update_data)

        assert result.id == sample_song.id  # Same song
        assert result.title == "Updated Title"
        assert result.artist == "Updated Artist"
        assert result.payout_per_play == Decimal("0.012000")




    def test_unique_isrc_constraint(self, db: Session, sample_song_data: SongCreate):
        """Test that ISRC uniqueness is enforced."""
        # Create first song
        crud_song.song.create(db=db, obj_in=sample_song_data)

        # Try to create another song with same ISRC
        duplicate_data = SongCreate(
            isrc=sample_song_data.isrc,  # Same ISRC
            title="Different Title",
            artist="Different Artist",
            album="Different Album",
            payout_per_play=Decimal("0.010000"),
            licensing_group="Different Group",
        )

        with pytest.raises(Exception):  # Should raise integrity error
            crud_song.song.create(db=db, obj_in=duplicate_data)


    def test_decimal_precision(self, db: Session):
        """Test that decimal values maintain proper precision."""
        song_data = SongCreate(
            isrc="US-DECIMAL-23-55555",
            title="Precise Song",
            artist="Precise Artist",
            album="Precise Album",
            payout_per_play=Decimal("0.12345678"),  # 8 decimal places
            licensing_group="Precise Group",
        )

        song = crud_song.song.create(db=db, obj_in=song_data)
        assert song.payout_per_play == Decimal("0.12345678")

    def test_optional_fields(self, db: Session):
        """Test creating songs with minimal required fields."""
        minimal_song_data = SongCreate(
            isrc="US-MINIMAL-23-44444",
            title=None,
            artist=None,
            album=None,
            payout_per_play=Decimal("0.001000"),
            licensing_group=None,
        )

        song = crud_song.song.create(db=db, obj_in=minimal_song_data)
        assert song.isrc == "US-MINIMAL-23-44444"
        assert song.payout_per_play == Decimal("0.001000")
        assert song.title is None
        assert song.artist is None
        assert song.album is None
        assert song.licensing_group is None
