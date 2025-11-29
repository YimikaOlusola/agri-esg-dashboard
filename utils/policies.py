from dataclasses import dataclass
from typing import Protocol, Dict, Any, List
from .land_model import Farm
from .actions import FieldAction

class Policy(Protocol):
    name: str
    slug: str

    def score_farm(self, farm: Farm, actions: List[FieldAction]) -> Dict[str, Any]:
        ...

@dataclass
class SFIPolicy:
    name: str = "Sustainable Farming Incentive"
    slug: str = "sfi"

    def score_farm(self, farm: Farm, actions: List[FieldAction]) -> Dict[str, Any]:
        # simple example – you can reuse your current SFI logic
        soil_actions = [a for a in actions if a.action_type in ("cover_crop", "reduced_tillage")]
        soil_pct = min(100.0, len(soil_actions) / max(len(farm.fields), 1) * 100)

        return {
            "policy": self.slug,
            "policy_name": self.name,
            "soil_score_pct": soil_pct,
            # later: £ payment estimates, risk flags, etc.
        }
@dataclass
class BNGPolicy(Policy): ...
@dataclass
class CSPolicy(Policy): ...
@dataclass
class CarbonMarketPolicy(Policy): ...
