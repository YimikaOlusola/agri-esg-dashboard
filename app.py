import streamlit as st
import pandas as pd
import time
from dotenv import load_dotenv

from utils.logging_interface import render_logging_interface

from utils.calculations import (
    compute_kpis, 
    aggregate_to_farm_level,
    compute_esg_scores
)
from utils.ai_insights import generate_ai_insights
from utils.visualisations import (
    create_gauge_chart, 
    create_progress_line_chart,
    create_score_breakdown_pie,
    create_emissions_donut,
    create_comparison_bar
)

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="AgriESG Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS - INLINE VERSION
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    :root {
        --color-green-dark: #2d5016;
        --color-green-medium: #4a7c29;
        --color-green-light: #6b9e47;
        --color-green-bg: #e8f5e9;
        --color-brown-dark: #5d4037;
        --color-brown-medium: #8d6e63;
        --color-beige: #f5f1ed;
        --color-yellow: #f9a825;
        --color-amber: #fbc02d;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: var(--color-beige) !important;
    }
    
    .main-title {
        font-size: 42px;
        font-weight: 700;
        color: var(--color-green-dark);
        text-align: center;
        margin-bottom: 5px;
    }
    
    .subtitle {
        font-size: 18px;
        color: var(--color-brown-medium);
        text-align: center;
        margin-bottom: 30px;
    }
    
    .hero-section {
        background: linear-gradient(135deg, var(--color-green-bg) 0%, #c8e6c9 100%);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 4px 15px rgba(45, 80, 22, 0.15);
        text-align: center;
        margin-bottom: 20px;
        width: 100%;
    }
    
    .hero-section > div {
        width: 100%;
    }
                
    .hero-top-cap {
        max-width: 650px; 
        margin: 0 auto;   
        border-top-left-radius: 20px;
        border-top-right-radius: 20px;
        height: 120px; 
        margin-bottom: -90px; 
        position: relative;
        z-index: 0;
        padding-top: 20px;
        text-align: center;
    }

    .hero-bottom-cap {
        max-width: 650px; /* MATCHES CHART WIDTH */
        margin: -30px auto 0 auto; /* CENTERS IT */
        border-bottom-left-radius: 20px;
        border-bottom-right-radius: 20px;
        padding: 0px 30px 30px 30px;
        text-align: center;
        position: relative;
        z-index: 2;
    }
    
   div[data-testid="stPlotlyChart"] {
        width: 100%;
        display: flex;            /* Use flexbox layout */
        justify-content: center;  /* Horizontally center the chart */
        align-items: center;      /* Vertically center */
    }         
    
    .score-message {
        font-size: 22px;
        font-weight: 600;
        margin-top: 15px;
        color: var(--color-brown-dark);
    }
    
    .esg-component-card {
        background: white;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin: 10px 5px;
    }
    
    .esg-component-icon {
        font-size: 28px;
        margin-bottom: 5px;
    }
    
    .esg-component-label {
        font-size: 12px;
        color: #757575;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
        font-weight: 600;
    }
    
    .esg-component-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--color-brown-dark);
        margin-bottom: 8px;
    }
    
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 25px 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        text-align: center;
        transition: transform 0.2s;
        height: 240px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin: 10px 0;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }
    
    .metric-icon {
        font-size: 56px;
        margin-bottom: 12px;
    }
    
    .metric-title {
        font-size: 13px;
        color: #757575;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: var(--color-brown-dark);
        margin-bottom: 8px;
        line-height: 1;
    }
    
    .metric-status {
        font-size: 15px;
        font-weight: 600;
        padding: 5px 15px;
        border-radius: 20px;
        margin-bottom: 10px;
    }
    
    .status-excellent {
        color: var(--color-green-dark);
        background: var(--color-green-bg);
    }
    
    .status-good {
        color: var(--color-yellow);
        background: #fff9e6;
    }
    
    .status-needs-work {
        color: #c62828;
        background: #ffebee;
    }
    
    .status-neutral {
        color: var(--color-brown-medium);
        background: #f5f5f5;
    }
    
    .progress-bar-container {
        width: 100%;
        height: 8px;
        background: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        margin-top: 10px;
    }
    
    .progress-bar-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease-in-out;
    }
    
    .progress-bar-green {
        background: linear-gradient(90deg, var(--color-green-medium), var(--color-green-light));
    }
    
    .progress-bar-yellow {
        background: linear-gradient(90deg, var(--color-yellow), var(--color-amber));
    }
    
    .progress-bar-red {
        background: linear-gradient(90deg, #c62828, #d84315);
    }
    
    .progress-bar-neutral {
        background: linear-gradient(90deg, var(--color-brown-medium), #a1887f);
    }
    
    .insights-container {
        background: white !important;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border-left: 5px solid #4a7c29;
        margin-bottom: 20px;
    }
    
    .insight-item {
        padding: 12px 0;
        margin-bottom: 12px;
        border-bottom: 1px solid #f0f0f0;
        font-size: 16px;
        line-height: 1.6;
        color: #5d4037 !important;
    }
    
    .insight-item:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }
    
    .insight-item p {
        color: #5d4037 !important;
        margin: 0 !important;
    }
    
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, var(--color-green-medium), var(--color-green-light)) !important;
        color: white !important;
        border: none !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* === MOBILE OPTIMIZATIONS === */
    @media (max-width: 768px) {
        /* Shrink the big title */
        .main-title {
            font-size: 32px !important;
        }
        
        .subtitle {
            font-size: 16px !important;
        }

        /* Adjust Hero Section */
        .hero-section {
            padding: 20px !important;
        }
        
        .score-message {
            font-size: 18px !important;
        }

        /* METRIC CARDS: Allow them to be shorter on mobile to save scroll space */
        .metric-card {
            height: auto !important;
            min-height: 160px !important;
            padding: 15px !important;
            margin: 5px 0 !important;
        }
        
        .metric-icon {
            font-size: 40px !important;
        }
        
        .metric-value {
            font-size: 28px !important;
        }
        
        /* Reduce padding on the detailed cards */
        .esg-component-card {
            padding: 10px !important;
        }
        
        /* Fix Chart Margins */
        div[data-testid="stPlotlyChart"] {
            width: 100% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True) 

load_css()

# REQUIRED AND OPTIONAL COLUMNS
REQUIRED_COLUMNS = {
    'farmer_name': 'Farmer Name',
    'farm_id': 'Farm ID',
    'farm_name': 'Farm Name',
    'year': 'Year',
    'month': 'Month',
    'field_id': 'Field ID',
    'field_name': 'Field Name',
    'field_area_ha': 'Field Area (hectares)',
    'crop_type': 'Crop Type',
    'soil_type': 'Soil Type',
    'fertiliser_kgN': 'Nitrogen Fertilizer (kg N)',
    'fertiliser_kgP2O5': 'Phosphate Fertilizer (kg P2O5)',
    'fertiliser_kgK2O': 'Potash Fertilizer (kg K2O)',
    'pesticide_applied_yes_no': 'Pesticide Applied (yes/no)',
    'diesel_litres': 'Diesel Used (litres)',
    'irrigation_applied_yes_no': 'Irrigation Applied (yes/no)',
    'labour_hours': 'Labour Hours',
    'livestock_present_yes_no': 'Livestock Present (yes/no)',
    'sfi_soil_standard_yes_no': 'SFI Soil Standard (yes/no)',
    'sfi_nutrient_management_yes_no': 'SFI Nutrient Management (yes/no)',
    'sfi_hedgerows_yes_no': 'SFI Hedgerows (yes/no)'
}

OPTIONAL_COLUMNS = {
    'soil_organic_matter_pct': 'Soil Organic Matter (%)',
    'soil_ph': 'Soil pH',
    'cover_crop_planted_yes_no': 'Cover Crop Planted (yes/no)',
    'hedgerow_length_m': 'Hedgerow Length (meters)',
    'wildflower_area_ha': 'Wildflower Area (hectares)',
    'buffer_strip_area_ha': 'Buffer Strip Area (hectares)',
    'trees_planted_count': 'Trees Planted Count',
    'reduced_tillage_yes_no': 'Reduced Tillage (yes/no)',
    'integrated_pest_management_yes_no': 'Integrated Pest Management (yes/no)',
    'water_volume_m3': 'Water Volume (m³)',
    'labour_hs_training_done_yes_no': 'Health & Safety Training (yes/no)',
    'worker_contracts_formalised_yes_no': 'Worker Contracts Formalized (yes/no)'
}

# Helper function for progress bars
def create_progress_bar(value, max_value=100, status="neutral"):
    """Create HTML progress bar"""
    percentage = min((value / max_value) * 100, 100) if max_value > 0 else 0
    
    if status == "excellent":
        color_class = "progress-bar-green"
    elif status == "good":
        color_class = "progress-bar-yellow"
    elif status == "needs-work":
        color_class = "progress-bar-red"
    else:
        color_class = "progress-bar-neutral"
    
    return f"""
    <div class="progress-bar-container">
        <div class="progress-bar-fill {color_class}" style="width: {percentage}%"></div>
    </div>
    """

# Helper function to get status info
def get_status_info(value, thresholds, lower_is_better=False):
    """Return status text, CSS class, emoji, and normalized score"""
    if lower_is_better:
        if value <= thresholds['excellent']:
            return "Excellent", "status-excellent", "✅", 90
        elif value <= thresholds['good']:
            return "Good", "status-good", "⚠️", 65
        else:
            return "Needs Work", "status-needs-work", "❌", 35
    else:
        if value >= thresholds['excellent']:
            return "Excellent", "status-excellent", "✅", 90
        elif value >= thresholds['good']:
            return "Good", "status-good", "⚠️", 65
        else:
            return "Needs Work", "status-needs-work", "❌", 35

@st.cache_data(ttl=1800)
def load_and_process_data(file_bytes):
    """Load CSV and compute all metrics - CACHED FOR SPEED"""
    start_time = time.time()
    
    df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
    df = compute_kpis(df)
    farm_df = aggregate_to_farm_level(df)
    
    load_time = time.time() - start_time
    return df, farm_df, load_time

# Header
st.markdown('<h1 class="main-title">🌾 AgriESG Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Simple insights for better farming</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📁 Upload Data")
    uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
    
    if uploaded_file is not None:
        st.success("✅ File uploaded!")
    
    st.markdown("---")

# Welcome screen
if uploaded_file is None:
    st.info("👋 **Welcome!** Upload your farm data CSV to get started.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 What You Need")
        st.markdown("""
        Your CSV file should contain **field-level data** with:
        - Farm and field details
        - Monthly records for each field
        - Fertilizer and fuel usage
        - SFI compliance information
        
        **Optional:** Add soil health, biodiversity, and worker data for better scores!
        """)
    
    with col2:
        st.markdown("### 🎯 Get Started")
        st.markdown("""
        1. **Download** the CSV template below
        2. **Fill in** your farm's monthly field data
        3. **Upload** the file using the button on the left
        
        The template includes **only required fields**. Add optional fields for richer insights!
        """)
    
    st.markdown("---")
    st.markdown("### 📥 Download CSV Template")
    
    template_data = {
        'farm_id': ['FARM-001', 'FARM-001'],
        'farm_name': ['Green Valley Farm', 'Green Valley Farm'],
        'year': [2025, 2025],
        'month': ['2025-03', '2025-04'],
        'field_id': ['FIELD-001', 'FIELD-001'],
        'field_name': ['North Field', 'North Field'],
        'field_area_ha': [15.0, 15.0],
        'crop_type': ['Spring Barley', 'Spring Barley'],
        'soil_type': ['Sandy loam', 'Sandy loam'],
        'fertiliser_kgN': [25, 20],
        'fertiliser_kgP2O5': [5, 4],
        'fertiliser_kgK2O': [8, 6],
        'pesticide_applied_yes_no': ['yes', 'no'],
        'diesel_litres': [120, 110],
        'irrigation_applied_yes_no': ['no', 'yes'],
        'labour_hours': [18, 20],
        'livestock_present_yes_no': ['no', 'no'],
        'sfi_soil_standard_yes_no': ['yes', 'yes'],
        'sfi_nutrient_management_yes_no': ['yes', 'yes'],
        'sfi_hedgerows_yes_no': ['no', 'no']
    }
    
    template_df = pd.DataFrame(template_data)
    csv_template = template_df.to_csv(index=False)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📥 Download Basic Template (Required Fields Only)",
            data=csv_template,
            file_name="farm_basic_inputs_template.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
    
    st.markdown("---")
    
    with st.expander("📚 See All Column Details (Required + Optional)"):
        st.markdown("### ✅ Required Columns")
        for col, desc in REQUIRED_COLUMNS.items():
            st.markdown(f"- **`{col}`**: {desc}")
        
        st.markdown("---")
        st.markdown("### 🌟 Optional Columns (for Better Scoring)")
        for col, desc in OPTIONAL_COLUMNS.items():
            st.markdown(f"- **`{col}`**: {desc}")
    
    st.stop()

# Load and validate data
file_bytes = uploaded_file.getvalue()

try:
    raw_df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
    
    # Check required columns
    missing_required = [
        REQUIRED_COLUMNS[col] for col in REQUIRED_COLUMNS.keys() 
        if col not in raw_df.columns
    ]
    
    if missing_required:
        st.error("### ⚠️ Missing Required Columns")
        st.markdown("Your CSV file is missing some **required** columns:")
        
        for col in missing_required:
            st.markdown(f"- ❌ **{col}**")
        
        with st.expander("📋 See the complete list of required columns"):
            st.markdown("### Required Columns (Must Have)")
            for col, desc in REQUIRED_COLUMNS.items():
                status = "✅" if col in raw_df.columns else "❌"
                st.markdown(f"{status} **`{col}`**: {desc}")
        
        st.stop()
    
    # Check optional columns
    present_optional = [
        OPTIONAL_COLUMNS[col] for col in OPTIONAL_COLUMNS.keys() 
        if col in raw_df.columns
    ]
    
    if present_optional:
        st.success(f"✅ Found {len(present_optional)} optional fields - your ESG score will be more accurate!")
    else:
        st.info("💡 **Tip:** Add optional fields like soil health and biodiversity data to improve your ESG score!")
    
    # Process data
    df, farm_df, load_time = load_and_process_data(file_bytes)
    
    if load_time > 3:
        st.warning(f"⚠️ Data loaded in {load_time:.1f}s (target: <3s)")
    else:
        st.success(f"✅ Data loaded in {load_time:.2f}s")

except pd.errors.EmptyDataError:
    st.error("### ⚠️ Empty File")
    st.markdown("The CSV file you uploaded is empty. Please upload a file with data.")
    st.stop()

except pd.errors.ParserError:
    st.error("### ⚠️ File Format Problem")
    st.markdown("""
    We couldn't read your file. Please make sure:
    - Your file is saved as **CSV format** (not Excel .xlsx)
    - Your data is separated by commas
    """)
    st.stop()

except Exception as e:
    st.error("### ⚠️ Something Went Wrong")
    st.markdown("""
    We encountered an unexpected problem loading your file.
    
    Please check:
    - Your CSV file is properly formatted
    - All numbers are valid (no text in number columns)
    - Column names match exactly (lowercase with underscores)
    """)
    
    with st.expander("🔧 Technical Details"):
        st.code(f"Error: {type(e).__name__}\n{str(e)}")
    
    st.stop()

# Compute ESG scores
with st.spinner("📊 Calculating ESG scores..."):
    esg_df = compute_esg_scores(farm_df)

# Sidebar filters
with st.sidebar:
    st.markdown("### 🔍 Filters")
    
    years = sorted(esg_df['year'].dropna().unique().tolist())
    farms = sorted(esg_df['farm_id'].dropna().unique().tolist())
    
    if len(farms) > 1:
        selected_farm = st.selectbox("🏡 Your Farm", farms)
    else:
        selected_farm = farms[0]
    
    view_mode = st.radio(
        "📅 View Mode",
        ["Current Year Snapshot", "Multi-Year Progress"],
        help="Single year for detailed view or multiple years for trends"
    )
    
    if view_mode == "Current Year Snapshot":
        selected_year = st.selectbox("Select Year", years, index=len(years)-1)
        selected_years = [selected_year]
    else:
        selected_years = st.multiselect(
            "Select Years for Comparison",
            years,
            default=years[-min(3, len(years)):] if len(years) >= 3 else years
        )
        if not selected_years:
            st.warning("Please select at least one year")
            st.stop()

# Filter data
filtered_esg = esg_df[
    (esg_df['farm_id'] == selected_farm) & 
    (esg_df['year'].isin(selected_years))
]

if filtered_esg.empty:
    st.warning("No data for selected filters")
    st.stop()

# Get current year data
if view_mode == "Current Year Snapshot":
    my_farm = filtered_esg.iloc[0]
    current_year = selected_year
else:
    latest = filtered_esg[filtered_esg['year'] == max(selected_years)].iloc[0]
    my_farm = latest
    current_year = max(selected_years)

# === HERO SECTION ===
st.markdown("---")

gauge_fig = create_gauge_chart(
    value=my_farm['esg_score'],
    title=f"Your Farm ESG Score ({current_year})"
)

gauge_fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=40, r=40, t=40, b=40), 
    height=300
)

col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    st.plotly_chart(
        gauge_fig, 
        use_container_width=True, 
        config={'displayModeBar': False}
    )

score = my_farm['esg_score']

score = my_farm['esg_score']
if score >= 70:
    message = "🎉 Excellent! You're a leader in sustainable farming."
    color = "#2d5016"
elif score >= 50:
    message = "👍 Good work! A few improvements will boost your score."
    color = "#c9800b"
else:
    message = "💪 Let's improve your farming practices together."
    color = "#c62828"

# Apply the hero-section style just to the text message now
st.markdown(f'''
<div class="hero-section">
    <p class="score-message" style="color: {color}; margin: 0;">{message}</p>
</div>
''', unsafe_allow_html=True)

# ESG COMPONENT BREAKDOWN
st.markdown("---")
comp_col1, comp_col2, comp_col3 = st.columns(3)

with comp_col1:
    e_score = my_farm['e_score']
    e_status = "excellent" if e_score >= 70 else "good" if e_score >= 50 else "needs-work"
    progress_html = create_progress_bar(e_score, 100, e_status)
    st.markdown(f'''
    <div class="esg-component-card">
        <div class="esg-component-icon">🌍</div>
        <div class="esg-component-label">Environment</div>
        <div class="esg-component-value">{e_score:.0f}%</div>
        {progress_html}
    </div>
    ''', unsafe_allow_html=True)

with comp_col2:
    s_score = my_farm['s_score']
    s_status = "excellent" if s_score >= 70 else "good" if s_score >= 50 else "needs-work"
    progress_html = create_progress_bar(s_score, 100, s_status)
    st.markdown(f'''
    <div class="esg-component-card">
        <div class="esg-component-icon">👥</div>
        <div class="esg-component-label">Social</div>
        <div class="esg-component-value">{s_score:.0f}%</div>
        {progress_html}
    </div>
    ''', unsafe_allow_html=True)

with comp_col3:
    g_score = my_farm['g_score']
    g_status = "excellent" if g_score >= 70 else "good" if g_score >= 50 else "needs-work"
    progress_html = create_progress_bar(g_score, 100, g_status)
    st.markdown(f'''
    <div class="esg-component-card">
        <div class="esg-component-icon">📋</div>
        <div class="esg-component-label">Governance</div>
        <div class="esg-component-value">{g_score:.0f}%</div>
        {progress_html}
    </div>
    ''', unsafe_allow_html=True)

st.markdown("---")

# === QUICK STATS ===
st.markdown('<h2 class="section-title">📊 Quick Stats</h2>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

# Metrics
total_area = my_farm['total_farm_area_ha']
emissions_per_ha = my_farm['emissions_per_ha']
n_per_ha = my_farm['n_per_ha']
sfi_compliance = (
    my_farm['sfi_soil_compliance_rate'] + 
    my_farm['sfi_nutrient_compliance_rate'] + 
    my_farm['sfi_hedgerow_compliance_rate']
) / 3 * 100

with col1:
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid #4a7c29;">
        <div class="metric-icon">🌾</div>
        <div class="metric-title">Total Farm Area</div>
        <div class="metric-value">{total_area:.1f} ha</div>
        <div class="metric-status status-neutral">✅ Tracked</div>
        {create_progress_bar(100, 100, "neutral")}
    </div>
    ''', unsafe_allow_html=True)

with col2:
    status_text, status_class, emoji, norm_score = get_status_info(
        emissions_per_ha, {'excellent': 30, 'good': 50}, lower_is_better=True
    )
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid {'#4a7c29' if status_class == 'status-excellent' else '#f9a825' if status_class == 'status-good' else '#c62828'};">
        <div class="metric-icon">🌫️</div>
        <div class="metric-title">Emissions</div>
        <div class="metric-value">{emissions_per_ha:.0f} kg/ha</div>
        <div class="metric-status {status_class}">{emoji} {status_text}</div>
        {create_progress_bar(norm_score, 100, status_text.lower().replace(' ', '-'))}
    </div>
    ''', unsafe_allow_html=True)

with col3:
    status_text, status_class, emoji, norm_score = get_status_info(
        n_per_ha, {'excellent': 50, 'good': 100}, lower_is_better=True
    )
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid {'#4a7c29' if status_class == 'status-excellent' else '#f9a825' if status_class == 'status-good' else '#c62828'};">
        <div class="metric-icon">🧪</div>
        <div class="metric-title">Nitrogen Use</div>
        <div class="metric-value">{n_per_ha:.0f} kg/ha</div>
        <div class="metric-status {status_class}">{emoji} {status_text}</div>
        {create_progress_bar(norm_score, 100, status_text.lower().replace(' ', '-'))}
    </div>
    ''', unsafe_allow_html=True)

with col4:
    status_text, status_class, emoji, norm_score = get_status_info(
        sfi_compliance, {'excellent': 80, 'good': 50}
    )
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid {'#4a7c29' if status_class == 'status-excellent' else '#f9a825' if status_class == 'status-good' else '#c62828'};">
        <div class="metric-icon">📋</div>
        <div class="metric-title">SFI Compliance</div>
        <div class="metric-value">{sfi_compliance:.0f}%</div>
        <div class="metric-status {status_class}">{emoji} {status_text}</div>
        {create_progress_bar(sfi_compliance, 100, status_text.lower().replace(' ', '-'))}
    </div>
    ''', unsafe_allow_html=True)

st.markdown("---")

# === AI INSIGHTS ===
st.markdown('<h2 class="section-title">💡 What You Can Do This Season</h2>', unsafe_allow_html=True)

farmer_name = my_farm.get('farmer_name', None)

if not farmer_name or pd.isna(farmer_name):
    name_lookup = df[df['farm_id'] == selected_farm]['farmer_name'].dropna().unique()
    
    if len(name_lookup) > 0:
        farmer_name = str(name_lookup[0])
    else:
        farmer_name = "Farmer" 

with st.spinner(f"🤖 Generating advice for {farmer_name}..."):
    insights = generate_ai_insights(
        esg_score=my_farm['esg_score'],
        e_score=my_farm['e_score'],
        s_score=my_farm['s_score'],
        emissions_per_ha=emissions_per_ha,
        emissions_per_tonne=0,
        yield_per_ha=0,
        female_share=0,
        accidents=0,
        farm_id=selected_farm,
        farmer_name=farmer_name 
    )

insights_html = '<div class="insights-container">'
for insight in insights:
    insights_html += f'<div class="insight-item"><p>{insight}</p></div>'
insights_html += '</div>'

st.markdown(insights_html, unsafe_allow_html=True)

st.markdown("---")

# === CHARTS ===
st.markdown('<h2 class="section-title">📈 Visual Breakdown</h2>', unsafe_allow_html=True)

# UPDATE THIS LINE
tab1, tab2, tab3, tab4 = st.tabs(["📊 Score Breakdown", "🌍 Emissions Sources", "📅 Progress Over Time", "📝 Activity Log"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Your ESG Score Components")
        pie_fig = create_score_breakdown_pie(
            e_score=my_farm['e_score'],
            s_score=my_farm['s_score'],
            g_score=my_farm['g_score']
        )
        st.plotly_chart(pie_fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        st.markdown("### Farm Performance Comparison")
        all_farms = esg_df[esg_df['year'] == current_year]
        comparison_fig = create_comparison_bar(my_farm, all_farms)
        st.plotly_chart(comparison_fig, use_container_width=True, config={'displayModeBar': False})

with tab2:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Emissions by Source")
        donut_fig = create_emissions_donut(
            fertilizer=my_farm['emissions_fertilizer'],
            diesel=my_farm['emissions_diesel'],
            electricity=0
        )
        st.plotly_chart(donut_fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        st.markdown("### Key Numbers")
        st.metric("Total Emissions", f"{my_farm['total_emissions']:.0f} kg CO₂e")
        st.metric("Per Hectare", f"{emissions_per_ha:.1f} kg/ha")

with tab3:
    if view_mode == "Multi-Year Progress" and len(selected_years) > 1:
        st.markdown("### Your ESG Score Over Time")
        
        historical_data = []
        for year in sorted(selected_years):
            year_data = filtered_esg[filtered_esg['year'] == year]
            if not year_data.empty:
                historical_data.append({
                    'year': year,
                    'esg_score': year_data.iloc[0]['esg_score']
                })
        
        if len(historical_data) > 1:
            progress_fig = create_progress_line_chart(historical_data)
            st.plotly_chart(progress_fig, width='stretch', config={'displayModeBar': False})
        else:
            st.info("Need at least 2 years of data to show progress.")
    else:
        st.info("📊 Switch to 'Multi-Year Progress' mode to see trends!")

with tab4:
    render_logging_interface()

st.markdown("---")

# === EXPORT ===
st.markdown('<h2 class="section-title">📥 Download Your Report</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if st.button("📄 Download PDF Report", type="primary", use_container_width=True):
        with st.spinner("🔄 Generating PDF..."):
            from utils.pdf_report import generate_pdf_report
            
            # Get current line chart if multi-year
            line_fig_for_pdf = None
            if view_mode == "Multi-Year Progress" and len(selected_years) > 1:
                historical_data = []
                for year in sorted(selected_years):
                    year_data = filtered_esg[filtered_esg['year'] == year]
                    if not year_data.empty:
                        historical_data.append({
                            'year': year,
                            'esg_score': year_data.iloc[0]['esg_score']
                        })
                
                if len(historical_data) > 1:
                    line_fig_for_pdf = create_progress_line_chart(historical_data)
            
            # Generate PDF
            pdf_buffer = generate_pdf_report(
                farm_data=my_farm,
                farmer_name=farmer_name,
                year=current_year,
                insights_list=insights,
                gauge_fig=gauge_fig,
                pie_fig=pie_fig,
                donut_fig=donut_fig,
                bar_fig=comparison_fig,
                line_fig=line_fig_for_pdf
            )
            
            st.download_button(
                label="💾 Download PDF",
                data=pdf_buffer,
                file_name=f"farm_{selected_farm}_esg_report_{current_year}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

with col2:
    if st.button("📊 Download CSV Report", type="primary", use_container_width=True):
        report_data = {
            'Farm ID': [selected_farm],
            'Farm Name': [my_farm['farm_name']],
            'Farmer Name': [my_farm.get('farmer_name', 'N/A')],
            'Year': [current_year],
            'ESG Score': [my_farm['esg_score']],
            'Environment Score': [my_farm['e_score']],
            'Social Score': [my_farm['s_score']],
            'Governance Score': [my_farm['g_score']],
            'Total Area (ha)': [total_area],
            'Emissions (kg/ha)': [emissions_per_ha],
            'Nitrogen Use (kg/ha)': [n_per_ha],
            'SFI Compliance (%)': [sfi_compliance]
        }
        
        report_df = pd.DataFrame(report_data)
        csv = report_df.to_csv(index=False)
        
        st.download_button(
            label="💾 Download CSV",
            data=csv,
            file_name=f"farm_{selected_farm}_report_{current_year}.csv",
            mime="text/csv",
            use_container_width=True
        )
