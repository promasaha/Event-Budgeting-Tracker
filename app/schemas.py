import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EventType(str, Enum):
    wedding = "wedding"
    birthday = "birthday"
    anniversary = "anniversary"
    corporate = "corporate"
    baby_shower = "baby_shower"
    graduation = "graduation"
    other = "other"


# ---- Budget items ----


class BudgetItemBase(BaseModel):
    category: str = Field(..., max_length=100, examples=["Venue", "Catering", "Photography"])
    description: Optional[str] = Field(None, max_length=255)
    budgeted_amount: Decimal = Field(..., ge=0, examples=[2500.00])
    actual_amount: Optional[Decimal] = Field(None, ge=0)
    vendor_name: Optional[str] = Field(None, max_length=255)
    paid: bool = False


class BudgetItemCreate(BudgetItemBase):
    pass


class BudgetItemOut(BudgetItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---- Events ----


class EventBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Alex & Sam's Wedding"])
    event_type: EventType = EventType.other
    event_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=255)
    host_name: Optional[str] = Field(None, max_length=255)
    organizer_email: EmailStr = Field(
        ..., description="Main organizer / point of contact for this event."
    )
    collaborator_emails: List[EmailStr] = Field(
        default_factory=list,
        description="Other people with visibility into / input on this event.",
    )
    guest_count: Optional[int] = Field(None, ge=0)
    total_budget: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class EventCreate(EventBase):
    budget_items: List[BudgetItemCreate] = Field(default_factory=list)


class EventUpdate(EventBase):
    """Body for PUT /events/{event_id}. This is a full replace: any field you
    omit falls back to its default (e.g. omitting budget_items clears them),
    matching standard PUT semantics rather than a partial PATCH."""

    budget_items: List[BudgetItemCreate] = Field(default_factory=list)


class EventOut(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    budget_items: List[BudgetItemOut] = Field(default_factory=list)
