import logging
from typing import Any

logger = logging.getLogger("dhl_rerouter")

import os

def debug_log_model(obj: Any, stage: str) -> None:
    """
    Log the state of a Pydantic model at INFO level if DEBUG_MODEL env var is set.
    Args:
        obj: The Pydantic model instance (must have .model_dump()).
        stage: A string describing the workflow stage.
    """
    if os.environ.get("DEBUG_MODEL", "").lower() in {"1", "true", "yes"}:
        logger.info("[MODEL DEBUG] %s: %s = %s", stage, obj.__class__.__name__, obj.model_dump())
