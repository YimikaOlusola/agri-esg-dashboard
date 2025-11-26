import pandas as pd
import numpy as np

# Emission factors (UK agriculture standards)
EF_N = 5.5  # kg CO2e per kg N fertilizer
EF_DIESEL = 2.7  # kg CO2e per litre diesel

def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute KPIs at field-month level, then aggregate to farm-year level.
    Handles UK agricultural data with SFI compliance.
    """
    df = df.copy()
    
    # Replace zeros with NaN for proper calculation
    df['field_area_ha'] = df['field_area_ha'].replace(0, np.nan)
    
    # === Field-level calculations ===
    
    # Fertilizer intensity (kg N per hectare)
    df['n_per_ha'] = df['fertiliser_kgN'] / df['field_area_ha']
    df['p_per_ha'] = df['fertiliser_kgP2O5'] / df['field_area_ha']
    df['k_per_ha'] = df['fertiliser_kgK2O'] / df['field_area_ha']
    
    # Emissions (kg CO2e)
    emissions_fertilizer = df['fertiliser_kgN'] * EF_N
    emissions_diesel = df['diesel_litres'] * EF_DIESEL
    
    df['emissions_fertilizer'] = emissions_fertilizer
    df['emissions_diesel'] = emissions_diesel
    df['total_emissions'] = emissions_fertilizer + emissions_diesel
    df['emissions_per_ha'] = df['total_emissions'] / df['field_area_ha']
    
    # Labour intensity
    df['labour_hours_per_ha'] = df['labour_hours'] / df['field_area_ha']
    
    # Convert yes/no to binary for aggregation
    yes_no_cols = [
        'pesticide_applied_yes_no', 'irrigation_applied_yes_no',
        'livestock_present_yes_no', 'sfi_soil_standard_yes_no',
        'sfi_nutrient_management_yes_no', 'sfi_hedgerows_yes_no'
    ]
    
    for col in yes_no_cols:
        if col in df.columns:
            df[col + '_binary'] = df[col].str.lower().isin(['yes', 'true', '1']).astype(int)
    
    return df

def aggregate_to_farm_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate field-level data to farm-year level for ESG scoring.
    """
    # Group by farm and year
    grouped = df.groupby(['farm_id', 'farm_name', 'year']).agg({
        # Area metrics
        'field_area_ha': 'sum',  # Total farm area
        
        # Intensity metrics (weighted by area)
        'n_per_ha': 'mean',
        'p_per_ha': 'mean',
        'k_per_ha': 'mean',
        'emissions_per_ha': 'mean',
        'labour_hours_per_ha': 'mean',
        
        # Total emissions
        'total_emissions': 'sum',
        'emissions_fertilizer': 'sum',
        'emissions_diesel': 'sum',
        
        # Practices (% of fields)
        'pesticide_applied_yes_no_binary': 'mean',
        'irrigation_applied_yes_no_binary': 'mean',
        'livestock_present_yes_no_binary': 'mean',
        
        # SFI compliance (% of fields meeting standard)
        'sfi_soil_standard_yes_no_binary': 'mean',
        'sfi_nutrient_management_yes_no_binary': 'mean',
        'sfi_hedgerows_yes_no_binary': 'mean',
    })
    
    # Rename for clarity
    grouped = grouped.rename(columns={
        'field_area_ha': 'total_farm_area_ha',
        'pesticide_applied_yes_no_binary': 'pesticide_use_rate',
        'irrigation_applied_yes_no_binary': 'irrigation_rate',
        'livestock_present_yes_no_binary': 'livestock_presence',
        'sfi_soil_standard_yes_no_binary': 'sfi_soil_compliance_rate',
        'sfi_nutrient_management_yes_no_binary': 'sfi_nutrient_compliance_rate',
        'sfi_hedgerows_yes_no_binary': 'sfi_hedgerow_compliance_rate',
    })
    
    return grouped.reset_index()

def merge_optional_data(base_df: pd.DataFrame, optional_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Merge optional environmental data if available.
    """
    if optional_df is None or optional_df.empty:
        return base_df
    
    # Aggregate optional data to farm-year level
    optional_agg = optional_df.groupby(['farm_id', 'year']).agg({
        'soil_organic_matter_pct': 'mean',
        'soil_ph': 'mean',
        'cover_crop_planted_yes_no': lambda x: x.str.lower().isin(['yes', 'true', '1']).mean(),
        'hedgerow_length_m': 'sum',
        'wildflower_area_ha': 'sum',
        'buffer_strip_area_ha': 'sum',
        'trees_planted_count': 'sum',
        'reduced_tillage_yes_no': lambda x: x.str.lower().isin(['yes', 'true', '1']).mean(),
        'integrated_pest_management_yes_no': lambda x: x.str.lower().isin(['yes', 'true', '1']).mean(),
        'water_volume_m3': 'sum',
        'labour_hs_training_done_yes_no': lambda x: x.str.lower().isin(['yes', 'true', '1']).mean(),
        'worker_contracts_formalised_yes_no': lambda x: x.str.lower().isin(['yes', 'true', '1']).mean(),
    }).reset_index()
    
    # Merge with base data
    merged = pd.merge(base_df, optional_agg, on=['farm_id', 'year'], how='left')
    
    return merged

def percentile_score(series: pd.Series, higher_is_better=True) -> pd.Series:
    """Convert a series into 0-100 percentile scores."""
    s = series.copy()
    
    if s.dropna().nunique() <= 1:
        return pd.Series(50, index=s.index)
    
    ranks = s.rank(pct=True)
    
    if higher_is_better:
        score = ranks * 100
    else:
        score = (1 - ranks) * 100
    
    return score.round(1)

def compute_esg_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute ESG scores from aggregated farm-level data.
    """
    result = df.copy()
    
    # === ENVIRONMENT SCORE (50% weight) ===
    env_components = {}
    
    # Lower emissions = better
    env_components['emissions'] = percentile_score(result['emissions_per_ha'], higher_is_better=False)
    
    # Lower nitrogen use = better (environmental protection)
    env_components['nitrogen'] = percentile_score(result['n_per_ha'], higher_is_better=False)
    
    # Less pesticide use = better
    env_components['pesticide'] = percentile_score(result['pesticide_use_rate'], higher_is_better=False)
    
    # Biodiversity metrics (if available)
    if 'hedgerow_length_m' in result.columns:
        # More hedgerows = better
        env_components['hedgerows'] = percentile_score(result['hedgerow_length_m'], higher_is_better=True)
    
    if 'wildflower_area_ha' in result.columns:
        env_components['wildflowers'] = percentile_score(result['wildflower_area_ha'], higher_is_better=True)
    
    if 'soil_organic_matter_pct' in result.columns:
        env_components['soil_health'] = percentile_score(result['soil_organic_matter_pct'], higher_is_better=True)
    
    if 'cover_crop_planted_yes_no' in result.columns:
        env_components['cover_crops'] = percentile_score(result['cover_crop_planted_yes_no'], higher_is_better=True)
    
    # Calculate environment score
    env_df = pd.DataFrame(env_components, index=result.index)
    result['e_score'] = env_df.mean(axis=1)
    
    # === SOCIAL SCORE (30% weight) ===
    soc_components = {}
    
    # Higher labour hours per hectare = more employment (context dependent)
    soc_components['employment'] = percentile_score(result['labour_hours_per_ha'], higher_is_better=True)
    
    # Safety and worker welfare (if available)
    if 'labour_hs_training_done_yes_no' in result.columns:
        soc_components['safety_training'] = percentile_score(
            result['labour_hs_training_done_yes_no'], higher_is_better=True
        )
    
    if 'worker_contracts_formalised_yes_no' in result.columns:
        soc_components['worker_contracts'] = percentile_score(
            result['worker_contracts_formalised_yes_no'], higher_is_better=True
        )
    
    # Calculate social score (or neutral if no data)
    if len(soc_components) > 0:
        soc_df = pd.DataFrame(soc_components, index=result.index)
        result['s_score'] = soc_df.mean(axis=1)
    else:
        result['s_score'] = 50.0  # Neutral score if no social data
    
    # === GOVERNANCE SCORE (20% weight) ===
    gov_components = {}
    
    # SFI compliance rates (higher = better governance)
    gov_components['sfi_soil'] = percentile_score(result['sfi_soil_compliance_rate'], higher_is_better=True)
    gov_components['sfi_nutrient'] = percentile_score(result['sfi_nutrient_compliance_rate'], higher_is_better=True)
    gov_components['sfi_hedgerow'] = percentile_score(result['sfi_hedgerow_compliance_rate'], higher_is_better=True)
    
    # Sustainable practices (if available)
    if 'reduced_tillage_yes_no' in result.columns:
        gov_components['reduced_tillage'] = percentile_score(result['reduced_tillage_yes_no'], higher_is_better=True)
    
    if 'integrated_pest_management_yes_no' in result.columns:
        gov_components['ipm'] = percentile_score(result['integrated_pest_management_yes_no'], higher_is_better=True)
    
    # Calculate governance score
    gov_df = pd.DataFrame(gov_components, index=result.index)
    result['g_score'] = gov_df.mean(axis=1)
    
    # === OVERALL ESG SCORE ===
    result['esg_score'] = (
        result['e_score'] * 0.5 +  # 50% Environment
        result['s_score'] * 0.3 +  # 30% Social
        result['g_score'] * 0.2    # 20% Governance
    )
    
    return result
