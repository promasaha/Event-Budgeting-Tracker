import secrets
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Security
from fastapi.security import APIKeyHeader
from mangum import Mangum
from sqlalchemy.orm import Session

from app import crud, schemas
from app.config import settings
from app.database import get_db

app = FastAPI(
    title="Event Budget API",
    description="Store and manage events (weddings, parties, etc.) along with "
    "their budgets and per-category budget items.",
    version="1.0.0",
)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: Optional[str] = Security(_api_key_header)) -> None:
    if api_key is None or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")


events_router = APIRouter(dependencies=[Depends(require_api_key)])


@app.get("/health", tags=["meta"])
def health_check():
    """Basic liveness check — does not touch the database or require auth."""
    return {"status": "ok"}


@events_router.post(
    "/events", response_model=schemas.EventOut, status_code=201, tags=["events"]
)
def create_event(event_in: schemas.EventCreate, db: Session = Depends(get_db)):
    return crud.create_event(db, event_in)


@events_router.get("/events", response_model=List[schemas.EventOut], tags=["events"])
def list_events(
    name: Optional[str] = Query(
        None, description="Case-insensitive partial match on event name."
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return crud.list_events(db, name=name, skip=skip, limit=limit)


@events_router.get(
    "/events/{event_id}", response_model=schemas.EventOut, tags=["events"]
)
def get_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return event


@events_router.put(
    "/events/{event_id}", response_model=schemas.EventOut, tags=["events"]
)
def update_event(
    event_id: uuid.UUID, event_in: schemas.EventUpdate, db: Session = Depends(get_db)
):
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return crud.update_event(db, event, event_in)


app.include_router(events_router)


# AWS Lambda entry point (API Gateway -> Lambda -> Mangum -> FastAPI).
# Set the Lambda handler to "app.main.handler". Unused for local `uvicorn`
# runs or ECS.
handler = Mangum(app)
