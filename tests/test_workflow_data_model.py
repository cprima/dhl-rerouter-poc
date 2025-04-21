import pytest
from pydantic import ValidationError
from dhl_rerouter_poc.workflow_data_model import (
    TransportProviderInfo,
    ConsignmentNotification,
    ShipmentTrackingInfo,
    AbsenceWindow,
    RecipientAvailability,
    DeliveryInterventionResult,
    ShipmentLifecycle,
)

# --- TransportProviderInfo ---
def test_transport_provider_info_basic():
    info = TransportProviderInfo(name="DHL", tracking_number="JJD123456789", extra={"service": "Express"})
    assert info.name == "DHL"
    assert info.tracking_number == "JJD123456789"
    assert info.extra["service"] == "Express"

# --- ConsignmentNotification ---
def test_consignment_notification_body_length():
    body = "x" * 4096
    notif = ConsignmentNotification(normalized_body=body)
    assert notif.normalized_body == body
    assert notif.body_truncated is False
    with pytest.raises(ValidationError):
        ConsignmentNotification(normalized_body="x" * 5000)

def test_consignment_notification_metadata():
    notif = ConsignmentNotification(
        normalized_body="Test",
        subject="Your package",
        sender="dhl@example.com",
        received_at="2025-04-21T11:00:00Z",
        message_id="abc123",
        source="imap"
    )
    assert notif.subject == "Your package"
    assert notif.sender == "dhl@example.com"
    assert notif.message_id == "abc123"
    assert notif.source == "imap"

# --- ShipmentTrackingInfo ---
def test_tracking_info_status_and_protocol():
    tracking = ShipmentTrackingInfo(
        status="delivered",
        delivered=True,
        delivery_date="2025-04-22",
        delivery_status="Delivered",
        delivery_options=["Pickup", "Neighbor"],
        shipment_history=["2025-04-20: In transit", "2025-04-22: Delivered"],
        custom_dropoff_input_present=False,
        protocol={"timestamp": "2025-04-22T09:00:00Z", "status": "ok"},
        last_checked="2025-04-22T09:00:00Z",
        status_code=200,
    )
    assert tracking.status == "delivered"
    assert tracking.protocol["status"] == "ok"
    assert tracking.status_code == 200

def test_tracking_info_unknown():
    tracking = ShipmentTrackingInfo(
        status="unknown",
        delivered=False,
        delivery_date=None,
        delivery_status=None,
        delivery_options=[],
        shipment_history=[],
        custom_dropoff_input_present=False,
        protocol={},
        last_checked=None,
        status_code=404,
    )
    assert tracking.status == "unknown"
    assert tracking.status_code == 404

# --- AbsenceWindow ---
def test_absence_window_fields():
    window = AbsenceWindow(
        event_id="evt123",
        summary="Vacation",
        start="2025-04-21T00:00:00Z",
        end="2025-04-25T23:59:59Z",
        notes="Out of office",
        source="work_calendar"
    )
    assert window.event_id == "evt123"
    assert window.source == "work_calendar"

# --- RecipientAvailability ---
def test_recipient_availability_multi_day_absence():
    window = AbsenceWindow(
        event_id="evt456",
        summary="Conference",
        start="2025-04-20",
        end="2025-04-24",
        notes=None,
        source="primary_calendar"
    )
    avail = RecipientAvailability(
        delivery_date="2025-04-23",
        is_away=True,
        overlapping_absences=[window],
        sources_checked=["primary_calendar", "work_calendar"]
    )
    assert avail.is_away is True
    assert avail.delivery_date == "2025-04-23"
    assert avail.overlapping_absences[0].summary == "Conference"
    assert "work_calendar" in avail.sources_checked

# --- DeliveryInterventionResult ---
def test_intervention_result_failure_with_retries():
    intervention = DeliveryInterventionResult(
        attempted=True,
        success=False,
        error="Timeout",
        timestamp="2025-04-22T10:00:00Z",
        attempts=3,
        status_code=503,
        detail="Carrier site not responding"
    )
    assert intervention.attempts == 3
    assert intervention.success is False
    assert intervention.status_code == 503

# --- ShipmentLifecycle ---
def test_shipment_lifecycle_happy_path():
    provider = TransportProviderInfo(name="DHL", tracking_number="JJD000123456")
    notif = ConsignmentNotification(normalized_body="Your package is on the way.")
    tracking = ShipmentTrackingInfo(
        status="in_transit",
        delivered=False,
        delivery_date="2025-04-24",
        delivery_status="In transit",
        delivery_options=["Pickup"],
        shipment_history=["2025-04-22: Shipped"],
        custom_dropoff_input_present=True,
        protocol={},
        last_checked="2025-04-22T11:00:00Z",
        status_code=200,
    )
    avail = RecipientAvailability(
        delivery_date="2025-04-24",
        is_away=False,
        overlapping_absences=[],
        sources_checked=["primary_calendar"]
    )
    intervention = DeliveryInterventionResult(
        attempted=True,
        success=True,
        error=None,
        timestamp="2025-04-22T12:00:00Z",
        attempts=1,
        status_code=200,
        detail="Reroute successful"
    )
    shipment = ShipmentLifecycle(
        provider=provider,
        notification=notif,
        tracking=tracking,
        recipient_availability=avail,
        intervention=intervention,
        meta={"test": True},
        workflow_status="completed",
        workflow_code=200,
        updated_at="2025-04-22T12:01:00Z"
    )
    assert shipment.workflow_status == "completed"
    assert shipment.meta["test"] is True
    assert shipment.intervention.success is True

# --- Serialization/Deserialization ---
def test_serialization_roundtrip():
    provider = TransportProviderInfo(name="UPS", tracking_number="1Z999AA10123456784")
    shipment = ShipmentLifecycle(provider=provider)
    data = shipment.model_dump()
    shipment2 = ShipmentLifecycle.model_validate(data)
    assert shipment2.provider.name == "UPS"
    assert shipment2 == shipment

# --- Edge Cases ---
def test_minimal_lifecycle():
    provider = TransportProviderInfo(name="DHL", tracking_number="JJD000000000")
    shipment = ShipmentLifecycle(provider=provider)
    assert shipment.provider.tracking_number == "JJD000000000"
    assert shipment.notification is None
    assert shipment.workflow_status == "pending"

# --- Invalid Data ---
def test_invalid_provider_missing_fields():
    with pytest.raises(ValidationError):
        TransportProviderInfo(name="DHL")  # missing tracking_number

