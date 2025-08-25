from app.api import deps
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
import logging

from app import crud, schemas, services

router = APIRouter()


@router.get("/{isrc}", response_model=schemas.Song)
def get_song_by_isrc(isrc: str, db: Session = Depends(deps.get_db)) -> schemas.Song:
    song = crud.song.get_by_isrc(db, isrc=isrc)

    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    return schemas.Song.from_orm(song)


@router.post("/upload", status_code=200, response_model=dict)
def upload_songs_file(file: UploadFile, db: Session = Depends(deps.get_db)) -> dict:
    """
    Upload and process an IRA file to ingest songs.

    Accepts an IRA file, processes it through the SongIngestionService,
    and returns a summary of the ingestion results.
    """
    # Validate file type
    if not file.filename or not file.filename.endswith((".txt", ".ira")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a .txt or .ira file.",
        )

    try:
        # Process the uploaded file
        report = services.SongIngestionService.load_from_file(file.file, db=db)

        # Return comprehensive response
        return {
            "message": "File processed successfully",
            "filename": file.filename,
            "summary": {
                "total_entries": report.total_entries,
                "successful_matches": report.successful_matches,
                "failed_matches": report.failed_matches,
                "database_errors": report.database_errors,
                "songs_created_or_updated": len(report.songs_created),
                "success_rate_percent": round(
                    (
                        (report.successful_matches / report.total_entries * 100)
                        if report.total_entries > 0
                        else 0
                    ),
                    1,
                ),
            },
            "songs_processed": report.songs_created,
            "errors": report.errors if report.errors else [],
        }

    except Exception as e:
        logging.error(f"Error processing uploaded file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
