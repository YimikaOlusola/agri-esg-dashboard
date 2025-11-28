import streamlit as st
import pandas as pd
import time
from dotenv import load_dotenv
import uuid
import base64

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
    page_icon="assets/agriesg_icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
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
    
    .score-message {
        font-size: 22px;
        font-weight: 600;
        margin-top: 15px;
        color: var(--color-brown-dark);
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
    
    .status-healthy {
        color: var(--color-green-dark);
        background: var(--color-green-bg);
    }
    
    .status-low {
        color: var(--color-green-dark);
        background: #dcedc8;
    }
    
    .status-on-track {
        color: var(--color-brown-medium);
        background: #f5f5f5;
    }
    
    .status-needs-work {
        color: #c62828;
        background: #ffebee;
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

    .insight-item p {
        color: #5d4037 !important;
        margin: 0 !important;
    }
    
    div[data-testid="stPlotlyChart"] {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, var(--color-green-medium), var(--color-green-light)) !important;
        color: white !important;
        border: none !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True) 

load_css()

# === COLUMN MAPPING ===
COLUMN_MAPPING = {
    # Required
    'nitrogen_fertiliser_kg': 'fertiliser_kgN',
    'diesel_used_litres': 'diesel_litres',
    
    # Recommended
    'phosphate_fertiliser_kg': 'fertiliser_kgP2O5',
    'potash_fertiliser_kg': 'fertiliser_kgK2O',
    'selling_price_£_ton': 'selling_price_per_ton',
    
    # Optional
    'cover_crop_yes_no': 'cover_crop_planted_yes_no', 
    'trees_planted': 'trees_planted_count',          
}

REQUIRED_INTERNAL_COLS = [
    'farmer_name', 'farm_name', 'year', 'month', 'field_name', 
    'field_area_ha', 'crop_type', 'fertiliser_kgN', 
    'pesticide_applied_yes_no', 'diesel_litres', 
    'irrigation_applied_yes_no', 'livestock_present_yes_no'
]

# Display labels for user feedback
REQUIRED_DISPLAY_LABELS = {
    'farmer_name': 'Farmer Name',
    'farm_name': 'Farm Name',
    'year': 'Year',
    'month': 'Month',
    'field_name': 'Field Name',
    'field_area_ha': 'Field Area (ha)',
    'crop_type': 'Crop Type',
    'fertiliser_kgN': 'Nitrogen Fertiliser (kg)',
    'pesticide_applied_yes_no': 'Pesticide Applied (Yes/No)',
    'diesel_litres': 'Diesel Used (Litres)',
    'irrigation_applied_yes_no': 'Irrigation Applied (Yes/No)',
    'livestock_present_yes_no': 'Livestock Present (Yes/No)'
}

# Helper function for progress bars
def create_progress_bar(value, max_value=100, status="neutral"):
    """Create HTML progress bar"""
    percentage = min((value / max_value) * 100, 100) if max_value > 0 else 0
    
    if "healthy" in status or "low" in status:
        color_class = "progress-bar-green"
    elif "needs-work" in status:
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
    """Return plain English status text, CSS class, and emoji"""
    if lower_is_better:
        if value <= thresholds['excellent']:
            return "Low", "status-low", "🟢", 90
        elif value <= thresholds['good']:
            return "Okay", "status-on-track", "✔️", 65
        else:
            return "High", "status-needs-work", "🔴", 35
    else:
        if value >= thresholds['excellent']:
            return "Healthy", "status-healthy", "🟢", 90
        elif value >= thresholds['good']:
            return "Okay", "status-on-track", "⚠️", 65
        else:
            return "Needs Work", "status-needs-work", "🔴", 35

@st.cache_data(ttl=1800)
def load_and_process_data(file_bytes):
    """Load CSV and compute all metrics"""
    start_time = time.time()
    
    df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
    
    # 1. Clean column names (standardize)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '').str.replace('/', '_').str.replace('.', '').str.replace('£', '£')
    
    # 2. Rename columns using the mapping to match internal logic
    df = df.rename(columns=COLUMN_MAPPING)
    
    # 3. Handle Missing IDs
    if 'farm_id' not in df.columns and 'farm_name' in df.columns:
        df['farm_id'] = df.apply(lambda x: f"{str(x['farm_name'])[:3].upper()}-{hash(str(x['farm_name'])) % 1000:03d}", axis=1)
    
    # Compute
    df = compute_kpis(df)
    farm_df = aggregate_to_farm_level(df)
    
    load_time = time.time() - start_time
    return df, farm_df, load_time

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None


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
        st.markdown("### 📋 Data Requirements")
        st.markdown("""
        **Required:**
        - Farmer & Farm Name
        - Date (Year/Month)
        - Field details & Crops
        - Inputs: Nitrogen, Pesticides, Diesel, Irrigation
        - Livestock presence
        """)
    
    with col2:
        st.markdown("### 🎯 Get Started")
        st.markdown("""
        1. **Download** the CSV template below
        2. **Fill in** your farm's monthly field data
        3. **Upload** the file using the button on the left
        """)
    
    st.markdown("---")
    
    st.expander("**View Optional/Recommended Data Fields**").markdown("""
    Providing these fields improves the accuracy of your scores and unlocks more detailed insights:
                                                                      
    Recommended 
    * Farm ID
    * Field ID
    * Phosphate Fertiliser (kg)
    * Potash Fertiliser (kg)
    * Soil Type
    * Labour Hours
    * Yield (tons)
    * Selling Price (£/ton)
                                                                      
    Optional advanced 
    * Cover Crop (Yes/No)
    * Reduced Tillage (Yes/No)
    * Trees Planted
    * Soil Test Conducted (Yes/No)
    * Notes
    """)
    
    st.markdown("### 📥 Download CSV Template")
    
    # Create template matching new requirements
    template_data = {
        'Farmer Name': ['John Doe'],
        'Farm Name': ['Green Valley Farm'],
        'Year': [2025],
        'Month': ['2025-03'],
        'Field Name': ['North Field'],
        'Field Area (ha)': [15.0],
        'Crop Type': ['Wheat'],
        'Nitrogen Fertiliser (kg)': [25],
        'Pesticide Applied (Yes/No)': ['Yes'],
        'Diesel Used (Litres)': [120],
        'Irrigation Applied (Yes/No)': ['No'],
        'Livestock Present (Yes/No)': ['No'],
        'Farm ID': ['FARM-01'],
        'Yield (tons)': [''],
        'Soil Test Conducted (Yes/No)': ['']
    }
    
    template_df = pd.DataFrame(template_data)
    csv_template = template_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download Farm Data Template",
        data=csv_template,
        file_name="farm_data_template.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary"
    )
    
    st.stop()

# Load and validate data
file_bytes = uploaded_file.getvalue()

try:
    # First pass to check columns - MIMIC THE LOADING LOGIC to valid columns correctly
    raw_df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
    
    # 1. Clean
    raw_df.columns = raw_df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '').str.replace('/', '_').str.replace('.', '').str.replace('£', '£')
    
    # 2. Rename using Mapping
    raw_df = raw_df.rename(columns=COLUMN_MAPPING)
    
    current_cols = raw_df.columns.tolist()
    
    # Validate Required (using internal names now)
    missing_required = [
        REQUIRED_DISPLAY_LABELS[col] for col in REQUIRED_INTERNAL_COLS 
        if col not in current_cols
    ]
    
    if missing_required:
        st.error("### ⚠️ Missing Required Columns")
        st.markdown("The following columns are missing or named incorrectly:")
        for col in missing_required:
            st.markdown(f"- ❌ **{col}**")
        st.stop()
    
    # Check for Optional/Recommended presence for the TIP
    # Check against a list of known optional internal names
    optional_internal_names = [
        'fertiliser_kgP2O5', 'fertiliser_kgK2O', 'soil_type', 'labour_hours',
        'yield_tons', 'selling_price_per_ton', 'cover_crop_planted_yes_no',
        'reduced_tillage_yes_no', 'trees_planted_count', 'soil_test_conducted_yes_no'
    ]
    
    has_optional = any(col in current_cols for col in optional_internal_names)
    
    if not has_optional:
        st.info("💡 **Tip:** Adding optional fields like yield and soil tests improves insight and strengthens your sustainability profile.")
    
    # Process data
    df, farm_df, load_time = load_and_process_data(file_bytes)

except Exception as e:
    st.error("### ⚠️ File Problem")
    st.markdown(f"Error reading file: {str(e)}")
    # st.code(str(e)) # Uncomment to debug
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
    
    view_mode = st.radio("📅 View Mode", ["Current Year Snapshot", "Multi-Year Progress"])
    
    if view_mode == "Current Year Snapshot":
        selected_year = st.selectbox("Select Year", years, index=len(years)-1)
        selected_years = [selected_year]
    else:
        selected_years = st.multiselect("Select Years", years, default=years)

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

# === HERO SECTION / HEADER ===
# Load the icon
icon_path = "assets/agriesg_icon.png" # Ensure this path matches exactly
icon_base64 = get_base64_image(icon_path)

# Build the image tag or fallback to emoji if file missing
if icon_base64:
    icon_html = f'<img src="data:image/png;base64,{icon_base64}" style="height: 50px; vertical-align: middle; margin-bottom: 8px; margin-right: 10px;">'
else:
    icon_html = "🌾" # Fallback if image not found

st.markdown(f'<h1 class="main-title">{icon_html} AgriESG Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Simple insights for better farming</p>', unsafe_allow_html=True)
st.markdown("---")

gauge_fig = create_gauge_chart(
    value=my_farm['esg_score'],
    title=f"Your Farm ESG Score ({current_year})"
)

col_left, col_center, col_right = st.columns([1, 2, 1])
with col_center:
    st.plotly_chart(gauge_fig, use_container_width=True, config={'displayModeBar': False})

score = my_farm['esg_score']
if score >= 70:
    message = "🟢 Healthy Profile! You're leading the way."
    color = "#2d5016"
elif score >= 50:
    message = "✔️ On Track! A few improvements will help."
    color = "#c9800b"
else:
    message = "🔴 Needs Work. Let's improve your practices."
    color = "#c62828"

st.markdown(f'''
<div class="hero-section">
    <p class="score-message" style="color: {color}; margin: 0;">{message}</p>
</div>
''', unsafe_allow_html=True)

# === QUICK STATS ===
st.markdown('<h2 class="section-title">Quick Stats</h2>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

total_area = my_farm['total_farm_area_ha']
emissions_per_ha = my_farm['emissions_per_ha']
n_per_ha = my_farm['n_per_ha']
# Check if SFI columns exist (might be 0 if optional SFI data missing)
sfi_cols = ['sfi_soil_compliance_rate', 'sfi_nutrient_compliance_rate', 'sfi_hedgerow_compliance_rate']
sfi_avg = sum(my_farm.get(c, 0) for c in sfi_cols) / 3 * 100

with col1:
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid #4a7c29;">
        <div class="metric-icon">🌾</div>
        <div class="metric-title">Total Farm Area</div>
        <div class="metric-value">{total_area:.1f} ha</div>
        <div class="metric-status status-on-track">✔️ On track</div>
    </div>
    ''', unsafe_allow_html=True)

with col2:
    status_text, status_class, emoji, norm_score = get_status_info(
        emissions_per_ha, {'excellent': 30, 'good': 50}, lower_is_better=True
    )
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid {'#4a7c29' if 'healthy' in status_class or 'low' in status_class else '#c62828'};">
        <div class="metric-icon">🌫️</div>
        <div class="metric-title">Emissions</div>
        <div class="metric-value">{emissions_per_ha:.0f} kg/ha</div>
        <div class="metric-status {status_class}">{emoji} {status_text}</div>
    </div>
    ''', unsafe_allow_html=True)

with col3:
    status_text, status_class, emoji, norm_score = get_status_info(
        n_per_ha, {'excellent': 50, 'good': 100}, lower_is_better=True
    )
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid {'#4a7c29' if 'healthy' in status_class or 'low' in status_class else '#c62828'};">
        <div class="metric-icon">🧪</div>
        <div class="metric-title">Nitrogen Use</div>
        <div class="metric-value">{n_per_ha:.0f} kg/ha</div>
        <div class="metric-status {status_class}">{emoji} {status_text}</div>
    </div>
    ''', unsafe_allow_html=True)

with col4:
    status_text, status_class, emoji, norm_score = get_status_info(
        sfi_avg, {'excellent': 80, 'good': 50}
    )
    st.markdown(f'''
    <div class="metric-card" style="border-left: 5px solid {'#4a7c29' if 'healthy' in status_class else '#c62828'};">
        <div class="metric-icon">📋</div>
        <div class="metric-title">Compliance</div>
        <div class="metric-value">{sfi_avg:.0f}%</div>
        <div class="metric-status {status_class}">{emoji} {status_text}</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown("---")

# === AI INSIGHTS ===
st.markdown('<h2 class="section-title">💡 What You Can Do This Season</h2>', unsafe_allow_html=True)

# Use Farm Name for greeting as requested
greeting_name = my_farm.get('farm_name', 'Farm')

with st.spinner(f"🤖 Generating advice for {greeting_name}..."):
    insights = generate_ai_insights(
        esg_score=my_farm['esg_score'],
        e_score=my_farm['e_score'],
        s_score=my_farm['s_score'],
        emissions_per_ha=emissions_per_ha,
        emissions_per_tonne=0,
        yield_per_ha=my_farm.get('yield_tons', 0) / max(total_area, 1),
        female_share=0,
        accidents=0,
        farm_id=selected_farm,
        farmer_name=greeting_name 
    )

insights_html = '<div class="insights-container">'
for insight in insights:
    insights_html += f'<div class="insight-item"><p>{insight}</p></div>'
insights_html += '</div>'

st.markdown(insights_html, unsafe_allow_html=True)

st.markdown("---")

# === CHARTS ===
st.markdown('<h2 class="section-title">Visual Breakdown</h2>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["Score Breakdown", "Emissions Sources", "Progress", "Logs"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Your ESG Score Components")
        pie_fig = create_score_breakdown_pie(
            e_score=my_farm['e_score'],
            s_score=my_farm['s_score'],
            g_score=my_farm['g_score']
        )
        st.plotly_chart(pie_fig, use_container_width=True)
    with col2:
        st.markdown("### Farm Performance Comparison")
        all_farms = esg_df[esg_df['year'] == current_year]
        comparison_fig = create_comparison_bar(my_farm, all_farms)
        st.plotly_chart(comparison_fig, use_container_width=True)

with tab2:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Emissions by Source")
        donut_fig = create_emissions_donut(
            fertilizer=my_farm['emissions_fertilizer'],
            diesel=my_farm['emissions_diesel'],
            electricity=0
        )
        st.plotly_chart(donut_fig, use_container_width=True)
    with col2:
        st.metric("Total Emissions", f"{my_farm['total_emissions']:.0f} kg CO₂e")

with tab3:
    if len(selected_years) > 1 and view_mode == "Multi-Year Progress":
        st.markdown("### Progress Over Time")
        hist_data = [{"year": y, "esg_score": filtered_esg[filtered_esg['year']==y].iloc[0]['esg_score']} for y in selected_years]
        line_fig = create_progress_line_chart(hist_data)
        st.plotly_chart(line_fig, use_container_width=True)
    else:
        st.info("Select 'Multi-Year Progress' to see trends.")

with tab4:
    render_logging_interface()
st.markdown("---")

# === EXPORT ===
st.markdown('<h2 class="section-title">Download Your Report</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

# Prepare the greeting name based on Farm Name (matching AI insights logic)
greeting_name = my_farm.get('farm_name', 'Farm Team')

with col1:
    if st.button("Download PDF Report", type="primary", use_container_width=True):
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
                farmer_name=greeting_name, 
                year=current_year,
                insights_list=insights,
                gauge_fig=gauge_fig,
                pie_fig=pie_fig,
                donut_fig=donut_fig,
                bar_fig=comparison_fig,
                line_fig=line_fig_for_pdf
            )
            
            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name=f"farm_{selected_farm}_esg_report_{current_year}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

with col2:
    if st.button("Download CSV Report", type="primary", use_container_width=True):
        report_data = {
            'Farm ID': [selected_farm],
            'Farm Name': [my_farm['farm_name']],
            'Report For': [greeting_name], 
            'Year': [current_year],
            'ESG Score': [my_farm['esg_score']],
            'Environment Score': [my_farm['e_score']],
            'Social Score': [my_farm['s_score']],
            'Governance Score': [my_farm['g_score']],
            'Total Area (ha)': [total_area],
            'Emissions (kg/ha)': [emissions_per_ha],
            'Nitrogen Use (kg/ha)': [n_per_ha],
            'SFI Compliance (%)': [sfi_avg]
        }
        
        report_df = pd.DataFrame(report_data)
        csv = report_df.to_csv(index=False)
        
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"farm_{selected_farm}_report_{current_year}.csv",
            mime="text/csv",
            use_container_width=True
        )