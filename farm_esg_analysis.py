# ================================================================
# 🌱 AGRIESG PLATFORM — MULTI-FARM & FARM/ENTERPRISE/CROP DASHBOARD
# Hybrid ESG Scoring (Threshold + Weighted, Balanced UK Standard)
# Privacy Mode + Anonymous Benchmarking + PDF Export
# Supports Simple (farm), Standard (enterprise), Advanced (crop) modes
# ================================================================

import base64

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from fpdf import FPDF
from PIL import Image

# ------------------------------------------------------------
# PAGE CONFIG (logo as page icon)
# ------------------------------------------------------------

icon_img = Image.open("agriesg_icon.png")

st.set_page_config(
    page_title="AgriESG Platform",
    page_icon=icon_img,
    layout="wide",
)

# ------------------------------------------------------------
# GLOBAL STYLING (dark shell + white panel)
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --agri-bg: #020617;
        --panel-bg: #ffffff;
        --accent: #16a34a;
        --accent-soft: #dcfce7;
        --accent-strong: #15803d;
        --text-main: #0f172a;
        --text-muted: #6b7280;
        --border-soft: #e5e7eb;
    }

    html, body, [class*="css"] {
        font-family: "Tenorite", system-ui, -apple-system, BlinkMacSystemFont,
                     "Segoe UI", sans-serif;
    }

    body, .stApp {
        background: radial-gradient(circle at top left, #022c22, #020617 55%);
        color: var(--text-main);
    }

    .block-container {
        padding: 2rem 2.5rem 3rem;
        max-width: 1300px;
        margin: 1.75rem auto 2.5rem auto;
        background: var(--panel-bg);
        border-radius: 24px;
        box-shadow: 0 26px 60px rgba(15, 23, 42, 0.32);
    }

    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.98) !important;
        border-right: 1px solid rgba(148,163,184,0.35);
    }
    section[data-testid="stSidebar"] * {
        color: #e5e7eb !important;
        font-size: 0.9rem;
    }

    .section-eyebrow {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        color: var(--text-muted);
        margin-bottom: 0.1rem;
    }
    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        color: var(--text-main);
    }

    .kpi-label-inline {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: var(--text-muted);
        text-align: center;
        margin-top: -0.3rem;
    }

    div[data-testid="stFileUploader"] > label div[data-testid="stFileUploaderDropzone"] {
        background-color: #f3f4f6;
        border: 1px dashed #d1d5db;
        color: #111827;
    }
    div[data-testid="stFileUploader"] div[role="list"] div {
        background-color: #f9fafb;
        border-radius: 0.5rem;
        padding: 0.25rem 0.75rem;
    }
    div[data-testid="stFileUploader"] div[role="list"] span {
        color: #111827 !important;
    }
    div[data-testid="stFileUploader"] button[kind="secondary"] {
        background-color: var(--accent) !important;
        color: #ffffff !important;
        border-radius: 999px !important;
        padding: 0.25rem 0.9rem !important;
        font-weight: 500 !important;
        border: none !important;
    }

    div[data-testid="stAlert"] {
        background-color: #fef9c3 !important;
        border: 1px solid #facc15 !important;
    }
    div[data-testid="stAlert"] * {
        color: #111827 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# ALTAIR THEME (uniform green palette)
# ------------------------------------------------------------
alt.themes.register(
    "agriesg_light",
    lambda: {
        "config": {
            "view": {
                "continuousWidth": 380,
                "continuousHeight": 260,
                "stroke": "transparent",
            },
            "background": "white",
            "axis": {
                "labelColor": "#4b5563",
                "titleColor": "#111827",
                "grid": True,
                "gridColor": "#e5e7eb",
            },
            "legend": {"labelColor": "#374151", "titleColor": "#111827"},
            "range": {
                "category": [
                    "#16a34a", "#22c55e", "#4ade80", "#bbf7d0",
                    "#0f766e", "#22c55e", "#16a34a", "#4ade80",
                ],
            },
        }
    },
)
alt.themes.enable("agriesg_light")

# ------------------------------------------------------------
# BRANDING: LOGO IN HEADER + SIDEBAR
# ------------------------------------------------------------

with open("agriesg_icon.png", "rb") as f:
    encoded_logo = base64.b64encode(f.read()).decode()

header_col1, header_col2 = st.columns([1, 6])
with header_col1:
    st.image(icon_img, width=78)
with header_col2:
    st.markdown(
        """
        <h1 style="margin-bottom:0.1rem; margin-top:0.1rem;">
            ESG Dashboard — Farms, Enterprises & Crops
        </h1>
        <p style="font-size:0.98rem; color:#4b5563; margin-top:0;">
            Analyse emissions, water, social indicators and governance at the level of detail you have:
            whole-farm, main enterprises or individual crops.
        </p>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

st.sidebar.markdown(
    f"""
    <div style="text-align:center;">
        <img src="data:image/png;base64,{encoded_logo}" width="80" style="margin-bottom:6px;">
        <p style="font-size:14px; color:#f9fafb; margin-bottom:0;">
            <strong>AgriESG Dashboard</strong>
        </p>
        <p style="font-size:11px; color:#9ca3af; margin-top:-4px;">
            v1.0 — Beta
        </p>
        <hr style="margin-top:6px; margin-bottom:4px; border-color:#4b5563;">
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------
EF_N = 5.5       # kg CO2e per kg N fertiliser
EF_DIESEL = 2.7  # kg CO2e per litre diesel
EF_ELEC = 0.5    # kg CO2e per kWh electricity


# ------------------------------------------------------------
# ESG SCORING ENGINE — HYBRID (THRESHOLD + WEIGHTED)
# ------------------------------------------------------------
def score_from_thresholds(value, thresholds):
    exc, good, mod, high = thresholds
    if pd.isna(value):
        return np.nan
    if value < exc:
        return 100
    elif value < good:
        return 75
    elif value < mod:
        return 50
    elif value < high:
        return 25
    return 0


def compute_esg_scores(row):
    # ---------- ENVIRONMENT ----------
    env_subscores = []
    env_subscores.append(
        score_from_thresholds(row["emissions_per_tonne"], (300, 450, 600, 800))
    )
    env_subscores.append(
        score_from_thresholds(row["water_per_tonne"], (2, 4, 7, 10))
    )

    if row["area_ha"] and not pd.isna(row["area_ha"]):
        n_per_ha = row["fertilizer_n_kg"] / row["area_ha"]
    else:
        n_per_ha = np.nan

    env_subscores.append(
        score_from_thresholds(n_per_ha, (90, 120, 160, 200))
    )

    env_score = np.nanmean(env_subscores)

    # ---------- SOCIAL ----------
    female_pct = row["female_share"] * 100 if pd.notna(row["female_share"]) else 0
    acc_rate = row["accidents_per_100_workers"]

    def social_score_female(p):
        if p >= 40:
            return 100
        if p >= 30:
            return 75
        if p >= 20:
            return 50
        if p >= 10:
            return 25
        return 0

    def social_score_acc(r):
        if pd.isna(r):
            return np.nan
        if r == 0:
            return 100
        if r < 5:
            return 75
        if r < 10:
            return 50
        if r < 20:
            return 25
        return 0

    soc_score = np.nanmean(
        [social_score_female(female_pct), social_score_acc(acc_rate)]
    )

    # ---------- GOVERNANCE ----------
    cert = str(row.get("certification_scheme", "None")).lower()

    if "organic" in cert or "leaf" in cert:
        gov_score = 100
    elif "red" in cert:
        gov_score = 80
    elif cert != "none":
        gov_score = 60
    else:
        gov_score = 40

    # ---------- OVERALL ----------
    overall = 0.5 * env_score + 0.3 * soc_score + 0.2 * gov_score

    return env_score, soc_score, gov_score, overall


# ------------------------------------------------------------
# KPI HELPERS
# ------------------------------------------------------------
def score_color(score):
    if score >= 80:
        return "score-green"
    if score >= 60:
        return "score-amber"
    if score >= 40:
        return "score-orange"
    return "score-red"


def relative_position(df, column, value, higher_is_better=True) -> float:
    """
    Return a 0–100 value showing where 'value' sits within the range
    of the uploaded dataset for that column.
    """
    series = df[column].dropna()
    if series.empty or series.nunique() == 1 or pd.isna(value):
        return 50.0

    min_v = float(series.min())
    max_v = float(series.max())
    if max_v == min_v:
        return 50.0

    if higher_is_better:
        pct = (value - min_v) / (max_v - min_v)
    else:
        pct = (max_v - value) / (max_v - min_v)

    pct = max(0.0, min(1.0, pct))
    return pct * 100.0


def circular_kpi(label: str, value, unit: str, precision: int, pct: float):
    """
    Render a circular KPI gauge with the value in the centre and a
    green ring indicating 'pct' (0–100) relative performance.
    """
    if pd.isna(value):
        value_text = "N/A"
    else:
        value_text = f"{value:.{precision}f}{unit}"

    data = pd.DataFrame(
        {"part": ["Filled", "Remaining"], "value": [pct, max(0, 100 - pct)]}
    )

    arc = (
        alt.Chart(data)
        .mark_arc(innerRadius=38, outerRadius=58)
        .encode(
            theta="value:Q",
            color=alt.Color(
                "part:N",
                scale=alt.Scale(range=["#16a34a", "#e5e7eb"]),
                legend=None,
            ),
        )
    )

    text_df = pd.DataFrame({"value": [value_text]})
    text = (
        alt.Chart(text_df)
        .mark_text(color="#0f172a", fontSize=16, fontWeight="bold")
        .encode(text="value:N")
    )

    chart = alt.layer(arc, text).properties(width=150, height=150)

    st.altair_chart(chart, use_container_width=False)
    st.markdown(
        f"<div class='kpi-label-inline'>{label}</div>",
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# KPI CALCULATIONS FROM RAW DF
# ------------------------------------------------------------
def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["area_ha"] = df["area_ha"].replace(0, np.nan)
    df["yield_tonnes"] = df["yield_tonnes"].replace(0, np.nan)
    df["workers_total"] = df["workers_total"].replace(0, np.nan)

    df["yield_per_ha"] = df["yield_tonnes"] / df["area_ha"]
    df["water_per_tonne"] = df["water_m3"] / df["yield_tonnes"]

    df["emissions_fertilizer"] = df["fertilizer_n_kg"] * EF_N
    df["emissions_diesel"] = df["diesel_litres"] * EF_DIESEL
    df["emissions_electric"] = df["electricity_kwh"] * EF_ELEC

    df["total_emissions"] = (
        df["emissions_fertilizer"]
        + df["emissions_diesel"]
        + df["emissions_electric"]
    )
    df["emissions_per_ha"] = df["total_emissions"] / df["area_ha"]
    df["emissions_per_tonne"] = df["total_emissions"] / df["yield_tonnes"]

    df["female_share"] = df["workers_female"] / df["workers_total"]
    df["accidents_per_100_workers"] = (
        df["accidents_count"] / df["workers_total"] * 100
    )

    if "detail_level" not in df.columns:
        df["detail_level"] = "farm"
    if "enterprise_type" not in df.columns:
        df["enterprise_type"] = ""

    df["detail_level"] = df["detail_level"].fillna("farm").str.lower()
    df["enterprise_type"] = df["enterprise_type"].fillna("")

    env_scores, soc_scores, gov_scores, esg_scores = [], [], [], []
    for _, r in df.iterrows():
        e, s, g, o = compute_esg_scores(r)
        env_scores.append(e)
        soc_scores.append(s)
        gov_scores.append(g)
        esg_scores.append(o)

    df["env_score"] = env_scores
    df["soc_score"] = soc_scores
    df["gov_score"] = gov_scores
    df["esg_score"] = esg_scores

    def build_label(r):
        dl = str(r["detail_level"]).lower()
        ent = str(r["enterprise_type"]).strip()
        crop = str(r["crop"]).strip()

        if dl == "farm":
            main = ent if ent else "Whole farm"
        elif dl == "enterprise":
            main = ent if ent else crop
        else:
            if ent and crop:
                main = f"{crop} ({ent})"
            else:
                main = crop or ent or "Record"

        return f"{r['organisation_name']} — {main} ({r['country']} {int(r['year'])})"

    df["record_label"] = df.apply(build_label, axis=1)

    return df


# ------------------------------------------------------------
# ESG NARRATIVE
# ------------------------------------------------------------
def generate_esg_narrative(row: pd.Series, peer_avg: dict) -> str:
    female_pct = row["female_share"] * 100 if pd.notna(row["female_share"]) else 0

    return f"""
### 🌱 ESG Narrative — {row['organisation_name']} ({row['farm_id']})

**Location & enterprise**

- Country: **{row['country']}**
- Enterprise / crop: **{row['enterprise_type'] or row['crop']}**
- Reporting year: **{int(row['year'])}**
- Farmed area for this record: **{row['area_ha']:.1f} ha**
- Production: **{row['yield_tonnes']:.1f} tonnes**

---

#### 🌍 Environment

- Emissions per tonne: **{row['emissions_per_tonne']:.1f} kg CO₂e/t**
- Water per tonne: **{row['water_per_tonne']:.1f} m³/t**
- Total emissions: **{row['total_emissions']:.0f} kg CO₂e**

Peer average emissions intensity is approximately **{peer_avg['emissions']:.1f} kg CO₂e/t**.

---

#### 👩‍🌾 Social

- Female workforce: **{female_pct:.0f}%**
- Accident rate: **{row['accidents_per_100_workers']:.1f} per 100 workers**

Peer average female share is around **{peer_avg['female']*100:.0f}%**.

---

#### 📑 Governance

- Certification scheme: **{row.get('certification_scheme', 'None')}**
- Governance score: **{row['gov_score']:.0f} / 100**

---

#### ⭐ ESG scores

- Environment score: **{row['env_score']:.0f} / 100**
- Social score: **{row['soc_score']:.0f} / 100**
- Governance score: **{row['gov_score']:.0f} / 100**
- **Overall ESG score: {row['esg_score']:.0f} / 100**

---

🔐 *Peer benchmarks are anonymised. No other farm's identity or individual data is shown.*
"""


# ------------------------------------------------------------
# SIMPLE PDF GENERATOR
# ------------------------------------------------------------
def narrative_to_pdf_bytes(title: str, narrative_md: str) -> bytes:
    cleaned = (
        narrative_md.replace("###", "")
        .replace("####", "")
        .replace("**", "")
        .replace("*", "")
    )

    def safe_latin1(text: str) -> str:
        return text.encode("latin-1", "replace").decode("latin-1")

    title_safe = safe_latin1(title)
    text_safe = safe_latin1(cleaned)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, 15)

    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 8, title_safe)
    pdf.ln(5)

    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, text_safe)

    pdf_out = pdf.output(dest="S")

    if pdf_out is None:
        return b""
    if isinstance(pdf_out, (bytes, bytearray)):
        return bytes(pdf_out)
    return pdf_out.encode("latin-1", "replace")


# ------------------------------------------------------------
# INFO + HOW-TO
# ------------------------------------------------------------
st.info(
    "🔐 **Your data is private.** No competitor information is ever shown — "
    "benchmarking uses anonymous peer averages only."
)

with st.expander("How to use AgriESG with different data levels"):
    st.markdown(
        """
- **Simple mode – Whole farm**  
  One row per farm. Use `detail_level = farm`, `enterprise_type = Whole farm`, `crop = Mixed`.
- **Standard mode – Main enterprises**  
  One row per enterprise (e.g. Arable, Dairy). Use `detail_level = enterprise`.
- **Advanced mode – Per crop**  
  One row per crop/rotation. Use `detail_level = crop`.

If you’re unsure, start with **Simple mode (Whole farm)** — your ESG scores will still be useful.
"""
    )

# ------------------------------------------------------------
# FILE UPLOAD
# ------------------------------------------------------------
uploaded = st.file_uploader("Upload your AgriESG CSV file", type=["csv"])

if uploaded is None:
    st.stop()

df_raw = pd.read_csv(uploaded)

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

missing = [c for c in required_cols if c not in df_raw.columns]
if missing:
    st.error("❌ Missing required columns: " + ", ".join(missing))
    st.stop()

optional_cols = ["detail_level", "enterprise_type", "certification_scheme"]
missing_opt = [c for c in optional_cols if c not in df_raw.columns]
if missing_opt:
    st.warning(
        "Optional columns not found (using simple farm-level mode): "
        + ", ".join(missing_opt)
    )

df = compute_kpis(df_raw)

# ------------------------------------------------------------
# SIDEBAR NAVIGATION & PRIVACY TOGGLE
# ------------------------------------------------------------
mode = st.sidebar.radio(
    "Dashboard mode",
    ["📊 Multi-Farm Overview", "🌱 Farm / Enterprise / Crop Analysis"],
)
privacy_mode = st.sidebar.checkbox(
    "Privacy Mode (hide peer benchmarking)",
    value=False,
    help="When enabled, peer comparison plots are hidden.",
)

# ------------------------------------------------------------
# MULTI-FARM OVERVIEW
# ------------------------------------------------------------
if mode == "📊 Multi-Farm Overview":
    st.markdown(
        "<div class='section-eyebrow'>Overview</div>"
        "<div class='section-title'>📊 Multi-Farm ESG Overview</div>",
        unsafe_allow_html=True,
    )

    total_area = df["area_ha"].sum()
    total_yield = df["yield_tonnes"].sum()
    total_emissions = df["total_emissions"].sum()
    avg_esg = df["esg_score"].mean()

    st.markdown("<div class='section-eyebrow'>Key metrics</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total area (ha)", f"{total_area:,.1f}")
    with c2:
        st.metric("Total yield (t)", f"{total_yield:,.1f}")
    with c3:
        st.metric("Total emissions (kg CO₂e)", f"{total_emissions:,.0f}")
    with c4:
        st.metric("Average ESG score", f"{avg_esg:.0f} / 100")

    st.markdown(
        "<div class='section-eyebrow'>Distribution</div>"
        "<div class='section-title'>ESG score distribution</div>",
        unsafe_allow_html=True,
    )

    df["esg_band"] = pd.cut(
        df["esg_score"],
        bins=[-0.1, 40, 60, 80, 100.1],
        labels=["Needs improvement", "Moderate", "Good", "Excellent"],
    )

    score_chart = (
        alt.Chart(df)
        .mark_circle(size=80)
        .encode(
            x=alt.X("farm_id:N", title="Farm ID"),
            y=alt.Y("esg_score:Q", title="ESG score"),
            color=alt.Color(
                "esg_band:N",
                title="ESG band",
                scale=alt.Scale(
                    domain=[
                        "Needs improvement",
                        "Moderate",
                        "Good",
                        "Excellent",
                    ],
                    range=["#b91c1c", "#f97316", "#eab308", "#16a34a"],
                ),
            ),
            tooltip=[
                "farm_id",
                "enterprise_type",
                "crop",
                alt.Tooltip("year:Q", title="Year", format=".0f"),
                alt.Tooltip("esg_score:Q", title="ESG score", format=".0f"),
                alt.Tooltip("env_score:Q", title="Environment", format=".0f"),
                alt.Tooltip("soc_score:Q", title="Social", format=".0f"),
                alt.Tooltip("gov_score:Q", title="Governance", format=".0f"),
                "esg_band",
            ],
        )
        .properties(height=350)
    )

    st.altair_chart(score_chart, use_container_width=True)

    st.markdown(
        "<div class='section-eyebrow'>Components</div>"
        "<div class='section-title'>Average ESG component scores</div>",
        unsafe_allow_html=True,
    )

    comp_df = pd.DataFrame(
        {
            "Component": ["Environment", "Social", "Governance"],
            "Score": [
                df["env_score"].mean(),
                df["soc_score"].mean(),
                df["gov_score"].mean(),
            ],
        }
    )

    comp_chart = (
        alt.Chart(comp_df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("Component:N", title=""),
            y=alt.Y("Score:Q", title="Average score", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(
                "Component:N",
                legend=None,
                scale=alt.Scale(range=["#16a34a", "#22c55e", "#4ade80"]),
            ),
            tooltip=["Component", alt.Tooltip("Score:Q", format=".0f")],
        )
        .properties(height=260)
    )

    st.altair_chart(comp_chart, use_container_width=True)

    st.markdown(
        "<div class='section-eyebrow'>Data</div>"
        "<div class='section-title'>Full dataset (one row per farm / enterprise / crop)</div>",
        unsafe_allow_html=True,
    )
    st.dataframe(df, use_container_width=True)

# ------------------------------------------------------------
# FARM / ENTERPRISE / CROP ANALYSIS
# ------------------------------------------------------------
else:
    st.markdown(
        "<div class='section-eyebrow'>Drill-down</div>"
        "<div class='section-title'>🌱 Farm / Enterprise / Crop ESG Analysis</div>",
        unsafe_allow_html=True,
    )

    record_label = st.sidebar.selectbox(
        "Select a record",
        df["record_label"].unique(),
        help="Each row may represent a whole farm, an enterprise (e.g. Arable), or a specific crop.",
    )
    row = df[df["record_label"] == record_label].iloc[0]

    st.markdown(f"#### {record_label}")

    # ---------- CIRCULAR KPI GAUGES ----------
    st.markdown(
        "<div class='section-eyebrow'>Performance</div>"
        "<div class='section-title'>Key performance indicators</div>",
        unsafe_allow_html=True,
    )

    # First row: yield, emissions intensity, water intensity
    c1, c2, c3 = st.columns(3)
    with c1:
        pct = relative_position(df, "yield_per_ha", row["yield_per_ha"], higher_is_better=True)
        circular_kpi("Yield per ha", row["yield_per_ha"], " t/ha", 2, pct)
    with c2:
        pct = relative_position(
            df, "emissions_per_tonne", row["emissions_per_tonne"], higher_is_better=False
        )
        circular_kpi("Emissions per tonne", row["emissions_per_tonne"], " kg CO₂e/t", 1, pct)
    with c3:
        pct = relative_position(
            df, "water_per_tonne", row["water_per_tonne"], higher_is_better=False
        )
        circular_kpi("Water per tonne", row["water_per_tonne"], " m³/t", 1, pct)

    # Second row: female workforce, total emissions, accident rate
    c4, c5, c6 = st.columns(3)
    with c4:
        female_val = row["female_share"] * 100 if pd.notna(row["female_share"]) else np.nan
        pct = relative_position(df.assign(female_pct=df["female_share"] * 100),
                                "female_pct",
                                female_val,
                                higher_is_better=True)
        circular_kpi("Female workforce", female_val, " %", 0, pct)
    with c5:
        pct = relative_position(
            df, "total_emissions", row["total_emissions"], higher_is_better=False
        )
        circular_kpi("Total emissions", row["total_emissions"], " kg CO₂e", 0, pct)
    with c6:
        pct = relative_position(
            df, "accidents_per_100_workers", row["accidents_per_100_workers"],
            higher_is_better=False,
        )
        circular_kpi("Accident rate", row["accidents_per_100_workers"], " /100 workers", 1, pct)

    # ---------- ESG SCORES (bar chart) ----------
    st.markdown(
        "<div class='section-eyebrow'>Scores</div>"
        "<div class='section-title'>ESG scores — selected vs peer average</div>",
        unsafe_allow_html=True,
    )

    scores_df = pd.DataFrame(
        {
            "Dimension": ["Environment", "Social", "Governance", "Overall ESG"],
            "Selected record": [
                float(row["env_score"]),
                float(row["soc_score"]),
                float(row["gov_score"]),
                float(row["esg_score"]),
            ],
            "Peer average": [
                float(df["env_score"].mean()),
                float(df["soc_score"].mean()),
                float(df["gov_score"].mean()),
                float(df["esg_score"].mean()),
            ],
        }
    ).melt("Dimension", var_name="Type", value_name="Score")

    scores_chart = (
        alt.Chart(scores_df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X(
                "Dimension:N",
                title="",
                axis=alt.Axis(labelAngle=0, labelLine=False),
            ),
            xOffset="Type:N",
            y=alt.Y("Score:Q", title="Score (0–100)", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(
                "Type:N",
                title="",
                scale=alt.Scale(range=["#16a34a", "#9ca3af"]),
            ),
            tooltip=[
                "Type",
                "Dimension",
                alt.Tooltip("Score:Q", format=".0f"),
            ],
        )
        .properties(height=270)
    )

    st.altair_chart(scores_chart, use_container_width=True)

    # ---------- EMISSIONS BREAKDOWN ----------
    st.markdown(
        "<div class='section-eyebrow'>Emissions</div>"
        "<div class='section-title'>Emissions breakdown</div>",
        unsafe_allow_html=True,
    )

    emis_df = pd.DataFrame(
        {
            "Source": ["Fertiliser N", "Diesel", "Electricity"],
            "kg_co2e": [
                row["emissions_fertilizer"],
                row["emissions_diesel"],
                row["emissions_electric"],
            ],
        }
    )

    donut = (
        alt.Chart(emis_df)
        .mark_arc(innerRadius=60)
        .encode(
            theta="kg_co2e:Q",
            color=alt.Color(
                "Source:N",
                scale=alt.Scale(
                    range=["#16a34a", "#22c55e", "#4ade80"]
                ),
                title="Source",
            ),
            tooltip=[
                "Source",
                alt.Tooltip("kg_co2e:Q", title="Emissions (kg CO₂e)", format=".0f"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(donut, use_container_width=True)

    # ---------- PEER COMPARISON ----------
    st.markdown(
        "<div class='section-eyebrow'>Benchmark</div>"
        "<div class='section-title'>Peer comparison (anonymous)</div>",
        unsafe_allow_html=True,
    )

    if privacy_mode:
        st.warning(
            "Peer benchmarking is hidden because Privacy Mode is enabled."
        )
    else:
        comp_df = df[["farm_id", "yield_per_ha", "emissions_per_ha"]].copy()
        comp_df["Farm"] = comp_df["farm_id"].apply(
            lambda x: "Selected farm" if x == row["farm_id"] else "Peer farm"
        )

        scatter = (
            alt.Chart(comp_df)
            .mark_circle(size=90)
            .encode(
                x=alt.X("yield_per_ha:Q", title="Yield (t/ha)"),
                y=alt.Y("emissions_per_ha:Q", title="Emissions (kg CO₂e/ha)"),
                color=alt.Color(
                    "Farm:N",
                    title="",
                    scale=alt.Scale(range=["#16a34a", "#9ca3af"]),
                ),
                tooltip=[
                    alt.Tooltip("Farm:N", title="Farm"),
                    alt.Tooltip(
                        "yield_per_ha:Q", title="Yield (t/ha)", format=".2f"
                    ),
                    alt.Tooltip(
                        "emissions_per_ha:Q",
                        title="Emissions (kg CO₂e/ha)",
                        format=".1f",
                    ),
                ],
            )
            .properties(height=330)
        )

        st.altair_chart(scatter, use_container_width=True)

    # ---------- ESG NARRATIVE ----------
    st.markdown(
        "<div class='section-eyebrow'>Narrative</div>"
        "<div class='section-title'>ESG narrative report</div>",
        unsafe_allow_html=True,
    )

    peer_avg = {
        "emissions": df["emissions_per_tonne"].mean(),
        "water": df["water_per_tonne"].mean(),
        "female": df["female_share"].mean(),
        "acc": df["accidents_per_100_workers"].mean(),
    }

    narrative = generate_esg_narrative(row, peer_avg)

    with st.expander("Open ESG narrative"):
        st.markdown(narrative)

    pdf_bytes = narrative_to_pdf_bytes(
        title=f"ESG report — {row['organisation_name']} ({row['enterprise_type'] or row['crop']} {int(row['year'])})",
        narrative_md=narrative,
    )
    st.download_button(
        label="📄 Download ESG report as PDF",
        data=pdf_bytes,
        file_name=f"ESG_report_{row['farm_id']}_{row['enterprise_type'] or row['crop']}_{int(row['year'])}.pdf",
        mime="application/pdf",
    )
