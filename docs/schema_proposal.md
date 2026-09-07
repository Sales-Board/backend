# Proposed Database Schema (Normalized)

## Core Reference Tables

1. `products`
2. `campaigns`
3. `agents`
4. `departments`

## Customer Domain

1. `customers`
- `id` (pk)
- `external_customer_id` (unique; maps from `Customer_ID`)
- `created_at`, `updated_at`

2. `customer_profiles`
- `id` (pk)
- `customer_id` (fk -> customers.id)
- demographics and profile attributes

## Lead Domain (Central)

1. `leads`
- `id` (pk)
- `customer_id` (fk)
- `campaign_id` (fk, nullable)
- `product_id` (fk, nullable)
- `source_channel`, `source_medium`, `source_platform`, `utm_source`, `utm_medium`, `utm_campaign`
- `status`, `priority`
- `created_at`, `updated_at`

2. `lead_status_history`
- `id` (pk)
- `lead_id` (fk)
- `status`
- `changed_at`
- `reason`

3. `lead_assignments`
- `id` (pk)
- `lead_id` (fk)
- `assigned_to_agent_id` (fk, nullable)
- `assigned_to_department_id` (fk, nullable)
- `assignment_reason`
- `assigned_at`
- `is_current`

4. `lead_transfers`
- `id` (pk)
- `lead_id` (fk)
- `from_agent_id` / `to_agent_id`
- `from_department_id` / `to_department_id`
- `transfer_reason`
- `transferred_at`

5. `lead_events`
- `id` (pk)
- `lead_id` (fk)
- `event_type`
- `event_time`
- `event_payload` (jsonb)

## Engagement Domain

1. `engagement_events`
- `id` (pk)
- `lead_id` (fk)
- `customer_id` (fk)
- `channel` (whatsapp/rcs/email/website)
- `metric_type` (sent/delivered/read/clicked/replied/failed)
- `metric_value`
- `event_time`

## Website Journey Domain

1. `website_events`
- `id` (pk)
- `lead_id` (fk)
- `customer_id` (fk)
- `event_name`
- `step_name`, `step_number`
- `device_type`
- `is_repeat_visitor`
- `metadata` (jsonb)
- `event_time`

## Calls Domain

1. `calls`
2. `call_transcripts`
3. `call_analyses`

## AI and Decision Domain

1. `model_versions`
2. `predictions`
3. `prediction_logs`
4. `recommendations`
5. `next_best_actions`

## Tasks Domain

1. `tasks`
2. `followups`

## Outcome and Audit

1. `lead_outcomes`
2. `audit_logs`

## Indexing Priorities

1. `leads(status, priority, created_at)`
2. `leads(campaign_id)`
3. `lead_events(lead_id, event_time desc)`
4. `website_events(lead_id, event_time desc)`
5. `engagement_events(lead_id, channel, event_time desc)`
6. `predictions(lead_id, model_type, predicted_at desc)`
