import logging
import os
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger("dhl_rerouter")

def debug_log_model(obj: Any, stage: str, run_id: Optional[UUID] = None) -> None:
    """
    Log the state of a Pydantic model at INFO level if DEBUG_MODEL env var is set.
    Args:
        obj: The Pydantic model instance (must have .model_dump()).
        stage: A string describing the workflow stage.
        run_id: Optional workflow/run UUID for cross-log correlation.
    """
    if os.environ.get("DEBUG_MODEL", "").lower() in {"1", "true", "yes"}:
        if run_id is not None:
            logger.info("[MODEL DEBUG] [run_id=%s] %s: %s = %s", run_id, stage, obj.__class__.__name__, obj.model_dump())
        else:
            logger.info("[MODEL DEBUG] %s: %s = %s", stage, obj.__class__.__name__, obj.model_dump())
