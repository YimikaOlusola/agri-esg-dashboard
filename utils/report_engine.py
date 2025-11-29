from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd

# === DATA CLASSES ===


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


# === EMISSIONS ENGINE (FIELD / FARM LEVEL) ===


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
    if df.empty:
        return EmissionsResults(
            scope1_total_tco2e=0.0,
            scope3_total_tco2e=0.0,
            total_emissions_tco2e=0.0,
            total_area_ha=0.0,
            scope1_intensity_kg_per_ha=0.0,
            scope3_intensity_kg_per_ha=0.0,
            intensity_kg_per_ha=0.0,
            top_drivers_sentence="No data available for emissions calculations.",
        )

    total_area_ha = df["Field Area (ha)"].fillna(0).sum()

    # Scope 1 – diesel
    total_diesel_litres = df["Diesel Used (Litres)"].fillna(0).sum()
    scope1_kg = total_diesel_litres * DIESEL_FACTOR_KG_PER_LITRE

    # Scope 3 – fertiliser
    total_n = df["Nitrogen Fertiliser (kg)"].fillna(0).sum()
    total_p = df["Phosphate Fertiliser (kg)"].fillna(0).sum()
    total_k = df["Potash Fertiliser (kg)"].fillna(0).sum()

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

    drivers: List[str] = []
    if scope1_t > 0:
        drivers.append("diesel use")
    if scope3_t > 0:
        drivers.append("fertiliser use")

    if not drivers:
        top_sentence = "No major emissions sources identified in the current dataset."
    elif len(drivers) == 1:
        top_sentence = f"Emissions are mainly driven by {drivers[0]}."
    else:
        top_sentence = (
            f"Emissions are mainly driven by {', '.join(drivers[:-1])} and {drivers[-1]}."
        )

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
    """
    Return a dict with all numbers/text needed for the emissions report.

    This is used by the Emissions & Performance report in the app.
    """
    results = _calculate_emissions(df)

    report = {
        "farm_name": farm_profile.farm_name,
        "report_year": farm_profile.report_year,
        "base_year": farm_profile.base_year,
        "number_of_fields": df["Field Name"].nunique(),
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


# === SUPPLY CHAIN TABLE (CROP-LEVEL SCOPE 3 VIEW) ===


def _build_supply_chain_table(farm_year_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a simple crop-level Scope 3 / supply-chain table.

    Tries to map:
      - crop_type
      - field_area_ha
      - diesel_litres
      - fertiliser_kgN / P2O5 / K2O
      - yield_tons (if available)
    """
    if farm_year_df.empty:
        return pd.DataFrame(
            columns=[
                "Crop",
                "Total Area (ha)",
                "Yield (tons)",
                "Emissions (tCO2e)",
                "Emissions (kgCO2e/ton)",
            ]
        )

    rows: List[Dict[str, Any]] = []
    crop_series = (
        farm_year_df["crop_type"]
        if "crop_type" in farm_year_df.columns
        else pd.Series(["Unknown"] * len(farm_year_df))
    )

    for crop, group in farm_year_df.groupby(crop_series):
        # Prepare a DF in the shape expected by _calculate_emissions
        tmp = group.rename(
            columns={
                "field_area_ha": "Field Area (ha)",
                "diesel_litres": "Diesel Used (Litres)",
                "fertiliser_kgN": "Nitrogen Fertiliser (kg)",
                "fertiliser_kgP2O5": "Phosphate Fertiliser (kg)",
                "fertiliser_kgK2O": "Potash Fertiliser (kg)",
            }
        )

        for col in [
            "Field Area (ha)",
            "Diesel Used (Litres)",
            "Nitrogen Fertiliser (kg)",
            "Phosphate Fertiliser (kg)",
            "Potash Fertiliser (kg)",
        ]:
            if col not in tmp.columns:
                tmp[col] = 0

        results = _calculate_emissions(tmp)

        total_yield_tons = (
            group["yield_tons"].fillna(0).sum()
            if "yield_tons" in group.columns
            else 0.0
        )
        emissions_t = results.total_emissions_tco2e
        if total_yield_tons > 0:
            emissions_kg_per_ton = (emissions_t * 1000.0) / total_yield_tons
        else:
            emissions_kg_per_ton = None

        rows.append(
            {
                "Crop": str(crop),
                "Total Area (ha)": float(results.total_area_ha),
                "Yield (tons)": float(total_yield_tons),
                "Emissions (tCO2e)": float(emissions_t),
                "Emissions (kgCO2e/ton)": emissions_kg_per_ton,
            }
        )

    return pd.DataFrame(rows)


# === SFI LAND PARCELS (FOR SFI PLAN DOCUMENT) ===


def _build_sfi_land_parcels(farm_year_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build land-parcel level view for SFI planning.

    Uses your internal column names:
      - field_name
      - field_id (optional)
      - field_area_ha
      - crop_type
      - soil_type
      - cover_crop_planted_yes_no
      - reduced_tillage_yes_no
      - trees_planted_count
      - soil_test_conducted_yes_no
    """
    if farm_year_df.empty:
        return {
            "land_parcels": [],
            "summary": {
                "total_area_ha": 0.0,
                "num_fields": 0,
                "cover_crop_area_pct": 0.0,
                "reduced_tillage_area_pct": 0.0,
                "soil_test_area_pct": 0.0,
                "fields_with_trees_pct": 0.0,
            },
        }

    parcels: List[Dict[str, Any]] = []
    total_area = 0.0
    cover_crop_area = 0.0
    reduced_tillage_area = 0.0
    soil_test_area = 0.0
    trees_area = 0.0

    for _, row in farm_year_df.iterrows():
        field_area = float(row.get("field_area_ha", 0.0) or 0.0)
        total_area += field_area

        # Normalise Yes/No style fields
        def is_yes(value: Any) -> bool:
            return str(value).strip().lower() in ["yes", "y", "true", "1"]

        cover_crop = is_yes(row.get("cover_crop_planted_yes_no", "no"))
        reduced_tillage = is_yes(row.get("reduced_tillage_yes_no", "no"))
        soil_test = is_yes(row.get("soil_test_conducted_yes_no", "no"))

        trees_val = row.get("trees_planted_count", 0)
        try:
            trees_count = float(trees_val) if trees_val not in [None, ""] else 0.0
        except Exception:
            trees_count = 0.0

        if cover_crop:
            cover_crop_area += field_area
        if reduced_tillage:
            reduced_tillage_area += field_area
        if soil_test:
            soil_test_area += field_area
        if trees_count > 0:
            trees_area += field_area

        parcels.append(
            {
                "field_id": row.get("field_id", ""),
                "field_name": row.get("field_name", ""),
                "field_area_ha": field_area,
                "crop_type": row.get("crop_type", ""),
                "soil_type": row.get("soil_type", ""),
                "cover_crop": cover_crop,
                "reduced_tillage": reduced_tillage,
                "soil_test_conducted": soil_test,
                "trees_planted_count": trees_count,
            }
        )

    def pct(part: float, whole: float) -> float:
        return float(part) / float(whole) * 100.0 if whole > 0 else 0.0

    summary = {
        "total_area_ha": total_area,
        "num_fields": len(parcels),
        "cover_crop_area_pct": pct(cover_crop_area, total_area),
        "reduced_tillage_area_pct": pct(reduced_tillage_area, total_area),
        "soil_test_area_pct": pct(soil_test_area, total_area),
        "fields_with_trees_pct": pct(trees_area, total_area),
    }

    return {
        "land_parcels": parcels,
        "summary": summary,
    }


# === MASTER PIPELINE FOR ALL 5 REPORTS ===


def build_master_report_data(
    df: pd.DataFrame,
    my_farm: pd.Series,
    selected_farm: str,
    current_year: int,
    selected_years: List[int],
    policy: Any = None,
) -> Dict[str, Any]:
    """
    ONE master object powering all 5 reports.

    - df: full activity-level dataframe (all farms, all years)
    - my_farm: aggregated row for the selected farm/year (from farm_df / esg_df)
    - selected_farm: farm_id
    - current_year: reporting year (int)
    - selected_years: list of years in view mode
    - policy: optional policy object (e.g. SFIPolicy)

    Returns a dict with keys:
      - farm
      - classification
      - emissions
      - esg
      - policy
      - sfi  (alias of policy for backwards compatibility)
      - supply_chain (DataFrame)
      - activity (DataFrame)
      - sfi_plan (land-parcel view + summary)
    """
    # --- Filter to the selected farm and year(s) ---
    if "farm_id" in df.columns:
        farm_all_years = df[df["farm_id"] == selected_farm].copy()
    else:
        # Fallback: assume this df is already only one farm
        farm_all_years = df.copy()

    if "year" in farm_all_years.columns:
        farm_current_year = farm_all_years[
            farm_all_years["year"] == current_year
        ].copy()
    else:
        farm_current_year = farm_all_years.copy()

    # --- Farm info block ---
    farm_name = (
        my_farm.get("farm_name")
        if hasattr(my_farm, "get")
        else (
            farm_all_years["farm_name"].iloc[0]
            if "farm_name" in farm_all_years.columns
            else selected_farm
        )
    )

    if hasattr(my_farm, "get"):
        area_ha = float(
            my_farm.get(
                "total_farm_area_ha",
                farm_current_year.get("field_area_ha", pd.Series([0])).sum(),
            )
        )
    else:
        area_ha = float(
            farm_current_year["field_area_ha"].sum()
            if "field_area_ha" in farm_current_year.columns
            else 0.0
        )

    farm_block = {
        "id": selected_farm,
        "name": farm_name or "Farm",
        "year": int(current_year),
        "years_selected": [int(y) for y in selected_years],
        "area_ha": area_ha,
    }

    # --- Helper for safe float access ---
    def _safe_float(series_like, key, default=0.0):
        try:
            return float(series_like.get(key, default))
        except Exception:
            return float(default)

    # --- Emissions block (from my_farm aggregates) ---
    emissions_block = {
        "total_emissions": _safe_float(my_farm, "total_emissions", 0.0),
        "emissions_per_ha": _safe_float(my_farm, "emissions_per_ha", 0.0),
        "n_per_ha": _safe_float(my_farm, "n_per_ha", 0.0),
    }

    # --- ESG scores block ---
    esg_block = {
        "esg_score": _safe_float(my_farm, "esg_score", 0.0),
        "e_score": _safe_float(my_farm, "e_score", 0.0),
        "s_score": _safe_float(my_farm, "s_score", 0.0),
        "g_score": _safe_float(my_farm, "g_score", 0.0),
    }

    # --- Simple classification description (data → frameworks) ---
    classification_block = {
        "scope1_columns": ["diesel_litres"] if "diesel_litres" in df.columns else [],
        "scope2_columns": [],  # electricity etc. – future work
        "scope3_columns": [
            col
            for col in ["fertiliser_kgN", "fertiliser_kgP2O5", "fertiliser_kgK2O"]
            if col in df.columns
        ],
        "production_columns": [col for col in ["yield_tons"] if col in df.columns],
        "area_column": "field_area_ha" if "field_area_ha" in df.columns else None,
    }

    # --- Policy / SFI block (for now inferred from existing columns) ---
    policy_name = getattr(policy, "name", "Sustainable Farming Incentive")
    policy_slug = getattr(policy, "slug", "sfi")

    soil_rate = _safe_float(my_farm, "sfi_soil_compliance_rate", 0.0)
    nutrient_rate = _safe_float(my_farm, "sfi_nutrient_compliance_rate", 0.0)
    hedgerow_rate = _safe_float(my_farm, "sfi_hedgerow_compliance_rate", 0.0)

    # assume these rates are 0–1; convert to %
    soil_pct = soil_rate * 100.0
    nutrient_pct = nutrient_rate * 100.0
    hedgerow_pct = hedgerow_rate * 100.0
    if any([soil_rate, nutrient_rate, hedgerow_rate]):
        readiness_pct = (soil_pct + nutrient_pct + hedgerow_pct) / 3.0
    else:
        readiness_pct = 0.0

    policy_block = {
        "policy": policy_slug,
        "policy_name": policy_name,
        "soil_pct": soil_pct,
        "nutrient_pct": nutrient_pct,
        "hedgerow_pct": hedgerow_pct,
        "readiness_pct": readiness_pct,
    }

    # Backwards-compatible alias for any old code that expects "sfi"
    sfi_block = dict(policy_block)

    # --- Supply chain (Scope 3 crop table) ---
    supply_chain_df = _build_supply_chain_table(farm_current_year)

    # --- SFI plan block (land-parcel view for SFI plan document) ---
    sfi_plan_block = _build_sfi_land_parcels(farm_current_year)

    # --- Assemble master dict ---
    master = {
        "farm": farm_block,
        "classification": classification_block,
        "emissions": emissions_block,
        "esg": esg_block,
        "policy": policy_block,
        "sfi": sfi_block,
        "supply_chain": supply_chain_df,
        "activity": farm_current_year,
        "sfi_plan": sfi_plan_block,
    }

    return master
