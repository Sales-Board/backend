from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
        validation_alias=AliasChoices("name", "CRM_Product_Name"),
        serialization_alias="CRM_Product_Name",
    )


class ProductCreate(ProductBase):
    code: str = Field(
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("code", "CRM_Product_Code"),
        serialization_alias="CRM_Product_Code",
    )


class ProductUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=150)


class ProductRead(ProductBase):
    id: int
    code: str = Field(serialization_alias="CRM_Product_Code")
    created_at: datetime
    updated_at: datetime
    excel_fields: dict[str, Any] | None = Field(default=None, serialization_alias="Excel_Fields")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
