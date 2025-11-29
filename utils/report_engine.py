from dataclasses import dataclass
from typing import Dict, Any
import pandas as pd

@dataclass
class FarmProfile:
    farm_name: str
    report_year: int
    base_year: int

@dataclass
class EmissionsResults:
    scope1_total_tco2e: float
    scope3_total_tco2e: float
    total_emissions_tco2e: float
    total_area_ha: float
    scope1_intensity_kg_per_ha: float
    scope3_intensity_kg_per_ha: float
    intensity_kg_per_ha: float
    top_drivers_sentence: str


# 🔁 Placeholder emission factors – replace later with real DEFRA/IPCC numbers
DIESEL_FACTOR_KG_PER_LITRE = 2.68
N_FERT_FACTOR_KG_PER_KG = 6.0
P_FERT_FACTOR_KG_PER_KG = 1.0
K_FERT_FACTOR_KG_PER_KG = 0.5

def _calculate_emissions(df: pd.DataFrame) -> EmissionsResults:
    """
    Map CSV columns to Scope 1 & 3 emissions and calculate intensities.

    Expected columns:
      - 'Field Area (ha)'
      - 'Diesel Used (Litres)'
      - 'Nitrogen Fertiliser (kg)'
      - 'Phosphate Fertiliser (kg)'
      - 'Potash Fertiliser (kg)'
    """
    total_area_ha = df['Field Area (ha)'].sum()

    # Scope 1 – diesel
    total_diesel_litres = df['Diesel Used (Litres)'].sum()
    scope1_kg = total_diesel_litres * DIESEL_FACTOR_KG_PER_LITRE

    # Scope 3 – fertiliser
    total_n = df['Nitrogen Fertiliser (kg)'].sum()
    total_p = df['Phosphate Fertiliser (kg)'].sum()
    total_k = df['Potash Fertiliser (kg)'].sum()

    fert_kg = (
        total_n * N_FERT_FACTOR_KG_PER_KG
        + total_p * P_FERT_FACTOR_KG_PER_KG
        + total_k * K_FERT_FACTOR_KG_PER_KG
    )

    scope3_kg = fert_kg

    # Convert to tonnes
    scope1_t = scope1_kg / 1000.0
    scope3_t = scope3_kg / 1000.0
    total_t = scope1_t + scope3_t

    if total_area_ha > 0:
        scope1_intensity = scope1_kg / total_area_ha
        scope3_intensity = scope3_kg / total_area_ha
        total_intensity = (scope1_kg + scope3_kg) / total_area_ha
    else:
        scope1_intensity = scope3_intensity = total_intensity = 0.0

    drivers = []
    if scope1_t > 0:
        drivers.append("diesel use")
    if scope3_t > 0:
        drivers.append("fertiliser use")

    if not drivers:
        top_sentence = "No major emissions sources identified in the current dataset."
    elif len(drivers) == 1:
        top_sentence = f"Emissions are mainly driven by {drivers[0]}."
    else:
        top_sentence = f"Emissions are mainly driven by {', '.join(drivers[:-1])} and {drivers[-1]}."

    return EmissionsResults(
        scope1_total_tco2e=scope1_t,
        scope3_total_tco2e=scope3_t,
        total_emissions_tco2e=total_t,
        total_area_ha=total_area_ha,
        scope1_intensity_kg_per_ha=scope1_intensity,
        scope3_intensity_kg_per_ha=scope3_intensity,
        intensity_kg_per_ha=total_intensity,
        top_drivers_sentence=top_sentence,
    )


def build_report(df: pd.DataFrame, farm_profile: FarmProfile) -> Dict[str, Any]:
    """Return a dict with all numbers/text needed for the PDF/Excel report."""
    results = _calculate_emissions(df)

    report = {
        "farm_name": farm_profile.farm_name,
        "report_year": farm_profile.report_year,
        "base_year": farm_profile.base_year,
        "number_of_fields": df['Field Name'].nunique(),
        "total_area_ha": results.total_area_ha,
        "scope1_total": results.scope1_total_tco2e,
        "scope3_total": results.scope3_total_tco2e,
        "total_emissions": results.total_emissions_tco2e,
        "scope1_intensity_kg_per_ha": results.scope1_intensity_kg_per_ha,
        "scope3_intensity_kg_per_ha": results.scope3_intensity_kg_per_ha,
        "intensity_kg_per_ha": results.intensity_kg_per_ha,
        "top_drivers_sentence": results.top_drivers_sentence,
        "fertiliser_emissions_tco2e": results.scope3_total_tco2e,
    }

    return report
