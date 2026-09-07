from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)

    crm_gender: str | None = Field(
        default=None,
        max_length=32,
        validation_alias=AliasChoices("crm_gender", "CRM_Gender"),
        serialization_alias="CRM_Gender",
    )
    crm_age_band: str | None = Field(
        default=None,
        max_length=32,
        validation_alias=AliasChoices("crm_age_band", "CRM_Age_Band"),
        serialization_alias="CRM_Age_Band",
    )
    crm_income_band: str | None = Field(
        default=None,
        max_length=32,
        validation_alias=AliasChoices("crm_income_band", "CRM_Income_Band"),
        serialization_alias="CRM_Income_Band",
    )
    crm_occupation: str | None = Field(
        default=None,
        max_length=100,
        validation_alias=AliasChoices("crm_occupation", "CRM_Occupation"),
        serialization_alias="CRM_Occupation",
    )
    crm_education: str | None = Field(
        default=None,
        max_length=100,
        validation_alias=AliasChoices("crm_education", "CRM_Education"),
        serialization_alias="CRM_Education",
    )
    crm_tobacco_user: str | None = Field(
        default=None,
        max_length=16,
        validation_alias=AliasChoices("crm_tobacco_user", "CRM_Tobacco_User"),
        serialization_alias="CRM_Tobacco_User",
    )
    crm_nonresident_flag: str | None = Field(
        default=None,
        max_length=16,
        validation_alias=AliasChoices("crm_nonresident_flag", "CRM_NonResident_Flag"),
        serialization_alias="CRM_NonResident_Flag",
    )
    crm_existing_plan_flag: str | None = Field(
        default=None,
        max_length=64,
        validation_alias=AliasChoices("crm_existing_plan_flag", "CRM_Existing_Plan_Flag"),
        serialization_alias="CRM_Existing_Plan_Flag",
    )


class CustomerCreate(CustomerBase):
    external_customer_id: str = Field(
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("external_customer_id", "Customer_ID"),
        serialization_alias="Customer_ID",
    )


class CustomerUpdate(CustomerBase):
    external_customer_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("external_customer_id", "Customer_ID"),
        serialization_alias="Customer_ID",
    )


class CustomerRead(CustomerBase):
    id: int
    external_customer_id: str = Field(serialization_alias="Customer_ID")
    created_at: datetime
    updated_at: datetime
    excel_fields: dict[str, Any] | None = Field(default=None, serialization_alias="Excel_Fields")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
