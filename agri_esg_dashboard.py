import streamlit as st
import pandas as pd
import numpy as np
import altair as alt   # for richer charts

# -----------------------
# CONFIG
# -----------------------

st.set_page_config(
    page_title="AgriESG Dashboard",
    page_icon="🌱",
    layout="wide",
)

# Emission factors (placeholder values – adjust with ESG experts)
EF_N = 5.5      # kg CO2e per kg N fertilizer
EF_DIESEL = 2.7 # kg CO2e per litre diesel
EF_ELEC = 0.5   # kg CO2e per kWh electricity

# -----------------------
# HELPER FUNCTIONS
# -----------------------

def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Add core agronomic, emissions and social KPIs at record level."""
    df = df.copy()

    df["area_ha"] = df["area_ha"].replace(0, np.nan)
    df["yield_tonnes"] = df["yield_tonnes"].replace(0, np.nan)
    df["workers_total"] = df["workers_total"].replace(0, np.nan)

    # Productivity & resource intensity
    df["yield_per_ha"] = df["yield_tonnes"] / df["area_ha"]
    df["n_per_ha"] = df["fertilizer_n_kg"] / df["area_ha"]
    df["water_per_tonne"] = df["water_m3"] / df["yield_tonnes"]

    # Emissions (kg CO2e)
    emissions_fertilizer = df["fertilizer_n_kg"] * EF_N
    emissions_diesel = df["diesel_litres"] * EF_DIESEL
    emissions_electric = df["electricity_kwh"] * EF_ELEC

    df["emissions_fertilizer"] = emissions_fertilizer
    df["emissions_diesel"] = emissions_diesel
    df["emissions_electric"] = emissions_electric

    df["total_emissions"] = emissions_fertilizer + emissions_diesel + emissions_electric
    df["emissions_per_tonne"] = df["total_emissions"] / df["yield_tonnes"]
    df["emissions_per_ha"] = df["total_emissions"] / df["area_ha"]

    # Social metrics
    df["female_share"] = df["workers_female"] / df["workers_total"]
    df["accidents_per_100_workers"] = (df["accidents_count"] / df["workers_total"]) * 100

    return df


def kpi_card(label: str, value, suffix: str = "", precision: int = 2):
    """Simple KPI metric helper."""
    if pd.isna(value):
        display_value = "N/A"
    else:
        display_value = f"{value:.{precision}f}{suffix}"
    st.metric(label=label, value=display_value)


def percentile_score(series: pd.Series, higher_is_better=True) -> pd.Series:
    """
    Convert a series into 0–100 percentile scores.
    If there's no variation, everyone gets 50.
    """
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
    Aggregate to farm level and compute Environment, Social,
    Governance and overall ESG scores.
    """
    grouped = df.groupby("farm_id").agg(
        organisation=("organisation_name", "first"),
        country=("country", "first"),
        crop=("crop", "first"),
        area_ha=("area_ha", "sum"),
        yield_tonnes=("yield_tonnes", "sum"),
        total_emissions=("total_emissions", "sum"),
        emissions_per_ha=("emissions_per_ha", "mean"),
        emissions_per_tonne=("emissions_per_tonne", "mean"),
        n_per_ha=("n_per_ha", "mean"),
        water_per_tonne=("water_per_tonne", "mean"),
        yield_per_ha=("yield_per_ha", "mean"),
        female_share=("female_share", "mean"),
        accidents_per_100_workers=("accidents_per_100_workers", "mean"),
        workers_total=("workers_total", "sum"),
        accidents_count=("accidents_count", "sum"),
    )

    # -------- Environment pillar (lower is better) --------
    env = pd.DataFrame(index=grouped.index)
    env["emissions_per_ha"] = percentile_score(grouped["emissions_per_ha"], higher_is_better=False)
    env["emissions_per_tonne"] = percentile_score(grouped["emissions_per_tonne"], higher_is_better=False)
    env["n_per_ha"] = percentile_score(grouped["n_per_ha"], higher_is_better=False)
    env["water_per_tonne"] = percentile_score(grouped["water_per_tonne"], higher_is_better=False)
    grouped["E_score"] = env.mean(axis=1)

    # -------- Social pillar --------
    soc = pd.DataFrame(index=grouped.index)
    # more women & fewer accidents are better
    soc["female_share"] = percentile_score(grouped["female_share"], higher_is_better=True)
    soc["accidents_per_100_workers"] = percentile_score(
        grouped["accidents_per_100_workers"], higher_is_better=False
    )
    grouped["S_score"] = soc.mean(axis=1)

    # -------- Governance pillar (optional flags) --------
    gov_cols = []
    for col in ["certification", "farm_safety_policy", "grievance_mechanism",
                "pesticide_handling_training", "living_wage_paid"]:
        if col in df.columns:
            # treat 'yes'/'true'/1 as good practice
            grouped[col] = df.groupby("farm_id")[col].apply(
                lambda x: (x.astype(str).str.lower().isin(["yes", "true", "1"])).mean()
            )
            gov_cols.append(col)

    if gov_cols:
        gov = pd.DataFrame(index=grouped.index)
        for col in gov_cols:
            gov[col] = percentile_score(grouped[col], higher_is_better=True)
        grouped["G_score"] = gov.mean(axis=1)
    else:
        grouped["G_score"] = 50.0  # neutral if no governance data

    # -------- Overall ESG score --------
    grouped["ESG_score"] = (
        grouped["E_score"] * 0.5 +
        grouped["S_score"] * 0.3 +
        grouped["G_score"] * 0.2
    )

    return grouped.reset_index()


def generate_insights(esg_df: pd.DataFrame) -> list[str]:
    """Create narrative insights from ESG table."""
    if esg_df.empty:
        return ["No insights available – no farms after filtering."]

    insights = []

    avg_esg = esg_df["ESG_score"].mean()
    insights.append(
        f"Average ESG score across **{len(esg_df)} farms** is **{avg_esg:,.1f}/100**."
    )

    # Top & bottom farm
    top = esg_df.sort_values("ESG_score", ascending=False).iloc[0]
    bottom = esg_df.sort_values("ESG_score", ascending=True).iloc[0]

    insights.append(
        f"**Farm {top['farm_id']}** in {top['country']} is the current ESG leader "
        f"with a score of **{top['ESG_score']:,.1f}**."
    )
    insights.append(
        f"**Farm {bottom['farm_id']}** in {bottom['country']} has the lowest ESG score "
        f"(**{bottom['ESG_score']:,.1f}**), indicating a priority candidate for support."
    )

    # Emission hotspots
    high_em = esg_df.sort_values("emissions_per_ha", ascending=False).head(3)
    high_list = ", ".join(high_em["farm_id"].astype(str).tolist())
    insights.append(
        f"Highest **emissions per hectare** are observed in farms: {high_list}. "
        "These are key hotspots for mitigation actions."
    )

    # Gender and safety
    if esg_df["female_share"].notna().any():
        best_gender = esg_df.sort_values("female_share", ascending=False).iloc[0]
        insights.append(
            f"Best gender inclusion: **Farm {best_gender['farm_id']}** with "
            f"**{best_gender['female_share']*100:,.0f}%** female workers."
        )

    if esg_df["accidents_per_100_workers"].notna().any():
        worst_safety = esg_df.sort_values("accidents_per_100_workers", ascending=False).iloc[0]
        insights.append(
            f"Safety concern: **Farm {worst_safety['farm_id']}** records "
            f"**{worst_safety['accidents_per_100_workers']:,.1f} accidents per 100 workers.**"
        )

    return insights


# -----------------------
# UI LAYOUT
# -----------------------

st.title("🌱 AgriESG Dashboard (Multi-Farm ESG Analysis)")
st.write("Upload your farm data CSV to generate ESG indicators, farm rankings, and insights.")

with st.expander("Click to see expected CSV format"):
    st.markdown(
        """
        **Required CSV columns:**

        - `organisation_name`
        - `farm_id`
        - `country`
        - `year`
        - `crop`
        - `area_ha`
        - `yield_tonnes`
        - `fertilizer_n_kg`
        - `diesel_litres`
        - `electricity_kwh`
        - `water_m3`
        - `workers_total`
        - `workers_female`
        - `accidents_count`

        *Optional columns for richer ESG scoring* (if available):

        - `certification`, `farm_safety_policy`, `grievance_mechanism`,
          `pesticide_handling_training`, `living_wage_paid`
        """
    )

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV to see the dashboard.")
    st.stop()

# -----------------------
# READ CSV WITH FALLBACK ENCODINGS
# -----------------------

try:
    raw_df = pd.read_csv(uploaded_file, encoding="utf-8")
except UnicodeDecodeError:
    uploaded_file.seek(0)
    raw_df = pd.read_csv(uploaded_file, encoding="latin1")
except Exception as e:
    st.error(f"Error reading CSV: {e}")
    st.stop()

# -----------------------
# VALIDATE REQUIRED COLUMNS
# -----------------------

required_cols = [
    "organisation_name","farm_id","country","year","crop","area_ha",
    "yield_tonnes","fertilizer_n_kg","diesel_litres","electricity_kwh",
    "water_m3","workers_total","workers_female","accidents_count"
]

missing = [c for c in required_cols if c not in raw_df.columns]
if missing:
    st.error(f"Missing required columns: {', '.join(missing)}")
    st.stop()

# -----------------------
# KPI CALCULATION
# -----------------------

df = compute_kpis(raw_df)

st.sidebar.header("Filters")

years = sorted(df["year"].dropna().unique().tolist())
crops = sorted(df["crop"].dropna().unique().tolist())
countries = sorted(df["country"].dropna().unique().tolist())

year_filter = st.sidebar.multiselect("Year", years, default=years)
crop_filter = st.sidebar.multiselect("Crop", crops, default=crops)
country_filter = st.sidebar.multiselect("Country", countries, default=countries)

filtered_df = df[
    df["year"].isin(year_filter)
    & df["crop"].isin(crop_filter)
    & df["country"].isin(country_filter)
]

if filtered_df.empty:
    st.warning("No data after applying filters.")
    st.stop()

# -----------------------
# PORTFOLIO KPIs (same as before)
# -----------------------

st.subheader("Key Indicators (filtered portfolio)")

agg = filtered_df.copy()

total_area = agg["area_ha"].sum()
total_yield = agg["yield_tonnes"].sum()
total_emissions = agg["total_emissions"].sum()
total_workers = agg["workers_total"].sum()
total_female_workers = agg["workers_female"].sum()
total_accidents = agg["accidents_count"].sum()

yield_per_ha = total_yield / total_area if total_area else np.nan
emissions_per_tonne = total_emissions / total_yield if total_yield else np.nan
water_per_tonne = agg["water_m3"].sum() / total_yield if total_yield else np.nan
female_share_overall = total_female_workers / total_workers if total_workers else np.nan
accidents_per_100_workers_overall = (total_accidents / total_workers * 100) if total_workers else np.nan

col1, col2, col3, col4 = st.columns(4)

with col1: kpi_card("Yield per ha (t/ha)", yield_per_ha)
with col2: kpi_card("Emissions per tonne (kg CO₂e/t)", emissions_per_tonne, precision=1)
with col3: kpi_card("Water per tonne (m³/t)", water_per_tonne, precision=1)
with col4: kpi_card("Female workforce (%)", female_share_overall*100 if not pd.isna(female_share_overall) else np.nan, suffix="%", precision=0)

col5, col6, col7, col8 = st.columns(4)

with col5: kpi_card("Total emissions (kg CO₂e)", total_emissions, precision=0)
with col6: kpi_card("Total area (ha)", total_area, precision=1)
with col7: kpi_card("Total workers", total_workers, precision=0)
with col8: kpi_card("Accidents per 100 workers", accidents_per_100_workers_overall, precision=2)

# -----------------------
# ESG SCORING & DEEP ANALYSIS
# -----------------------

esg_df = compute_esg_scores(filtered_df)
insights = generate_insights(esg_df)

st.markdown("---")
st.subheader("ESG Scores & Farm Benchmarking")

c_esg1, c_esg2 = st.columns(2)

# ESG ranking bar chart
with c_esg1:
    st.markdown("**ESG score by farm (0–100)**")
    chart_df = esg_df.sort_values("ESG_score", ascending=False)
    esg_chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("ESG_score:Q", title="ESG score"),
            y=alt.Y("farm_id:N", sort="-x", title="Farm"),
            color=alt.Color("ESG_score:Q", scale=alt.Scale(scheme="blues")),
            tooltip=[
                "farm_id",
                "country",
                "crop",
                alt.Tooltip("ESG_score:Q", format=".1f"),
                alt.Tooltip("E_score:Q", format=".1f", title="Env"),
                alt.Tooltip("S_score:Q", format=".1f", title="Soc"),
                alt.Tooltip("G_score:Q", format=".1f", title="Gov"),
            ],
        )
    )
    st.altair_chart(esg_chart, use_container_width=True)

# Emissions vs yield scatter
with c_esg2:
    st.markdown("**Emissions vs productivity (per farm)**")
    scatter = (
        alt.Chart(esg_df)
        .mark_circle(size=120)
        .encode(
            x=alt.X("yield_per_ha:Q", title="Yield (t/ha)"),
            y=alt.Y("emissions_per_ha:Q", title="Emissions (kg CO₂e/ha)"),
            color=alt.Color("ESG_score:Q", scale=alt.Scale(scheme="viridis")),
            tooltip=[
                "farm_id",
                "country",
                "crop",
                alt.Tooltip("ESG_score:Q", format=".1f"),
                alt.Tooltip("yield_per_ha:Q", format=".2f", title="Yield t/ha"),
                alt.Tooltip("emissions_per_ha:Q", format=".1f", title="Emissions kg CO₂e/ha"),
            ],
        )
    )
    st.altair_chart(scatter, use_container_width=True)

# Narrative insights
st.markdown("### Automatic ESG insights")
for text in insights:
    st.markdown(f"- {text}")

# -----------------------
# ORIGINAL CHARTS (kept for familiarity)
# -----------------------

st.markdown("---")
st.subheader("Emissions & Productivity by Farm")

emissions_farm = filtered_df.groupby("farm_id", as_index=False)["total_emissions"].sum()
yield_farm = filtered_df.groupby("farm_id", as_index=False)["yield_tonnes"].sum()

c1, c2 = st.columns(2)

with c1:
    st.markdown("**Emissions per farm (kg CO₂e)**")
    st.bar_chart(emissions_farm.set_index("farm_id")["total_emissions"])

with c2:
    st.markdown("**Yield per farm (tonnes)**")
    st.bar_chart(yield_farm.set_index("farm_id")["yield_tonnes"])

# -----------------------
# DETAILED TABLE
# -----------------------

st.markdown("---")
st.subheader("Detailed data (record level)")
st.dataframe(filtered_df, use_container_width=True)

st.markdown("#### Farm-level ESG table")
st.dataframe(esg_df, use_container_width=True)
