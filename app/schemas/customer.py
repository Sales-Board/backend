from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):

    crm_gender: str | None = Field(
        default=None,
        max_length=32,
        alias="CRM_Gender",
        validation_alias=AliasChoices("CRM_Gender", "crm_gender"),
    )
    crm_age_band: str | None = Field(
        default=None,
        max_length=32,
        alias="CRM_Age_Band",
        validation_alias=AliasChoices("CRM_Age_Band", "crm_age_band"),
    )
    crm_income_band: str | None = Field(
        default=None,
        max_length=32,
        alias="CRM_Income_Band",
        validation_alias=AliasChoices("CRM_Income_Band", "crm_income_band"),
    )
    crm_occupation: str | None = Field(
        default=None,
        max_length=100,
        alias="CRM_Occupation",
        validation_alias=AliasChoices("CRM_Occupation", "crm_occupation"),
    )
    crm_education: str | None = Field(
        default=None,
        max_length=100,
        alias="CRM_Education",
        validation_alias=AliasChoices("CRM_Education", "crm_education"),
    )
    crm_tobacco_user: str | None = Field(
        default=None,
        max_length=16,
        alias="CRM_Tobacco_User",
        validation_alias=AliasChoices("CRM_Tobacco_User", "crm_tobacco_user"),
    )
    crm_nonresident_flag: str | None = Field(
        default=None,
        max_length=16,
        alias="CRM_NonResident_Flag",
        validation_alias=AliasChoices("CRM_NonResident_Flag", "crm_nonresident_flag"),
    )
    crm_existing_plan_flag: str | None = Field(
        default=None,
        max_length=64,
        alias="CRM_Existing_Plan_Flag",
        validation_alias=AliasChoices("CRM_Existing_Plan_Flag", "crm_existing_plan_flag"),
    )


class CustomerCreate(CustomerBase):
    external_customer_id: str = Field(
        min_length=1,
        max_length=64,
        alias="Customer_ID",
        validation_alias=AliasChoices("Customer_ID", "external_customer_id"),
    )


class CustomerUpdate(CustomerBase):
    external_customer_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        alias="Customer_ID",
        validation_alias=AliasChoices("Customer_ID", "external_customer_id"),
    )


class CustomerRead(CustomerBase):
    id: int
    external_customer_id: str = Field(alias="Customer_ID", validation_alias=AliasChoices("Customer_ID", "external_customer_id"))
    created_at: datetime
    updated_at: datetime
    excel_fields: dict[str, Any] | None = Field(default=None, serialization_alias="Excel_Fields")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
