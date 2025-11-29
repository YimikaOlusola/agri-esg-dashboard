from typing import Dict, Any
import io
import pandas as pd
from fpdf import FPDF


def build_excel_from_report(report_data: Dict[str, Any]) -> bytes:
    """Create an Excel file with emissions summary and return as bytes."""
    buffer = io.BytesIO()

    summary_df = pd.DataFrame(
        [
            {
                "Scope": "Scope 1",
                "Description": "On-farm fuel use (diesel, etc.)",
                "Emissions (tCO2e)": report_data["scope1_total"],
                "Intensity (kgCO2e/ha)": report_data["scope1_intensity_kg_per_ha"],
            },
            {
                "Scope": "Scope 3",
                "Description": "Purchased fertiliser (upstream)",
                "Emissions (tCO2e)": report_data["scope3_total"],
                "Intensity (kgCO2e/ha)": report_data["scope3_intensity_kg_per_ha"],
            },
            {
                "Scope": "Total",
                "Description": "Total emissions",
                "Emissions (tCO2e)": report_data["total_emissions"],
                "Intensity (kgCO2e/ha)": report_data["intensity_kg_per_ha"],
            },
        ]
    )

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Emissions Summary", index=False)

    buffer.seek(0)
    return buffer.getvalue()


def render_report_to_pdf(report_data: Dict[str, Any]) -> bytes:
    """Generate a simple emissions PDF report using FPDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Effective page width (A4 minus margins)
    epw = pdf.w - 2 * pdf.l_margin

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Farm Emissions & Sustainability Report", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.ln(5)
    pdf.cell(0, 8, f"Farm: {report_data.get('farm_name', 'Farm')}", ln=True)
    pdf.cell(0, 8, f"Reporting year: {report_data.get('report_year', '-')}", ln=True)
    pdf.cell(0, 8, f"Base year: {report_data.get('base_year', '-')}", ln=True)
    pdf.cell(
        0,
        8,
        "Boundary: "
        f"{report_data.get('number_of_fields', 0)} fields, "
        f"{report_data.get('total_area_ha', 0.0):.2f} ha",
        ln=True,
    )

    # Emissions summary
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Emissions Summary", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.ln(4)

    # Use explicit width = epw and reset X so FPDF always has enough space
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(
        epw,
        6,
        (
            "Scope 1 (on-farm fuel use): "
            f"{report_data.get('scope1_total', 0.0):.2f} tCO2e "
            f"({report_data.get('scope1_intensity_kg_per_ha', 0.0):.1f} kgCO2e/ha)"
        ),
    )

    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(
        epw,
        6,
        (
            "Scope 3 (purchased fertiliser): "
            f"{report_data.get('scope3_total', 0.0):.2f} tCO2e "
            f"({report_data.get('scope3_intensity_kg_per_ha', 0.0):.1f} kgCO2e/ha)"
        ),
    )

    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(
        epw,
        6,
        (
            "Total emissions: "
            f"{report_data.get('total_emissions', 0.0):.2f} tCO2e "
            f"({report_data.get('intensity_kg_per_ha', 0.0):.1f} kgCO2e/ha)"
        ),
    )

    # Scope 3 breakdown
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Scope 3 Breakdown", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.ln(4)

    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(
        epw,
        6,
        (
            "Purchased fertilisers: "
            f"{report_data.get('fertiliser_emissions_tco2e', 0.0):.2f} tCO2e"
        ),
    )

    # Key metrics
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Key Metrics", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(4)

    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(
        epw,
        6,
        (
            "Total emissions: "
            f"{report_data.get('total_emissions', 0.0):.2f} tCO2e\n"
            "Average emissions intensity: "
            f"{report_data.get('intensity_kg_per_ha', 0.0):.1f} kgCO2e/ha"
        ),
    )

    pdf_bytes = pdf.output(dest="S").encode("latin1")
    return pdf_bytes


def render_sfi_plan_pdf(report_data: Dict[str, Any]) -> bytes:
    """
    Generate an SFI-ready plan PDF from the master report_data dict.

    Expects:
      report_data["farm"]
      report_data["policy"] or ["sfi"]
      report_data["sfi_plan"]["summary"]
      report_data["sfi_plan"]["land_parcels"]
    """
    farm = report_data.get("farm", {})
    policy = report_data.get("policy", report_data.get("sfi", {}))
    sfi_plan = report_data.get("sfi_plan", {})
    summary = sfi_plan.get("summary", {})
    parcels = sfi_plan.get("land_parcels", [])

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SFI Action Plan", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.ln(4)
    pdf.cell(0, 8, f"Farm: {farm.get('name', 'Farm')}", ln=True)
    pdf.cell(0, 8, f"Farm ID: {farm.get('id', '-')}", ln=True)
    pdf.cell(0, 8, f"Year: {farm.get('year', '-')}", ln=True)
    pdf.cell(0, 8, f"Policy layer: {policy.get('policy_name', 'SFI')}", ln=True)

    pdf.ln(8)
    pdf.set_font("Arial", "I", 11)
    pdf.multi_cell(
        0,
        6,
        "This document summarises SFI-relevant actions and land parcels based on your "
        "farm data. It is designed to support SFI applications and advisor discussions.",
    )

    # Summary
    pdf.ln(8)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Farm SFI Summary", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.ln(4)
    pdf.multi_cell(
        0,
        6,
        f"Total area: {summary.get('total_area_ha', 0.0):.2f} ha across "
        f"{summary.get('num_fields', 0)} fields.",
    )

    pdf.ln(2)
    pdf.multi_cell(
        0,
        6,
        "Readiness by practice (share of farm area with each action in place):",
    )
    pdf.ln(2)
    pdf.cell(
        0,
        6,
        f"- Cover crops established on: "
        f"{summary.get('cover_crop_area_pct', 0.0):.1f}% of area",
        ln=True,
    )
    pdf.cell(
        0,
        6,
        f"- Reduced / conservation tillage on: "
        f"{summary.get('reduced_tillage_area_pct', 0.0):.1f}% of area",
        ln=True,
    )
    pdf.cell(
        0,
        6,
        f"- Fields with recent soil tests: "
        f"{summary.get('soil_test_area_pct', 0.0):.1f}% of area",
        ln=True,
    )
    pdf.cell(
        0,
        6,
        f"- Fields with trees / agroforestry: "
        f"{summary.get('fields_with_trees_pct', 0.0):.1f}% of area",
        ln=True,
    )

    pdf.ln(4)
    pdf.multi_cell(
        0,
        6,
        f"Overall SFI/policy readiness score: "
        f"{policy.get('readiness_pct', 0.0):.1f}%.",
    )

    # Land parcels table
    pdf.ln(8)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Field-by-field SFI actions", ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 6, "Field ID", border=1)
    pdf.cell(40, 6, "Field Name", border=1)
    pdf.cell(15, 6, "Area", border=1)
    pdf.cell(25, 6, "Crop", border=1)
    pdf.cell(20, 6, "Soil", border=1)
    pdf.cell(20, 6, "Cover crop", border=1)
    pdf.cell(25, 6, "Reduced till", border=1)
    pdf.cell(20, 6, "Soil test", border=1)
    pdf.ln()

    pdf.set_font("Arial", "", 9)
    for p in parcels:
        pdf.cell(25, 6, str(p.get("field_id", ""))[:15], border=1)
        pdf.cell(40, 6, str(p.get("field_name", ""))[:22], border=1)
        pdf.cell(15, 6, f"{p.get('field_area_ha', 0.0):.1f}", border=1)
        pdf.cell(25, 6, str(p.get("crop_type", ""))[:12], border=1)
        pdf.cell(20, 6, str(p.get("soil_type", ""))[:10], border=1)
        pdf.cell(20, 6, "Yes" if p.get("cover_crop") else "No", border=1)
        pdf.cell(25, 6, "Yes" if p.get("reduced_tillage") else "No", border=1)
        pdf.cell(20, 6, "Yes" if p.get("soil_test_conducted") else "No", border=1)
        pdf.ln()

    pdf.ln(8)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Notes and next steps", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(4)
    pdf.multi_cell(
        0,
        6,
        "Use this plan to discuss SFI options with your advisor or delivery body. "
        "You can attach this document as supporting evidence showing current actions, "
        "eligible land, and management practices planned for the agreement period.",
    )

    pdf.ln(10)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, "Farmer / manager name: ___________________________", ln=True)
    pdf.cell(0, 6, "Date: ___________________________", ln=True)
    pdf.cell(0, 6, "Signature: ___________________________", ln=True)

    pdf_bytes = pdf.output(dest="S").encode("latin1")
    return pdf_bytes
