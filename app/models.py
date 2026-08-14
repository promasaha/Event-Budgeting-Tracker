import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    event_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    host_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    organizer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    collaborator_emails: Mapped[List[str]] = mapped_column(
        ARRAY(String(255)), nullable=False, default=list
    )
    guest_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    total_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    budget_items: Mapped[List["BudgetItem"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="BudgetItem.category",
    )


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    budgeted_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    actual_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    vendor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    paid: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    event: Mapped["Event"] = relationship(back_populates="budget_items")
