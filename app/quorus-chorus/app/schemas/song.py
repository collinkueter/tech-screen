from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional


class SongBase(BaseModel):
    isrc: str = Field(..., min_length=1, max_length=16, description="International Standard Recording Code")
    album: Optional[str] = Field(None, max_length=150, description="Album name")
    artist: Optional[str] = Field(None, max_length=150, description="Artist name")
    title: Optional[str] = Field(None, max_length=150, description="Song title")
    payout_per_play: Decimal = Field(..., ge=0, description="Payout amount per play")
    licensing_group: Optional[str] = Field(None, max_length=150, description="Licensing group")


class SongCreate(SongBase):
    pass


class SongUpdate(BaseModel):
    isrc: Optional[str] = Field(None, min_length=1, max_length=16)
    album: Optional[str] = Field(None, max_length=150)
    artist: Optional[str] = Field(None, max_length=150)
    title: Optional[str] = Field(None, max_length=150)
    payout_per_play: Optional[Decimal] = Field(None, ge=0)
    licensing_group: Optional[str] = Field(None, max_length=150)


class SongInDbBase(SongBase):
    id: int

    class Config:
        from_attributes = True


class Song(SongInDbBase):
    pass
