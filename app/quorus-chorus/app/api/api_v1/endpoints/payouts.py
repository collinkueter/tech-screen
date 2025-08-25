from app.api import deps
from fastapi import APIRouter, Depends, HTTPException

from datetime import datetime

from app import crud, models, schemas
from sqlalchemy.orm import Session


router = APIRouter()


@router.get("/{isrc}")
def get_payout_for_song(
    isrc: str,
    play_count: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(deps.get_db),
) -> float:
    song = crud.song.get_by_isrc(db, isrc=isrc)
    
    if not song:
        raise HTTPException(status_code=404, detail=f"Song with ISRC {isrc} not found")
    
    return float(song.payout_per_play * play_count)
