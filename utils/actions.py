from dataclasses import dataclass
from typing import Literal, Dict, Any
import pandas as pd

ActionType = Literal["cover_crop", "buffer_strip", "reduced_tillage", "grazing", "hedgerow_planting"]

@dataclass
class FieldAction:
    field_id: str
    action_type: ActionType
    intensity: float  # 0–1 or ha covered
    year: int

def extract_actions_from_df(df: pd.DataFrame) -> list[FieldAction]:
    actions: list[FieldAction] = []
    for _, row in df.iterrows():
        fid = str(row.get("field_id", row["field_name"]))
        year = int(row["year"])

        if row.get("cover_crop_planted_yes_no", "").lower() == "yes":
            actions.append(FieldAction(field_id=fid, action_type="cover_crop", intensity=1.0, year=year))

        if row.get("reduced_tillage_yes_no", "").lower() == "yes":
            actions.append(FieldAction(field_id=fid, action_type="reduced_tillage", intensity=1.0, year=year))

        # later: buffer strips, grazing, etc.

    return actions
