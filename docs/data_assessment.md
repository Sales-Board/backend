# Dataset Assessment

## Sheets

1. dataset
2. data_dictionary
3. label_definition

## Primary Working Sheet

The `dataset` sheet contains 1500 records plus one header row.

## Candidate Business Key

- `Customer_ID` (candidate key for customer identity; may have repeated records in future loads)

## Domain-Oriented Column Grouping

1. Lead Source and Campaign Context
- `CRM_Channel`
- `CRM_Department`
- `CRM_Lead_Type`
- `CRM_Lead_Source`
- `CRM_Data_Medium`
- `CRM_Source`
- `CRM_Data_Source_Platform`
- `CRM_UTM_Source`
- `CRM_UTM_Medium`
- `CRM_UTM_Campaign`
- `CRM_Lead_Create_Hour`
- `CRM_Lead_Create_DayOfWeek`
- `CRM_Lead_Create_Weekend`
- `CRM_Lead_Create_Month`

2. Customer Profile
- `CRM_Gender`
- `CRM_Age_Band`
- `CRM_Income_Band`
- `CRM_Occupation`
- `CRM_Education`
- `CRM_Tobacco_User`
- `CRM_NonResident_Flag`
- `CRM_Existing_Plan_Flag`

3. Product Context
- `CRM_Product_Code`
- `CRM_Product_Name`
- `WEB_Plan_Type`
- `WEB_Plan_Variant`
- `WEB_Quoted_Price`
- `WEB_Coverage_Amount`
- `WEB_Payment_Frequency`

4. Call and Contact Activity
- `CRM_Contact_Count`
- `CRM_NonContact_Count`
- `CRM_No_Of_Attempts`
- `CDR_Total_Calls`
- `CDR_Connected_Calls`
- `CDR_Connect_Rate`
- `CDR_Total_Talk_Sec`
- `CDR_Avg_Talk_Sec`
- `CDR_Max_Talk_Sec`
- `CDR_Distinct_Call_Days`
- `CDR_Distinct_Agents`
- `CDR_Callbacks_Scheduled`
- `CDR_Inbound_Calls`
- `CDR_Top_Call_Status`
- `CDR_Top_Q_Type`
- `CDR_First_Call_Delay_Days`
- `CDR_Call_Span_Days`

5. Messaging Engagement
- `MSG_Campaigns_Targeted`
- `MSG_Sent`
- `MSG_Delivered`
- `MSG_Read`
- `MSG_Clicked`
- `MSG_Replied`
- `MSG_Failed`
- `MSG_Engaged`

6. Website and Journey Events
- `WEB_Tracked`
- `Visits`
- `Page_Views`
- `Total_Seconds_Spent`
- Event flags `ev_*`
- `WEB_Step_Name`
- `WEB_Step_Number`
- `WEB_New_Vs_Repeat`
- `WEB_Last_Touch_Channel`
- `WEB_UTM_Source`
- `WEB_Device_Type`

7. Outcome and Label Signals
- `Label_Source_Disposition`
- `Label_Source_Lead_Status`
- `Label_Basis`
- `LABEL_Customer_Validity`

## Candidate Relationships

1. Campaign -> Lead
2. Lead -> Customer
3. Lead -> Engagement Events
4. Lead -> Call Summary / Call Events
5. Lead -> Website Events
6. Lead -> Outcome / Labels

## Targets and Leakage Notes

1. Primary target candidate: `LABEL_Customer_Validity` (4-class label)
2. Potential leakage risk columns:
- `CRM_Has_Application_No`
- `CRM_Has_Payment_Flag`
- `ev_Payment_Success`
- `ev_Payment_Failure`
- `Label_Source_Disposition`
- `Label_Source_Lead_Status`
3. Rule: these fields should be excluded from features for early-stage prediction tasks unless the prediction timestamp is after these events.
