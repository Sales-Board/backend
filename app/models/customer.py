from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_customer_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    crm_gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    crm_age_band: Mapped[str | None] = mapped_column(String(32), nullable=True)
    crm_income_band: Mapped[str | None] = mapped_column(String(32), nullable=True)
    crm_occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    crm_education: Mapped[str | None] = mapped_column(String(100), nullable=True)
    crm_tobacco_user: Mapped[str | None] = mapped_column(String(16), nullable=True)
    crm_nonresident_flag: Mapped[str | None] = mapped_column(String(16), nullable=True)
    crm_existing_plan_flag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    excel_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
