"""
workflow_data_model.py

Unified, logistics-oriented Pydantic data model for the shipment rerouting automation workflow.
See docs/workflow_data_model.md for full documentation and field rationale.
"""
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
    delivery_options: List[str]
    shipment_history: List[str]
    custom_dropoff_input_present: bool
    protocol: Dict[str, Any]
    last_checked: Optional[str]
    status_code: Optional[int]  # HTTP/TCP style codes

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
    provider: TransportProviderInfo
    notification: Optional[ConsignmentNotification] = None
    tracking: Optional[ShipmentTrackingInfo] = None
    recipient_availability: Optional[RecipientAvailability] = None
    intervention: Optional[DeliveryInterventionResult] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    workflow_status: str = "pending"  # "pending", "in_progress", "completed", "failed"
    workflow_code: Optional[int] = None
    updated_at: Optional[str] = None
