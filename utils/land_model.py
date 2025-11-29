# utils/land_model.py
from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd

@dataclass
class Field:
    field_id: str
    name: str
    area_ha: float
    crop_type: str | None = None
    soil_type: str | None = None

@dataclass
class Farm:
    farm_id: str
    name: str
    fields: List[Field]
    raw_df: pd.DataFrame     # full activity table
    kpi_df: pd.DataFrame     # after compute_kpis

    def total_area(self) -> float:
        return sum(f.area_ha for f in self.fields)
def build_farm_from_df(df: pd.DataFrame, farm_id: str) -> Farm:
    farm_rows = df[df["farm_id"] == farm_id]

    fields = []
    for name, group in farm_rows.groupby("field_name"):
        fields.append(
            Field(
                field_id=str(group["field_id"].iloc[0]) if "field_id" in group.columns else name,
                name=name,
                area_ha=float(group["field_area_ha"].iloc[0]),
                crop_type=str(group["crop_type"].iloc[0]) if "crop_type" in group.columns else None,
                soil_type=str(group["soil_type"].iloc[0]) if "soil_type" in group.columns else None,
            )
        )

    farm_name = str(farm_rows["farm_name"].iloc[0]) if "farm_name" in farm_rows.columns else farm_id

    return Farm(
        farm_id=farm_id,
        name=farm_name,
        fields=fields,
        raw_df=farm_rows.copy(),
        kpi_df=farm_rows.copy(),  # later you can pass compute_kpis() result
    )
