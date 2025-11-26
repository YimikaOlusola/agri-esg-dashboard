import streamlit as st
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import time

from utils.calculations import (
    compute_kpis, 
    aggregate_to_farm_level,
    merge_optional_data,
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

# Load CSS (same as before)
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8f9fa;
    }
    
    .main-title {
        font-size: 42px;
        font-weight: 700;
        color: #2c5f2d;
        text-align: center;
        margin-bottom: 5px;
    }
    
    .subtitle {
        font-size: 18px;
        color: #666;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .section-title {
        font-size: 26px;
        font-weight: 600;
        color: #2c5f2d;
        margin: 25px 0 15px 0;
        padding-left: 10px;
        border-left: 5px solid #28a745;
    }
    
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        text-align: center;
        transition: transform 0.2s;
        height: 200px;
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
        font-size: 15px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #333;
        margin-bottom: 8px;
        line-height: 1;
    }
    
    .metric-status {
        font-size: 15px;
        font-weight: 600;
        padding: 5px 15px;
        border-radius: 20px;
    }
    
    .insight-card {
        background: white;
        border-left: 5px solid #ffc107;
        border-radius: 10px;
        padding: 20px 25px;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        display: flex;
        align-items: flex-start;
        transition: transform 0.2s;
    }
    
    .insight-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .insight-number {
        background: #ffc107;
        color: white;
        font-size: 20px;
        font-weight: 700;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-right: 20px;
        flex-shrink: 0;
    }
    
    .insight-text {
        font-size: 17px;
        line-height: 1.6;
        color: #333;
        flex-grow: 1;
    }
    
    .hero-section {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    
    .score-message {
        font-size: 22px;
        font-weight: 600;
        margin-top: 15px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

load_css()

# DEFINE REQUIRED AND OPTIONAL COLUMNS
REQUIRED_COLUMNS = {
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
    'bulk_density_g_cm3': 'Bulk Density (g/cm³)',
    'soil_test_date': 'Soil Test Date',
    'cover_crop_planted_yes_no': 'Cover Crop Planted (yes/no)',
    'cover_crop_species': 'Cover Crop Species',
    'cover_crop_coverage_pct': 'Cover Crop Coverage (%)',
    'hedgerow_length_m': 'Hedgerow Length (meters)',
    'wildflower_area_ha': 'Wildflower Area (hectares)',
    'buffer_strip_area_ha': 'Buffer Strip Area (hectares)',
    'trees_planted_count': 'Trees Planted Count',
    'bare_soil_days_estimate': 'Bare Soil Days Estimate',
    'manure_or_compost_kg_per_ha': 'Manure/Compost (kg/ha)',
    'reduced_tillage_yes_no': 'Reduced Tillage (yes/no)',
    'integrated_pest_management_yes_no': 'Integrated Pest Management (yes/no)',
    'water_volume_m3': 'Water Volume (m³)',
    'biodiversity_notes': 'Biodiversity Notes',
    'labour_hs_training_done_yes_no': 'Health & Safety Training (yes/no)',
    'worker_contracts_formalised_yes_no': 'Worker Contracts Formalized (yes/no)'
}

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

# Welcome screen if no file
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
    
    # Template with REQUIRED columns only
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
        st.markdown("These columns **must** be in your CSV file:")
        
        for col, desc in REQUIRED_COLUMNS.items():
            st.markdown(f"- **`{col}`**: {desc}")
        
        st.markdown("---")
        st.markdown("### 🌟 Optional Columns (for Better Scoring)")
        st.markdown("Add these to get higher ESG scores and richer insights:")
        
        for col, desc in OPTIONAL_COLUMNS.items():
            st.markdown(f"- **`{col}`**: {desc}")
        
        st.markdown("---")
        st.markdown("""
        #### 💡 Tips
        - All column names must be **lowercase with underscores**
        - Use `yes` or `no` for yes/no fields (not 1/0 or True/False)
        - Leave cells empty if you don't have data (don't use 0)
        - Each row = one field for one month
        - Save as **CSV format** (not Excel .xlsx)
        """)
    
    st.stop()

# Load and validate data
file_bytes = uploaded_file.getvalue()

try:
    raw_df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
    
    # CHECK REQUIRED COLUMNS ONLY
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
        
        with st.expander("📥 Download template with correct structure"):
            template_data = {
                'farm_id': ['FARM-001'],
                'farm_name': ['Example Farm'],
                'year': [2025],
                'month': ['2025-03'],
                'field_id': ['FIELD-001'],
                'field_name': ['North Field'],
                'field_area_ha': [15.0],
                'crop_type': ['Spring Barley'],
                'soil_type': ['Sandy loam'],
                'fertiliser_kgN': [25],
                'fertiliser_kgP2O5': [5],
                'fertiliser_kgK2O': [8],
                'pesticide_applied_yes_no': ['yes'],
                'diesel_litres': [120],
                'irrigation_applied_yes_no': ['no'],
                'labour_hours': [18],
                'livestock_present_yes_no': ['no'],
                'sfi_soil_standard_yes_no': ['yes'],
                'sfi_nutrient_management_yes_no': ['yes'],
                'sfi_hedgerows_yes_no': ['no']
            }
            
            template_df = pd.DataFrame(template_data)
            csv_template = template_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Correct Template",
                data=csv_template,
                file_name="farm_basic_inputs_template.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.stop()
    
    # CHECK OPTIONAL COLUMNS (just inform, don't block)
    present_optional = [
        OPTIONAL_COLUMNS[col] for col in OPTIONAL_COLUMNS.keys() 
        if col in raw_df.columns
    ]
    
    if present_optional:
        st.success(f"✅ Found {len(present_optional)} optional fields - your ESG score will be more accurate!")
        with st.expander(f"🌟 Optional fields detected ({len(present_optional)})"):
            for col in present_optional:
                st.markdown(f"- ✅ {col}")
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
    - There are no special characters in column names
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
    
    # Farm selection
    farms = sorted(esg_df['farm_id'].dropna().unique().tolist())
    if len(farms) > 1:
        selected_farm = st.selectbox("🏡 Your Farm", farms)
    else:
        selected_farm = farms[0]
    
    # Year selection
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
col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    st.markdown('<div class="hero-section">', unsafe_allow_html=True)
    
    gauge_fig = create_gauge_chart(
        value=my_farm['esg_score'],
        title=f"Your Farm ESG Score ({current_year})"
    )
    st.plotly_chart(gauge_fig, use_container_width=True, config={'displayModeBar': False})
    
    score = my_farm['esg_score']
    if score >= 70:
        message = "🎉 Excellent! You're a leader in sustainable farming."
        color = "#28a745"
    elif score >= 50:
        message = "👍 Good work! A few improvements will boost your score."
        color = "#ffc107"
    else:
        message = "💪 Let's improve your farming practices together."
        color = "#dc3545"
    
    st.markdown(f'<p class="score-message" style="color: {color}">{message}</p>', 
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

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

def get_status(value, thresholds, lower_is_better=False):
    if lower_is_better:
        if value <= thresholds['good']:
            return ("Excellent", "#28a745", "✅")
        elif value <= thresholds['ok']:
            return ("Good", "#ffc107", "⚠️")
        else:
            return ("Needs Work", "#dc3545", "❌")
    else:
        if value >= thresholds['good']:
            return ("Excellent", "#28a745", "✅")
        elif value >= thresholds['ok']:
            return ("Good", "#ffc107", "⚠️")
        else:
            return ("Needs Work", "#dc3545", "❌")

with col1:
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid #28a745;">
        <div class="metric-icon">🌾</div>
        <div class="metric-title">Total Farm Area</div>
        <div class="metric-value">{total_area:.1f} ha</div>
        <div class="metric-status" style="color: #28a745;">✅ Tracked</div>
    </div>
    ''', unsafe_allow_html=True)

with col2:
    emission_status, emission_color, emission_emoji = get_status(
        emissions_per_ha, {'good': 30, 'ok': 50}, lower_is_better=True
    )
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid {emission_color};">
        <div class="metric-icon">🌫️</div>
        <div class="metric-title">Emissions</div>
        <div class="metric-value">{emissions_per_ha:.0f} kg/ha</div>
        <div class="metric-status" style="color: {emission_color};">{emission_emoji} {emission_status}</div>
    </div>
    ''', unsafe_allow_html=True)

with col3:
    nitrogen_status, nitrogen_color, nitrogen_emoji = get_status(
        n_per_ha, {'good': 50, 'ok': 100}, lower_is_better=True
    )
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid {nitrogen_color};">
        <div class="metric-icon">🧪</div>
        <div class="metric-title">Nitrogen Use</div>
        <div class="metric-value">{n_per_ha:.0f} kg/ha</div>
        <div class="metric-status" style="color: {nitrogen_color};">{nitrogen_emoji} {nitrogen_status}</div>
    </div>
    ''', unsafe_allow_html=True)

with col4:
    sfi_status, sfi_color, sfi_emoji = get_status(
        sfi_compliance, {'good': 80, 'ok': 50}
    )
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid {sfi_color};">
        <div class="metric-icon">📋</div>
        <div class="metric-title">SFI Compliance</div>
        <div class="metric-value">{sfi_compliance:.0f}%</div>
        <div class="metric-status" style="color: {sfi_color};">{sfi_emoji} {sfi_status}</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown("---")

# === AI INSIGHTS ===
st.markdown('<h2 class="section-title">💡 What You Can Do This Season</h2>', unsafe_allow_html=True)

with st.spinner("🤖 Generating personalized advice..."):
    insights = generate_ai_insights(
        esg_score=my_farm['esg_score'],
        e_score=my_farm['e_score'],
        s_score=my_farm['s_score'],
        emissions_per_ha=emissions_per_ha,
        emissions_per_tonne=0,  # Not available
        yield_per_ha=0,  # Not available
        female_share=0,  # Not available
        accidents=0,  # Not available
        farm_id=selected_farm
    )

for i, insight in enumerate(insights, 1):
    st.markdown(f'''
    <div class="insight-card">
        <span class="insight-number">{i}</span>
        <span class="insight-text">{insight}</span>
    </div>
    ''', unsafe_allow_html=True)

st.markdown("---")

# === CHARTS ===
st.markdown('<h2 class="section-title">📈 Visual Breakdown</h2>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Score Breakdown", "🌍 Emissions Sources", "📅 Progress Over Time"])

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
            st.plotly_chart(progress_fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("📊 Switch to 'Multi-Year Progress' mode to see trends!")

st.markdown("---")

# === EXPORT ===
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("📥 Download My Farm Report", type="primary", use_container_width=True):
        report_data = {
            'Farm ID': [selected_farm],
            'Farm Name': [my_farm['farm_name']],
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
            label="💾 Download CSV Report",
            data=csv,
            file_name=f"farm_{selected_farm}_report_{current_year}.csv",
            mime="text/csv",
            use_container_width=True
        )

st.markdown("---")
st.markdown('<p style="text-align: center; color: #999; font-size: 14px;">Made with 🌱 for farmers | AgriESG Dashboard © 2025</p>', 
            unsafe_allow_html=True)
