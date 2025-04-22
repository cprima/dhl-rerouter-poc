"""
workflow_data_model.py

Unified, logistics-oriented Pydantic data model for the shipment rerouting automation workflow.
See docs/workflow_data_model.md for full documentation and field rationale.
"""
import uuid
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TransportProviderInfo(BaseModel):
    """
    Information about the carrier/transport provider for a shipment.
    Use .is_supported() to check if the carrier is currently supported by the automation workflow.
    """
    name: str  # e.g. "DHL", "UPS", "FedEx"
    tracking_number: str
    extra: Dict[str, Any] = Field(default_factory=dict)

    def is_supported(self) -> bool:
        """Return True if this carrier is supported by the workflow."""
        # In the future, this could check a registry or config
        return self.name.upper() == "DHL"

class ConsignmentNotification(BaseModel):
    subject: Optional[str] = None
    sender: Optional[str] = None
    received_at: Optional[str] = None  # ISO timestamp
    normalized_body: str = Field(..., max_length=4096)
    body_truncated: bool = False
    message_id: Optional[str] = None
    source: Optional[str] = None  # e.g. "imap", "api", "manual"

class ShipmentTrackingInfo(BaseModel):
    status: str  # e.g. "in_transit", "delivered", "unknown", "error"
    delivered: bool
    delivery_date: Optional[str]  # ISO date
    delivery_status: Optional[str]
    delivery_options: list[str]
    shipment_history: list[str]
    custom_dropoff_input_present: bool
    protocol: dict[str, Any]
    last_checked: Optional[str]
    status_code: Optional[int]  # HTTP/TCP style codes

    @classmethod
    def set_status(cls, delivery_status: str | None, delivery_date: str | None) -> str:
        """
        Determine the shipment status string based on delivery_status and delivery_date.
        Returns one of: "delivered", "in_transit", "unknown", or "error".
        """
        if delivery_status:
            import re
            norm = delivery_status.strip().lower()
            # DHL-specific: 'Order data transmitted electronically.' (with or without trailing period/whitespace) means in_transit
            if re.fullmatch(r"order data transmitted electronically\.?", norm):
                import logging
                logging.getLogger("dhl_test").info("Matched DHL 'Order data transmitted electronically.' as in_transit")
                return "in_transit"
            if "delivery successful" in norm or "delivered" in norm:
                return "delivered"
            if "in transit" in norm:
                return "in_transit"
            if "error" in norm:
                return "error"
        if delivery_date:
            # If date is in the past (and no explicit delivered status), may be delivered
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(delivery_date)
                if dt < datetime.now(dt.tzinfo):
                    return "delivered"
            except Exception:
                pass
        return "unknown"

    @classmethod
    def from_extracted_data(
        cls,
        delivery_status: str | None,
        parsed_date: str | None,
        delivery_options: list[str],
        shipment_history: list[str],
        custom_dropoff_input_present: bool,
        protocol: dict[str, Any],
        last_checked: str | None = None,
        status_code: int | None = None,
    ) -> "ShipmentTrackingInfo":
        """
        Construct a ShipmentTrackingInfo instance from extracted page data.
        Sets status using set_status, delivered as status == 'delivered', and delivery_date only if status is 'delivered'.
        """
        status = cls.set_status(delivery_status, parsed_date)
        delivered = status == "delivered"
        delivery_date = parsed_date if status == "delivered" else None
        return cls(
            status=status,
            delivered=delivered,
            delivery_date=delivery_date,
            delivery_status=delivery_status,
            delivery_options=delivery_options,
            shipment_history=shipment_history,
            custom_dropoff_input_present=custom_dropoff_input_present,
            protocol=protocol,
            last_checked=last_checked,
            status_code=status_code,
        )

class AbsenceWindow(BaseModel):
    event_id: Optional[str]
    summary: Optional[str]
    start: str  # ISO datetime or date
    end: str    # ISO datetime or date
    notes: Optional[str]
    source: Optional[str]  # e.g. "primary_calendar", "work_calendar", "external_api"

class RecipientAvailability(BaseModel):
    delivery_date: str  # ISO date checked
    is_away: bool
    overlapping_absences: List[AbsenceWindow]
    sources_checked: List[str]  # All calendar sources checked

class DeliveryInterventionResult(BaseModel):
    attempted: bool
    success: bool
    error: Optional[str]
    timestamp: Optional[str]
    attempts: int = 1  # Number of automation attempts
    status_code: Optional[int]  # HTTP/TCP style codes
    detail: Optional[str]

class ShipmentLifecycle(BaseModel):
    run_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    provider: TransportProviderInfo
    notification: Optional[ConsignmentNotification] = None
    tracking: Optional[ShipmentTrackingInfo] = None
    recipient_availability: Optional[RecipientAvailability] = None
    intervention: Optional[DeliveryInterventionResult] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    workflow_status: str = "pending"  # "pending", "in_progress", "completed", "failed"
    workflow_code: Optional[int] = None
    updated_at: Optional[str] = None
