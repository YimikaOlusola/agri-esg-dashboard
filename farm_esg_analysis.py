import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="AgriESG – Farm-level ESG Analysis",
    page_icon="🌱",
    layout="wide",
)

EF_N = 5.5      # kg CO2e per kg N fertiliser  (placeholder)
EF_DIESEL = 2.7 # kg CO2e per litre diesel     (placeholder)
EF_ELEC = 0.5   # kg CO2e per kWh electricity  (placeholder)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Add agronomic, emissions & social KPIs at row level."""
    df = df.copy()

    df["area_ha"] = df["area_ha"].replace(0, np.nan)
    df["yield_tonnes"] = df["yield_tonnes"].replace(0, np.nan)
    df["workers_total"] = df["workers_total"].replace(0, np.nan)

    # Productivity & resource intensity
    df["yield_per_ha"] = df["yield_tonnes"] / df["area_ha"]
    df["n_per_ha"] = df["fertilizer_n_kg"] / df["area_ha"]
    df["water_per_tonne"] = df["water_m3"] / df["yield_tonnes"]

    # Emissions (kg CO2e)
    df["emissions_fertilizer"] = df["fertilizer_n_kg"] * EF_N
    df["emissions_diesel"] = df["diesel_litres"] * EF_DIESEL
    df["emissions_electric"] = df["electricity_kwh"] * EF_ELEC

    df["total_emissions"] = (
        df["emissions_fertilizer"]
        + df["emissions_diesel"]
        + df["emissions_electric"]
    )
    df["emissions_per_tonne"] = df["total_emissions"] / df["yield_tonnes"]
    df["emissions_per_ha"] = df["total_emissions"] / df["area_ha"]

    # Social metrics
    df["female_share"] = df["workers_female"] / df["workers_total"]
    df["accidents_per_100_workers"] = (
        df["accidents_count"] / df["workers_total"] * 100
    )

    return df


def percentile_score(series: pd.Series, higher_is_better=True) -> pd.Series:
    """Return 0–100 percentile scores from a series."""
    s = series.copy()
    if s.dropna().nunique() <= 1:
        return pd.Series(50, index=s.index)
    ranks = s.rank(pct=True)
    if higher_is_better:
        sc = ranks * 100
    else:
        sc = (1 - ranks) * 100
    return sc.round(1)


def compute_esg_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate to farm level and compute E, S, G & ESG scores
    (relative to all farms in the uploaded dataset).
    """
    g = df.groupby("farm_id").agg(
        organisation=("organisation_name", "first"),
        country=("country", "first"),
        crop=("crop", "first"),
        year=("year", "first"),
        area_ha=("area_ha", "sum"),
        yield_tonnes=("yield_tonnes", "sum"),
        total_emissions=("total_emissions", "sum"),
        emissions_per_ha=("emissions_per_ha", "mean"),
        emissions_per_tonne=("emissions_per_tonne", "mean"),
        n_per_ha=("n_per_ha", "mean"),
        water_per_tonne=("water_per_tonne", "mean"),
        yield_per_ha=("yield_per_ha", "mean"),
        workers_total=("workers_total", "sum"),
        workers_female=("workers_female", "sum"),
        accidents_count=("accidents_count", "sum"),
        female_share=("female_share", "mean"),
        accidents_per_100_workers=("accidents_per_100_workers", "mean"),
    )

    # ---------- Environment ----------
    env = pd.DataFrame(index=g.index)
    env["emissions_per_ha"] = percentile_score(
        g["emissions_per_ha"], higher_is_better=False
    )
    env["emissions_per_tonne"] = percentile_score(
        g["emissions_per_tonne"], higher_is_better=False
    )
    env["n_per_ha"] = percentile_score(
        g["n_per_ha"], higher_is_better=False
    )
    env["water_per_tonne"] = percentile_score(
        g["water_per_tonne"], higher_is_better=False
    )
    g["E_score"] = env.mean(axis=1)

    # ---------- Social ----------
    soc = pd.DataFrame(index=g.index)
    soc["female_share"] = percentile_score(
        g["female_share"], higher_is_better=True
    )
    soc["accidents_per_100_workers"] = percentile_score(
        g["accidents_per_100_workers"], higher_is_better=False
    )
    g["S_score"] = soc.mean(axis=1)

    # ---------- Governance (simple: certification yes/no) ----------
    if "certification_scheme" in df.columns:
        # treat "None" or empty as no certification
        cert_share = df.assign(
            has_cert=lambda x: ~x["certification_scheme"]
            .fillna("None")
            .str.contains("none", case=False)
        ).groupby("farm_id")["has_cert"].mean()
        g["gov_cert"] = cert_share
        gov = pd.DataFrame(index=g.index)
        gov["gov_cert"] = percentile_score(
            g["gov_cert"], higher_is_better=True
        )
        g["G_score"] = gov.mean(axis=1)
    else:
        g["G_score"] = 50.0

    # Overall ESG: weight E=50, S=30, G=20
    g["ESG_score"] = (
        g["E_score"] * 0.5 + g["S_score"] * 0.3 + g["G_score"] * 0.2
    )

    return g.reset_index()


def safe(x, unit=""):
    return f"{x:.2f}{unit}" if pd.notna(x) else "N/A"


def generate_esg_report(row):
    """Plain-text ESG report for a single farm (row from esg_df)."""
    report = f"""
# 🌱 ESG Report — {row['organisation']} ({row['farm_id']})

## 1. Executive Summary
This report summarises the ESG performance of **{row['organisation']}**, located in **{row['country']}**, 
producing **{row['crop']}** in **{int(row['year'])}**.

Key farm details:
- Total area: **{safe(row['area_ha'], ' ha')}**
- Total yield: **{safe(row['yield_tonnes'], ' tonnes')}**
- Workers employed: **{int(row['workers_total'])}**
- Female workforce share: **{safe(row['female_share']*100, '%')}**

---

## 2. Environmental Performance

### 🌍 Emissions & Energy
- Total emissions: **{safe(row['total_emissions'], ' kg CO₂e')}**
- Emissions per tonne: **{safe(row['emissions_per_tonne'], ' kg CO₂e/t')}**
- Emissions per hectare: **{safe(row['emissions_per_ha'], ' kg CO₂e/ha')}**

### 💧 Water & Nutrients
- Water per tonne: **{safe(row['water_per_tonne'], ' m³/t')}**
- Nitrogen per hectare: **{safe(row['n_per_ha'], ' kg N/ha')}**
- Yield productivity: **{safe(row['yield_per_ha'], ' t/ha')}**

---

## 3. Social Performance

### 👩‍🌾 Workforce & Safety
- Workers: **{int(row['workers_total'])}**
- Female workers: **{int(row['workers_female'])}**
- Female share: **{safe(row['female_share']*100, '%')}**
- Accident rate: **{safe(row['accidents_per_100_workers'], ' accidents per 100 workers')}**

---

## 4. Governance

- Certification scheme: **{row.get('certification_scheme', 'Not provided')}**
- ESG scores (0–100):
  - Environment (E): **{safe(row['E_score'])}**
  - Social (S): **{safe(row['S_score'])}**
  - Governance (G): **{safe(row['G_score'])}**
  - Overall ESG: **{safe(row['ESG_score'])}**

---

## 5. Suggested KPIs & Targets
- Reduce emissions intensity by **10% in 3 years**
- Improve water efficiency by **15% per tonne**
- Increase female workforce share to **30%**
- Maintain accident rate at **0 per 100 workers**

---

## 6. Future Commitments (example)
- Expand regenerative practices (cover crops, reduced tillage)
- Improve biodiversity (hedgerows, pollinator margins)
- Increase renewable energy share on farm
- Enhance data collection for ESG reporting

---

*Report automatically generated by the AgriESG Farm Analysis Tool.*
"""
    return report


# --------------------------------------------------
# UI – FILE UPLOAD
# --------------------------------------------------
st.title("🌱 AgriESG – Farm-level ESG Dashboard & Report")
st.write(
    "Upload your farm dataset (same CSV used for the multi-farm dashboard) "
    "and then select a farm to see detailed ESG performance."
)

with st.expander("Expected CSV columns (minimum)"):
    st.markdown(
        """
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

Optional (for richer governance):  
`certification_scheme`, `region`, `county`, etc.
        """
    )

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV file to begin.")
    st.stop()

try:
    raw_df = pd.read_csv(uploaded_file, encoding="utf-8")
except UnicodeDecodeError:
    uploaded_file.seek(0)
    raw_df = pd.read_csv(uploaded_file, encoding="latin1")

required_cols = [
    "organisation_name",
    "farm_id",
    "country",
    "year",
    "crop",
    "area_ha",
    "yield_tonnes",
    "fertilizer_n_kg",
    "diesel_litres",
    "electricity_kwh",
    "water_m3",
    "workers_total",
    "workers_female",
    "accidents_count",
]

missing = [c for c in required_cols if c not in raw_df.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()

df = compute_kpis(raw_df)
esg_df = compute_esg_scores(df)

# --------------------------------------------------
# SELECT FARM
# --------------------------------------------------
st.sidebar.header("Farm selection")
farm_id = st.sidebar.selectbox("Choose a farm", esg_df["farm_id"].unique())

farm_esg = esg_df[esg_df["farm_id"] == farm_id].iloc[0]
farm_rows = df[df["farm_id"] == farm_id]

st.markdown(
    f"### 📍 {farm_esg['organisation']} — {farm_esg['crop']} "
    f"({farm_esg['country']}, {int(farm_esg['year'])})"
)

# --------------------------------------------------
# TABS: Dashboard / ESG Scores / Report
# --------------------------------------------------
tab_dashboard, tab_scores, tab_report = st.tabs(
    ["📊 Dashboard", "📈 ESG Scores", "📄 ESG Report"]
)

# ---------------------- DASHBOARD TAB ----------------------
with tab_dashboard:
    # KPI cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Area (ha)", f"{farm_esg['area_ha']:.1f}")
    with k2:
        st.metric("Yield per ha (t/ha)", safe(farm_esg["yield_per_ha"]))
    with k3:
        st.metric("Emissions per ha (kg CO₂e/ha)", safe(farm_esg["emissions_per_ha"]))
    with k4:
        st.metric("Water per tonne (m³/t)", safe(farm_esg["water_per_tonne"]))

    st.markdown("---")

    c1, c2 = st.columns(2)

    # Emissions breakdown donut
    with c1:
        st.markdown("#### 🔍 Emissions breakdown (kg CO₂e)")
        emis_parts = farm_rows[["emissions_fertilizer", "emissions_diesel", "emissions_electric"]].sum()
        emis_df = (
            emis_parts.rename_axis("source")
            .reset_index(name="kg_co2e")
        )
        donut = (
            alt.Chart(emis_df)
            .mark_arc(innerRadius=60)
            .encode(
                theta="kg_co2e:Q",
                color=alt.Color("source:N", legend=None),
                tooltip=["source", alt.Tooltip("kg_co2e:Q", format=".0f")],
            )
        )
        st.altair_chart(donut, use_container_width=True)

    # Emissions vs yield (vs portfolio avg)
    with c2:
        st.markdown("#### 📉 Emissions vs yield (comparison to portfolio)")
        comp_df = esg_df[["farm_id", "yield_per_ha", "emissions_per_ha"]].copy()
        comp_df["highlight"] = np.where(comp_df["farm_id"] == farm_id, "Selected farm", "Other farms")

        scatter = (
            alt.Chart(comp_df)
            .mark_circle()
            .encode(
                x=alt.X("yield_per_ha:Q", title="Yield (t/ha)"),
                y=alt.Y("emissions_per_ha:Q", title="Emissions (kg CO₂e/ha)"),
                color=alt.Color("highlight:N"),
                tooltip=["farm_id", alt.Tooltip("yield_per_ha:Q", format=".2f"), alt.Tooltip("emissions_per_ha:Q", format=".1f")],
            )
        )
        st.altair_chart(scatter, use_container_width=True)

    st.markdown("---")

    # Social chart
    st.markdown("#### 👩‍🌾 Social indicators")
    soc_df = esg_df[["farm_id", "female_share", "accidents_per_100_workers"]].copy()
    soc_df["female_share_pct"] = soc_df["female_share"] * 100

    soc_chart = (
        alt.Chart(soc_df)
        .transform_fold(
            ["female_share_pct", "accidents_per_100_workers"],
            as_=["indicator", "value"],
        )
        .mark_bar()
        .encode(
            x=alt.X("farm_id:N", title="Farm"),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color("indicator:N", title=None),
            tooltip=["farm_id", "indicator", alt.Tooltip("value:Q", format=".1f")],
        )
    )
    st.altair_chart(soc_chart, use_container_width=True)

# ---------------------- ESG SCORES TAB ----------------------
with tab_scores:
    st.markdown("#### ESG pillar scores (0–100, relative to portfolio)")
    score_df = pd.DataFrame(
        {
            "Pillar": ["Environment", "Social", "Governance", "Overall ESG"],
            "Score": [
                farm_esg["E_score"],
                farm_esg["S_score"],
                farm_esg["G_score"],
                farm_esg["ESG_score"],
            ],
        }
    )

    bar = (
        alt.Chart(score_df)
        .mark_bar()
        .encode(
            x=alt.X("Pillar:N"),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100])),
            tooltip=["Pillar", alt.Tooltip("Score:Q", format=".1f")],
        )
    )
    st.altair_chart(bar, use_container_width=True)

    st.write(
        "- Scores are **relative to all farms in the uploaded dataset** "
        "(percentile-based).\n"
        "- Environment weighs emissions, nitrogen and water intensity.\n"
        "- Social captures gender balance and accident rates.\n"
        "- Governance is currently driven by certification presence."
    )

# ---------------------- REPORT TAB ----------------------
with tab_report:
    st.markdown("#### Auto-generated ESG narrative")
    report_text = generate_esg_report(farm_esg)
    st.markdown(report_text)
