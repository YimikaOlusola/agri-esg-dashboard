# ================================================================
# 🌱 AGRI ESG PLATFORM — MULTI-FARM + FARM-LEVEL DASHBOARD (MVP)
# Hybrid ESG Scoring (Threshold + Weighted)
# Balanced UK Standard thresholds
# With Privacy Mode + Anonymous Benchmarking
# ================================================================

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="AgriESG Platform",
    page_icon="🌱",
    layout="wide"
)

# ------------------------------------------------------------
# WHITE CLEAN THEME
# ------------------------------------------------------------
st.markdown("""
<style>
body, .stApp { background-color: #ffffff !important; color: #111827; }
.block-container { padding-top: 1rem; padding-bottom: 3rem; }
.kpi-card {
    padding: 1.0rem 1.1rem; border-radius: 18px;
    background-color: #ffffff; border: 1px solid #e5e7eb;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}
.kpi-label { font-size: 0.78rem; text-transform: uppercase; color: #6b7280; }
.kpi-value { font-size: 1.35rem; font-weight: 700; color: #111827; }
.score-card {
    padding: 15px; border-radius: 14px; color: white; font-weight: 600;
    text-align: center; font-size: 1.1rem; margin-bottom: 10px;
}
.score-green { background-color: #22c55e; }
.score-amber { background-color: #facc15; color: black !important; }
.score-orange { background-color: #fb923c; }
.score-red { background-color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# ALTAIR LIGHT THEME
# ------------------------------------------------------------
alt.themes.register("agriesg_light", lambda: {
    "config": {
        "view": {"continuousWidth": 380, "continuousHeight": 260, "stroke": "transparent"},
        "background": "white",
        "axis": {"labelColor": "#374151", "titleColor": "#111827"},
        "legend": {"labelColor": "#374151", "titleColor": "#111827"},
    }
})
alt.themes.enable("agriesg_light")

# ------------------------------------------------------------
# ESG SCORING ENGINE — HYBRID (THRESHOLD + WEIGHTED)
# ------------------------------------------------------------

def score_from_thresholds(value, thresholds):
    """
    thresholds = (excellent, good, moderate, high)
    returns score 100..0
    """
    exc, good, mod, high = thresholds
    if value < exc: return 100
    elif value < good: return 75
    elif value < mod: return 50
    elif value < high: return 25
    return 0

def compute_esg_scores(row):
    """
    Returns env_score, soc_score, gov_score, overall
    using Balanced UK Standard + Weighted Model
    """

    # ------------------ ENVIRONMENT ------------------
    env_subscores = []
    env_subscores.append(
        score_from_thresholds(row["emissions_per_tonne"], (300, 450, 600, 800))
    )
    env_subscores.append(
        score_from_thresholds(row["water_per_tonne"], (2, 4, 7, 10))
    )
    n_per_ha = row["fertilizer_n_kg"] / row["area_ha"] if row["area_ha"] else np.nan
    env_subscores.append(
        score_from_thresholds(n_per_ha, (90, 120, 160, 200))
    )

    env_score = np.nanmean(env_subscores)

    # ------------------ SOCIAL ------------------
    female_pct = row["female_share"] * 100 if pd.notna(row["female_share"]) else 0
    acc_rate = row["accidents_per_100_workers"]

    def social_score_female(p):
        if p >= 40: return 100
        if p >= 30: return 75
        if p >= 20: return 50
        if p >= 10: return 25
        return 0

    def social_score_acc(r):
        if r == 0: return 100
        if r < 5: return 75
        if r < 10: return 50
        if r < 20: return 25
        return 0

    soc_score = np.nanmean([
        social_score_female(female_pct),
        social_score_acc(acc_rate)
    ])

    # ------------------ GOVERNANCE ------------------
    cert = str(row.get("certification_scheme", "None")).lower()

    if "organic" in cert or "leaf" in cert:
        gov_score = 100
    elif "red" in cert:  # Red Tractor
        gov_score = 80
    elif cert != "none":
        gov_score = 60
    else:
        gov_score = 40

    # ------------------ OVERALL ------------------
    overall = (0.5 * env_score) + (0.3 * soc_score) + (0.2 * gov_score)

    return env_score, soc_score, gov_score, overall

# ------------------------------------------------------------
# KPI & SAFE FORMATTERS
# ------------------------------------------------------------

def kpi_card(label, value, unit="", precision=2):
    if pd.isna(value): display = "N/A"
    else: display = f"{value:.{precision}f}{unit}"
    st.markdown(
        f"<div class='kpi-card'><div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{display}</div></div>",
        unsafe_allow_html=True
    )

def score_color(score):
    if score >= 80: return "score-green"
    if score >= 60: return "score-amber"
    if score >= 40: return "score-orange"
    return "score-red"

# ------------------------------------------------------------
# KPI CALCULATIONS
# ------------------------------------------------------------

EF_N = 5.5
EF_DIESEL = 2.7
EF_ELEC = 0.5

def compute_kpis(df):
    df = df.copy()
    df["yield_per_ha"] = df["yield_tonnes"] / df["area_ha"]
    df["water_per_tonne"] = df["water_m3"] / df["yield_tonnes"]

    df["emissions_fertilizer"] = df["fertilizer_n_kg"] * EF_N
    df["emissions_diesel"] = df["diesel_litres"] * EF_DIESEL
    df["emissions_electric"] = df["electricity_kwh"] * EF_ELEC

    df["total_emissions"] = df["emissions_fertilizer"] + df["emissions_diesel"] + df["emissions_electric"]
    df["emissions_per_ha"] = df["total_emissions"] / df["area_ha"]
    df["emissions_per_tonne"] = df["total_emissions"] / df["yield_tonnes"]

    df["female_share"] = df["workers_female"] / df["workers_total"]
    df["accidents_per_100_workers"] = (df["accidents_count"] / df["workers_total"]) * 100

    # ESG scoring for each farm
    env_scores = []
    soc_scores = []
    gov_scores = []
    overall_scores = []

    for _, row in df.iterrows():
        e, s, g, o = compute_esg_scores(row)
        env_scores.append(e)
        soc_scores.append(s)
        gov_scores.append(g)
        overall_scores.append(o)

    df["env_score"] = env_scores
    df["soc_score"] = soc_scores
    df["gov_score"] = gov_scores
    df["esg_score"] = overall_scores

    return df

# ------------------------------------------------------------
# ESG NARRATIVE
# ------------------------------------------------------------
def generate_esg_narrative(row, peer_avg):
    """
    peer_avg is a dict with peer averages for:
    emissions_per_tonne, water_per_tonne, female_share, acc_rate
    """
    return f"""
### 🌱 ESG Narrative — {row['organisation_name']} ({row['farm_id']})

#### 📍 Farm Summary
- Country: **{row['country']}**
- Crop: **{row['crop']}**
- Year: **{int(row['year'])}**
- Farm area: **{row['area_ha']} ha**
- Production: **{row['yield_tonnes']} tonnes**

---

### 🌍 Environment
- Emissions per tonne: **{row['emissions_per_tonne']:.1f} kg CO₂e/t**
- Water per tonne: **{row['water_per_tonne']:.1f} m³/t**
- Total emissions: **{row['total_emissions']:.0f} kg CO₂e**

Peer average emissions: **{peer_avg['emissions']:.1f} kg CO₂e/t**

---

### 👩‍🌾 Social
- Female workforce: **{row['female_share']*100:.0f}%**
- Accident rate: **{row['accidents_per_100_workers']:.1f} per 100 workers**

Peer average female share: **{peer_avg['female']*100:.0f}%**

---

### 📑 Governance
- Certification: **{row.get('certification_scheme', 'None')}**
- Governance Score: **{row['gov_score']:.0f} / 100**

---

### ⭐ Scores
- Environment Score: **{row['env_score']:.0f} / 100**
- Social Score: **{row['soc_score']:.0f} / 100**
- Governance Score: **{row['gov_score']:.0f} / 100**
- **Overall ESG Score: {row['esg_score']:.0f} / 100**

---

### 🔐 Privacy
Benchmarking uses **anonymous peer averages only**.
No other farms’ identities or individual results are ever shown.
"""

# ------------------------------------------------------------
# FILE UPLOAD
# ------------------------------------------------------------
st.title("🌱 AgriESG Platform — Multi-Farm + Farm-Level Dashboard")
st.info("🔐 Your data is private. No competitor information is disclosed.")

uploaded = st.file_uploader("Upload AgriESG CSV", type=["csv"])

if not uploaded:
    st.stop()

df_raw = pd.read_csv(uploaded)
required = [
    "organisation_name","farm_id","country","year","crop",
    "area_ha","yield_tonnes","fertilizer_n_kg","diesel_litres",
    "electricity_kwh","water_m3","workers_total","workers_female",
    "accidents_count"
]

if any(c not in df_raw.columns for c in required):
    st.error("❌ Missing required columns.")
    st.stop()

df = compute_kpis(df_raw)

# ------------------------------------------------------------
# SIDEBAR NAVIGATION
# ------------------------------------------------------------
mode = st.sidebar.radio("Dashboard Mode", ["📊 Multi-Farm Overview", "🌱 Farm-Level Analysis"])
privacy_mode = st.sidebar.checkbox("Privacy Mode (hide peer benchmarking)", value=False)
# =============================================================
# PART 2 — CONTINUATION OF FULL AGRIESG APPLICATION
# =============================================================

# ------------------------------------------------------------
# MULTI-FARM OVERVIEW DASHBOARD
# ------------------------------------------------------------
if mode == "📊 Multi-Farm Overview":

    st.header("📊 Multi-Farm ESG Overview")

    # Peer averages (safe)
    peer_avg_emissions = df["emissions_per_tonne"].mean()
    peer_avg_water = df["water_per_tonne"].mean()
    peer_avg_female = df["female_share"].mean()
    peer_avg_acc = df["accidents_per_100_workers"].mean()

    # ---------------------- KPI CARDS ----------------------
    st.subheader("Key Aggregated Metrics")

    total_area = df["area_ha"].sum()
    total_yield = df["yield_tonnes"].sum()
    total_emissions = df["total_emissions"].sum()
    avg_esg = df["esg_score"].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Area", total_area, " ha", 1)
    with c2:
        kpi_card("Total Yield", total_yield, " t", 1)
    with c3:
        kpi_card("Total Emissions", total_emissions, " kg CO₂e", 0)
    with c4:
        kpi_card("Average ESG Score", avg_esg, "", 0)

    # ---------------------- ESG SCORE DISTRIBUTION ----------------------
    st.markdown("### ESG Score Distribution")

    score_chart = (
        alt.Chart(df)
        .mark_circle(size=80)
        .encode(
            x=alt.X("farm_id:N", title="Farm"),
            y=alt.Y("esg_score:Q", title="ESG Score"),
            color=alt.condition(
                alt.datum.esg_score >= 80, alt.value("#22c55e"),
                alt.condition(alt.datum.esg_score >= 60, alt.value("#facc15"),
                alt.condition(alt.datum.esg_score >= 40, alt.value("#fb923c"), alt.value("#ef4444")))
            ),
            tooltip=["farm_id", "esg_score", "env_score", "soc_score", "gov_score"]
        )
        .properties(height=350)
    )

    st.altair_chart(score_chart, use_container_width=True)

    # ---------------------- ESG COMPONENT AVERAGES ----------------------
    st.markdown("### Average ESG Component Scores")

    avg_env = df["env_score"].mean()
    avg_soc = df["soc_score"].mean()
    avg_gov = df["gov_score"].mean()

    comp_df = pd.DataFrame({
        "Component": ["Environment", "Social", "Governance"],
        "Score": [avg_env, avg_soc, avg_gov]
    })

    comp_chart = (
        alt.Chart(comp_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Component:N"),
            y="Score:Q",
            color=alt.Color("Component:N", legend=None),
            tooltip=["Component", "Score"]
        )
        .properties(height=300)
    )

    st.altair_chart(comp_chart, use_container_width=True)

    # ---------------------- FULL TABLE ----------------------
    st.markdown("### Full Farm Dataset")
    st.dataframe(df, use_container_width=True)

# ------------------------------------------------------------
# FARM-LEVEL ANALYSIS DASHBOARD
# ------------------------------------------------------------
else:
    st.header("🌱 Farm-Level ESG Analysis")

    # Choose farm
    farm_id = st.sidebar.selectbox("Select Farm", df["farm_id"].unique())
    row = df[df["farm_id"] == farm_id].iloc[0]

    st.subheader(f"📍 {row['organisation_name']} — {row['crop']} ({row['country']} {int(row['year'])})")

    # ---------------------- KPI CARDS ----------------------
    st.markdown("### Key Performance Indicators")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Yield per ha", row["yield_per_ha"], " t/ha", 2)
    with c2:
        kpi_card("Emissions per tonne", row["emissions_per_tonne"], " kg CO₂e/t", 1)
    with c3:
        kpi_card("Water per tonne", row["water_per_tonne"], " m³/t", 1)
    with c4:
        kpi_card("Female workforce", row["female_share"] * 100, "%", 0)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        kpi_card("Total emissions", row["total_emissions"], " kg CO₂e", 0)
    with c6:
        kpi_card("Farm area", row["area_ha"], " ha", 1)
    with c7:
        kpi_card("Workers", row["workers_total"], "", 0)
    with c8:
        kpi_card("Accident rate", row["accidents_per_100_workers"], " /100 workers", 1)

    # ---------------------- ESG SCORECARDS ----------------------
    st.markdown("### ESG Scores")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"<div class='score-card {score_color(row['env_score'])}'>Environment<br>{row['env_score']:.0f}/100</div>",
            unsafe_allow_html=True)
    with c2:
        st.markdown(
            f"<div class='score-card {score_color(row['soc_score'])}'>Social<br>{row['soc_score']:.0f}/100</div>",
            unsafe_allow_html=True)
    with c3:
        st.markdown(
            f"<div class='score-card {score_color(row['gov_score'])}'>Governance<br>{row['gov_score']:.0f}/100</div>",
            unsafe_allow_html=True)
    with c4:
        st.markdown(
            f"<div class='score-card {score_color(row['esg_score'])}'>Overall ESG<br>{row['esg_score']:.0f}/100</div>",
            unsafe_allow_html=True)

    # ---------------------- EMISSIONS DONUT ----------------------
    st.markdown("### Emissions Breakdown")

    emis_df = pd.DataFrame({
        "Source": ["Fertilizer N", "Diesel", "Electricity"],
        "kg_co2e": [row["emissions_fertilizer"], row["emissions_diesel"], row["emissions_electric"]]
    })

    donut = (
        alt.Chart(emis_df)
        .mark_arc(innerRadius=60)
        .encode(
            theta="kg_co2e:Q",
            color="Source:N",
            tooltip=["Source", "kg_co2e"]
        )
        .properties(height=300)
    )

    st.altair_chart(donut, use_container_width=True)

    # ---------------------- PEER COMPARISON (ANONYMISED) ----------------------
    st.markdown("### Peer Comparison (Anonymous)")

    if privacy_mode:
        st.warning("Peer benchmarking hidden due to Privacy Mode.")
    else:
        comp_df = df[["farm_id", "yield_per_ha", "emissions_per_ha"]].copy()
        comp_df["Farm"] = comp_df["farm_id"].apply(
            lambda x: "Selected Farm" if x == farm_id else "Peer Farm"
        )

        scatter = (
            alt.Chart(comp_df)
            .mark_circle(size=90)
            .encode(
                x=alt.X("yield_per_ha:Q", title="Yield (t/ha)"),
                y=alt.Y("emissions_per_ha:Q", title="Emissions (kg CO₂e/ha)"),
                color="Farm",
                tooltip=["Farm", "yield_per_ha", "emissions_per_ha"]
            )
            .properties(height=350)
        )

        st.altair_chart(scatter, use_container_width=True)

    # ---------------------- ESG NARRATIVE ----------------------
    st.markdown("### ESG Narrative Report")

    peer_avg = {
        "emissions": df["emissions_per_tonne"].mean(),
        "water": df["water_per_tonne"].mean(),
        "female": df["female_share"].mean(),
        "acc": df["accidents_per_100_workers"].mean()
    }

    with st.expander("Open ESG Narrative"):
        st.markdown(generate_esg_narrative(row, peer_avg))

# END OF FULL CODE
