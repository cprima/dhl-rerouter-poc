"""
Carrier base interface for pluggable carrier support.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass, field

@dataclass
class StepResult:
    status: str  # 'success', 'error', etc.
    data: dict | None = None
    errors: list[str] = field(default_factory=list)

class CarrierBase(ABC):
    carrier_name: str

    @abstractmethod
    def check_reroute_availability(
        self,
        tracking_number: str,
        zip_code: str,
        timeout: int = 20
    ) -> dict:
        """
        Return a dict describing reroute availability and shipment status.
        """
        pass

    @abstractmethod
    def reroute_shipment(
        self,
        tracking_number: str,
        zip_code: str,
        custom_location: str,
        highlight_only: bool = True,
        selenium_headless: bool = False,
        timeout: int = 20
    ) -> bool:
        """
        Execute reroute action for the shipment. Returns True if successful.
        """
        pass
