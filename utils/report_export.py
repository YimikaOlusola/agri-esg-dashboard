# 3) SFI Plan (SFI / Government)
elif report_key == "sfi_plan":
    st.markdown("### SFI Plan")
    st.caption("Field-by-field SFI actions and readiness for use in SFI applications.")

    from utils.report_export import render_sfi_plan_pdf

    policy_results = report_data.get("policy") or report_data.get("sfi", {})

    soil_pct = policy_results.get("soil_pct", 0.0)
    nutrient_pct = policy_results.get("nutrient_pct", 0.0)
    hedgerow_pct = policy_results.get("hedgerow_pct", 0.0)
    readiness_pct = policy_results.get("readiness_pct", 0.0)

    # Simple CSV snapshot as before
    sfi_plan_df = pd.DataFrame(
        [
            {
                "Farm ID": report_data["farm"]["id"],
                "Farm Name": report_data["farm"]["name"],
                "Year": report_data["farm"]["year"],
                "SFI Soil Compliance (%)": soil_pct,
                "SFI Nutrient Compliance (%)": nutrient_pct,
                "SFI Hedgerow Compliance (%)": hedgerow_pct,
                "Overall SFI Readiness (%)": readiness_pct,
                "Policy Layer": policy_results.get("policy_name", "SFI"),
            }
        ]
    )
    sfi_csv = sfi_plan_df.to_csv(index=False).encode("utf-8")

    col1, col2 = st.columns(2)

    # PDF button – full SFI Action Plan
    if "pdf" in report_meta["formats"]:
        with col1:
            if st.button("PDF – SFI Action Plan", type="primary", use_container_width=True):
                with st.spinner("🔄 Generating SFI plan..."):
                    sfi_pdf = render_sfi_plan_pdf(report_data)
                    st.download_button(
                        "Download SFI Plan PDF",
                        data=sfi_pdf,
                        file_name=f"farm_{selected_farm}_sfi_plan_{current_year}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

    # CSV snapshot button
    if "csv" in report_meta["formats"]:
        with col2:
            st.download_button(
                "CSV – SFI Plan Snapshot",
                data=sfi_csv,
                file_name=f"farm_{selected_farm}_sfi_plan_{current_year}.csv",
                mime="text/csv",
                use_container_width=True,
            )
