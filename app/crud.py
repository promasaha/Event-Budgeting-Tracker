import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models, schemas


def create_event(db: Session, event_in: schemas.EventCreate) -> models.Event:
    event = models.Event(
        name=event_in.name,
        event_type=event_in.event_type.value,
        event_date=event_in.event_date,
        location=event_in.location,
        host_name=event_in.host_name,
        organizer_email=event_in.organizer_email,
        collaborator_emails=list(event_in.collaborator_emails),
        guest_count=event_in.guest_count,
        total_budget=event_in.total_budget,
        notes=event_in.notes,
        budget_items=[models.BudgetItem(**item.model_dump()) for item in event_in.budget_items],
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: uuid.UUID) -> Optional[models.Event]:
    stmt = (
        select(models.Event)
        .options(selectinload(models.Event.budget_items))
        .where(models.Event.id == event_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def list_events(
    db: Session, name: Optional[str] = None, skip: int = 0, limit: int = 100
) -> List[models.Event]:
    stmt = select(models.Event).options(selectinload(models.Event.budget_items))
    if name:
        # Case-insensitive partial match, since exact name uniqueness was not
        # required — e.g. "Sam's Wedding" matches a query of "wedding".
        stmt = stmt.where(models.Event.name.ilike(f"%{name}%"))
    stmt = stmt.order_by(models.Event.created_at.desc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def update_event(
    db: Session, event: models.Event, event_in: schemas.EventUpdate
) -> models.Event:
    event.name = event_in.name
    event.event_type = event_in.event_type.value
    event.event_date = event_in.event_date
    event.location = event_in.location
    event.host_name = event_in.host_name
    event.organizer_email = event_in.organizer_email
    event.collaborator_emails = list(event_in.collaborator_emails)
    event.guest_count = event_in.guest_count
    event.total_budget = event_in.total_budget
    event.notes = event_in.notes

    # Full replace of budget items (PUT semantics): the old set is dropped and
    # the new one inserted. cascade="all, delete-orphan" on the relationship
    # (see models.py) takes care of deleting the orphaned rows.
    event.budget_items = [
        models.BudgetItem(**item.model_dump()) for item in event_in.budget_items
    ]

    db.commit()
    db.refresh(event)
    return event
