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
import pandas as pd

def build_master_report_data(
    df: pd.DataFrame,
    my_farm: pd.Series,
    selected_farm: str,
    current_year: int,
    selected_years: list[int]
) -> Dict[str, Any]:
    """
    MASTER PIPELINE for all reports.

    It implements the 5 backend steps:
    1) Ingest & clean (already done before this function is called)
    2) Classify into sustainability categories
    3) Emissions & performance (Scope 1/3, intensity)
    4) SFI / compliance logic
    5) Package everything into one report_data object
    """

    # 2. Classification categories (conceptual mapping)
    classification = {
        "scope1": ["emissions_diesel"],
        "scope3": ["emissions_fertilizer"],
        "production": ["yield_tons"],
        "area": ["field_area_ha"],
        "sfi": [
            "sfi_soil_compliance_rate",
            "sfi_nutrient_compliance_rate",
            "sfi_hedgerow_compliance_rate",
        ],
    }

    # 3. Emissions & performance calculations – use values already computed by compute_kpis
    scope1_kg = float(my_farm.get("emissions_diesel", 0))
    scope3_kg = float(my_farm.get("emissions_fertilizer", 0))
    total_kg = float(my_farm.get("total_emissions", scope1_kg + scope3_kg))

    scope1_t = scope1_kg / 1000.0
    scope3_t = scope3_kg / 1000.0
    total_t = total_kg / 1000.0

    total_area_ha = float(my_farm.get("total_farm_area_ha", df.get("field_area_ha", pd.Series([0])).sum()))
    emissions_per_ha = float(my_farm.get("emissions_per_ha", 0))
    n_per_ha = float(my_farm.get("n_per_ha", 0))

    # 4. SFI / compliance logic (simple version – you can extend later)
    sfi_soil = float(my_farm.get("sfi_soil_compliance_rate", 0)) * 100
    sfi_nutrient = float(my_farm.get("sfi_nutrient_compliance_rate", 0)) * 100
    sfi_hedgerow = float(my_farm.get("sfi_hedgerow_compliance_rate", 0)) * 100

    sfi_readiness = (sfi_soil + sfi_nutrient + sfi_hedgerow) / 3 if any(
        [sfi_soil, sfi_nutrient, sfi_hedgerow]
    ) else 0

    # Supply chain view – by crop
    if "crop_type" in df.columns:
        supply_chain_df = (
            df.groupby("crop_type", dropna=False)
            .agg(
                field_area_ha=("field_area_ha", "sum"),
                emissions_fertilizer=("emissions_fertilizer", "sum"),
                emissions_diesel=("emissions_diesel", "sum"),
                yield_tons=("yield_tons", "sum") if "yield_tons" in df.columns else ("field_area_ha", "sum"),
            )
            .reset_index()
            .rename(
                columns={
                    "crop_type": "Crop",
                    "field_area_ha": "Total Area (ha)",
                    "emissions_fertilizer": "Fertiliser Emissions (kgCO2e)",
                    "emissions_diesel": "Diesel Emissions (kgCO2e)",
                    "yield_tons": "Yield (tons)",
                }
            )
        )
    else:
        supply_chain_df = pd.DataFrame(
            [
                {
                    "Crop": "All crops",
                    "Total Area (ha)": total_area_ha,
                    "Fertiliser Emissions (kgCO2e)": scope3_kg,
                    "Diesel Emissions (kgCO2e)": scope1_kg,
                    "Yield (tons)": float(my_farm.get("yield_tons", 0)),
                }
            ]
        )

    supply_chain_df["Total Emissions (kgCO2e)"] = (
        supply_chain_df["Fertiliser Emissions (kgCO2e)"]
        + supply_chain_df["Diesel Emissions (kgCO2e)"]
    )

    report_data = {
        "farm": {
            "id": selected_farm,
            "name": my_farm.get("farm_name", ""),
            "year": int(current_year),
            "years_selected": [int(y) for y in selected_years],
            "area_ha": total_area_ha,
        },
        "classification": classification,
        "emissions": {
            "scope1_t": scope1_t,
            "scope3_t": scope3_t,
            "total_t": total_t,
            "scope1_kg": scope1_kg,
            "scope3_kg": scope3_kg,
            "total_kg": total_kg,
            "emissions_per_ha": emissions_per_ha,
            "n_per_ha": n_per_ha,
        },
        "sfi": {
            "soil_pct": sfi_soil,
            "nutrient_pct": sfi_nutrient,
            "hedgerow_pct": sfi_hedgerow,
            "readiness_pct": sfi_readiness,
        },
        "esg": {
            "esg_score": float(my_farm.get("esg_score", 0)),
            "e_score": float(my_farm.get("e_score", 0)),
            "s_score": float(my_farm.get("s_score", 0)),
            "g_score": float(my_farm.get("g_score", 0)),
        },
        "supply_chain": supply_chain_df,
        "activity": df,
    }

    return report_data
