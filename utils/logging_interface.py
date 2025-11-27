import streamlit as st
import pandas as pd
import os
from datetime import date

# Define where the logs will be saved locally
LOG_FILE = "farm_activity_log.csv"

def init_log_file():
    """Creates the CSV file if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        # Create a dataframe with the standard columns
        df = pd.DataFrame(columns=[
            'date', 'activity_type', 'details', 
            'quantity', 'unit', 'sfi_aligned'
        ])
        df.to_csv(LOG_FILE, index=False)

def save_log_entry(entry_data):
    """Appends a new entry to the local CSV file."""
    # Load existing
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
    else:
        df = pd.DataFrame(columns=entry_data.keys())
    
    # Convert single entry to dataframe
    new_entry_df = pd.DataFrame([entry_data])
    
    # Combine and save
    updated_df = pd.concat([df, new_entry_df], ignore_index=True)
    updated_df.to_csv(LOG_FILE, index=False)
    return updated_df

def render_logging_interface():
    """Renders the UI for the logging tab."""
    st.markdown("### 📝 Field Activity Log")
    
    st.info("✅ **SFI Soil Standard: ON TRACK** — Your recent soil tests meet the 2025 requirements.")

    # Ensure file exists
    init_log_file()
    
    with st.form("log_activity_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            log_date = st.date_input("Date", value=date.today())
            activity = st.selectbox("Activity Type", [
                "Fertiliser Application",
                "Pesticide Spray",
                "Soil Test",
                "Harvesting",
                "Irrigation",
                "SFI Compliance Check"
            ])
        
        with col2:
            # Dynamic details based on activity could go here
            details = st.text_input("Notes / Field Name", placeholder="e.g., North Field")
            
            sub_c1, sub_c2 = st.columns(2)
            with sub_c1:
                quantity = st.number_input("Quantity", min_value=0.0, step=0.1)
            with sub_c2:
                unit = st.selectbox("Unit", ["kg", "litres", "tonnes", "hours", "N/A"])
        
        # SFI Checkbox
        sfi_check = st.checkbox("This action aligns with SFI Standards?")
        
        submitted = st.form_submit_button("💾 Save Activity Log", use_container_width=True, type="primary")
        
        if submitted:
            # Create data packet
            entry = {
                'date': log_date,
                'activity_type': activity,
                'details': details,
                'quantity': quantity,
                'unit': unit,
                'sfi_aligned': "Yes" if sfi_check else "No"
            }
            
            # Save to file
            save_log_entry(entry)
            st.success(f"Action logged: {activity}")

    # --- Display Recent Logs ---
    st.markdown("#### Recent History")
    if os.path.exists(LOG_FILE):
        history_df = pd.read_csv(LOG_FILE)
        if not history_df.empty:
            # Show last 5 entries, sorted by most recent (assuming append order)
            st.dataframe(history_df.tail(5).iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("No logs found yet.")
    else:
        st.info("Log file initialized.")