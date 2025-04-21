from pydantic import BaseModel
from typing import List

class RerouteTestScenario(BaseModel):
    tracking_number: str
    reroute_available: bool
    calendar_away: bool
    expected_reroute: bool

# Optional: loader for YAML
import yaml
from pathlib import Path

def load_scenarios(yaml_path: str) -> List[RerouteTestScenario]:
    with open(yaml_path, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)
    return [RerouteTestScenario.model_validate(item) for item in raw]
