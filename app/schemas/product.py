from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
        alias="CRM_Product_Name",
        validation_alias=AliasChoices("CRM_Product_Name", "name"),
    )


class ProductCreate(ProductBase):
    code: str = Field(
        min_length=1,
        max_length=64,
        alias="CRM_Product_Code",
        validation_alias=AliasChoices("CRM_Product_Code", "code"),
    )


class ProductUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=150)


class ProductRead(ProductBase):
    id: int
    code: str = Field(alias="CRM_Product_Code", validation_alias=AliasChoices("CRM_Product_Code", "code"))
    created_at: datetime
    updated_at: datetime
    excel_fields: dict[str, Any] | None = Field(default=None, serialization_alias="Excel_Fields")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
