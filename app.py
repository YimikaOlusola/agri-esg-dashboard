import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load ESG data and ensure Year is treated as string to avoid comma formatting
df = pd.read_csv("esg_data.csv")
df["Year"] = df["Year"].astype(str)

st.set_page_config(page_title="ESG Dashboard", layout="wide")
st.title("ESG Dashboard for Agricultural SMEs")
st.markdown("This dashboard visualizes sustainability performance across key metrics from 2021 to 2025.")

# Show raw data
with st.expander("View Raw ESG Data"):
    st.dataframe(df)

# Line chart: Carbon Emissions
st.subheader("Carbon Emissions Over Time")
st.line_chart(df.set_index("Year")["Carbon Emissions (tonnes CO2e)"])

# Line chart: Biodiversity Score (robust column handling)
st.subheader("Biodiversity Score Trend")
biodiversity_col = None
for col in df.columns:
    if "Biodiversity" in col:
        biodiversity_col = col
        break

if biodiversity_col:
    st.line_chart(df.set_index("Year")[biodiversity_col])
else:
    st.error("Biodiversity Score column not found. Please check your CSV file.")

# Custom labels for charts
custom_labels = {
    "Carbon Emissions (tonnes CO2e)": "Carbon Emission",
    "Water Usage (m3)": "Water Usage (L)",
    "Waste Generated (kg)": "Waste Generated",
    "Labour Hours (per hectare)": "Labour Hours (hr)",
    "Fertilizer Usage (kg/ha)": "Fertilizer Usage (kg)",
    "Energy Consumption (kWh)": "Energy Consumption",
    biodiversity_col: "Biodiversity Score"
}

# Horizontal bar chart: ESG Snapshot for 2025
st.subheader("2025 ESG Snapshot (Horizontal)")
if "2025" in df["Year"].values:
    latest = df[df["Year"] == "2025"].drop("Year", axis=1).T
    latest = latest.rename(index=custom_labels)
    latest.columns = ["2025"]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(latest.index, latest["2025"], color="skyblue")
    ax.set_xlabel("Value")
    ax.set_title("2025 ESG Snapshot")
    st.pyplot(fig)
else:
    st.error("No data found for year 2025.")

# Radar chart: 2025 ESG Profile
st.subheader("2025 ESG Profile (Radar Chart)")
metrics = list(custom_labels.keys())

if all(metric in df.columns for metric in metrics):
    values_2025 = df[df["Year"] == "2025"][metrics].values.flatten()
    min_vals = df[metrics].min()
    max_vals = df[metrics].max()
    normalized = (values_2025 - min_vals) / (max_vals - min_vals) * 100

    labels = [custom_labels[m] for m in metrics]
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    normalized = np.concatenate((normalized, [normalized[0]]))
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, normalized, color='green', linewidth=2)
    ax.fill(angles, normalized, color='green', alpha=0.25)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_title("2025 ESG Profile", fontsize=14)
    ax.set_ylim(0, 100)

    st.pyplot(fig)
else:
    st.error("One or more ESG metrics are missing from the CSV file.")

# Insights
st.subheader("Key Insights")
st.markdown("- Carbon emissions reduced by 27 percent from 2021 to 2025.")
st.markdown("- Biodiversity score improved significantly, reflecting regenerative practices.")
st.markdown("- Energy consumption dropped by over 10 percent, showing efficiency gains.")
st.markdown("- Fertilizer usage decreased steadily, supporting soil health and sustainability.")

# Footer
st.markdown("---")
st.caption("Built with Streamlit | Data based on UK agricultural estimates | MVP for ESG innovation endorsement")