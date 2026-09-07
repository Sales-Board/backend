from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)


class CustomerCreate(CustomerBase):
    external_customer_id: str = Field(min_length=1, max_length=64)


class CustomerUpdate(CustomerBase):
    external_customer_id: str | None = Field(default=None, min_length=1, max_length=64)


class CustomerRead(CustomerBase):
    id: int
    external_customer_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
