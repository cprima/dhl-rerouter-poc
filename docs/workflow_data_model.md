# Unified Workflow Data Model

## Purpose
This document describes the unified, automation-focused data model used to represent the lifecycle of a shipment as it passes through the rerouting automation workflow. It is designed for multi-carrier support, traceability, and robust automation.

## Context
- **Who should read this?**
  - Developers extending the automation workflow
  - Testers writing or reviewing end-to-end tests
  - Integrators adding new carriers, calendar sources, or notification channels
- **Where is this model used?**
  - Throughout the core automation pipeline (from email/notification ingestion to reroute execution)

## Model Overview

### Top-Level: `ShipmentLifecycle`
Represents the entire lifecycle and automation context for a single shipment/consignment.

**Fields:**
- `provider`: Carrier/logistics provider information
- `notification`: Notification or consignment message context
- `tracking`: Structured tracking status and carrier data
- `recipient_availability`: Absence/availability information
- `intervention`: Outcome of delivery intervention/reroute
- `meta`: Arbitrary extra data
- `workflow_status`: Current state of the workflow (pending, in_progress, completed, failed)
- `workflow_code`: Numeric status code (inspired by HTTP/TCP)
- `updated_at`: Last update timestamp

### Submodels

#### `TransportProviderInfo`
- `name`: Carrier name (e.g., DHL, UPS)
- `tracking_number`: Unique tracking/consignment number
- `extra`: Carrier-specific fields

#### `ConsignmentNotification`
- `subject`, `sender`, `received_at`: Metadata
- `normalized_body`: Cleaned, size-limited message body
- `body_truncated`: Was the body truncated?
- `message_id`: Unique message identifier
- `source`: Origin of the notification (IMAP, API, manual, etc.)

#### `ShipmentTrackingInfo`
- `status`: High-level status (in_transit, delivered, unknown, error)
- `delivered`: Boolean
- `delivery_date`, `delivery_status`, `delivery_options`, `shipment_history`
- `custom_dropoff_input_present`: Boolean
- `protocol`: Raw protocol/errors from carrier
- `last_checked`: Timestamp
- `status_code`: Numeric status code (HTTP/TCP style)

#### `AbsenceWindow`
- `event_id`, `summary`, `start`, `end`, `notes`: Event details
- `source`: Calendar or system that provided the event

#### `RecipientAvailability`
- `delivery_date`: The date being checked
- `is_away`: Boolean
- `overlapping_absences`: List of `AbsenceWindow`s
- `sources_checked`: List of all calendar sources checked

#### `DeliveryInterventionResult`
- `attempted`, `success`, `error`, `timestamp`
- `attempts`: Number of automation attempts
- `status_code`: Numeric status code (HTTP/TCP style)
- `detail`: Human-readable diagnostic info

## Best Practices & Design Inspirations
- **Domain-driven naming:** All classes use logistics terminology for clarity and extensibility.
- **Traceability:** All data sources and state changes are referenced and timestamped.
- **Automation focus:** The model supports retries, error codes, and multi-source integration.
- **Extensibility:** Use of `meta` and `extra` fields for future-proofing.

## Example Usage
```python
from workflow_data_model import ShipmentLifecycle, TransportProviderInfo, ...

shipment = ShipmentLifecycle(
    provider=TransportProviderInfo(name="DHL", tracking_number="JJD..."),
    ...
)
```

## Change History
- v0.1: Initial version, aligned with automation and logistics best practices.

---

*This document should be updated whenever the workflow data model changes or is extended.*
