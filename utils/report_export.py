from typing import Dict, Any
import io

import pandas as pd
from fpdf import FPDF


def build_excel_from_report(report_data: Dict[str, Any]) -> bytes:
    """
    Create an Excel file with emissions summary and return it as raw bytes.

    This is designed for the Emissions & Performance report and uses:
      - scope1_total
      - scope3_total
      - total_emissions
      - scope1_intensity_kg_per_ha
      - scope3_intensity_kg_per_ha
      - intensity_kg_per_ha
    from the report_data dict.
    """
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
                "Scope": "Scope Total",
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
    """
    Generate a simple emissions PDF using FPDF.

    Expects in report_data:
      - farm_name
      - report_year
      - base_year
      - number_of_fields
      - total_area_ha
      - scope1_total
      - scope3_total
      - total_emissions
      - scope1_intensity_kg_per_ha
      - scope3_intensity_kg_per_ha
      - intensity_kg_per_ha
      - fertiliser_emissions_tco2e
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Fixed content width to avoid "Not enough horizontal space" errors
    full_width = 180  # approximate width inside margins

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Farm Emissions & Sustainability Report", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.ln(5)
    pdf.cell(0, 8, f"Farm: {report_data['farm_name']}", ln=True)
    pdf.cell(0, 8, f"Reporting year: {report_data['report_year']}", ln=True)
    pdf.cell(0, 8, f"Base year: {report_data['base_year']}", ln=True)
    pdf.cell(
        0,
        8,
        f"Boundary: {report_data['number_of_fields']} fields, "
        f"{report_data['total_area_ha']:.2f} ha",
        ln=True,
    )

    # Emissions summary
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Emissions Summary", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.ln(4)
    pdf.multi_cell(
        full_width,
        6,
        (
            f"Scope 1 (on-farm fuel use): {report_data['scope1_total']:.2f} tCO2e "
            f"({report_data['scope1_intensity_kg_per_ha']:.1f} kgCO2e/ha)"
        ),
    )
    pdf.multi_cell(
        full_width,
        6,
        (
            f"Scope 3 (purchased fertiliser): {report_data['scope3_total']:.2f} tCO2e "
            f"({report_data['scope3_intensity_kg_per_ha']:.1f} kgCO2e/ha)"
        ),
    )
    pdf.multi_cell(
        full_width,
        6,
        (
            f"Total emissions: {report_data['total_emissions']:.2f} tCO2e "
            f"({report_data['intensity_kg_per_ha']:.1f} kgCO2e/ha)"
        ),
    )

    # Scope 3 breakdown
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Scope 3 Breakdown", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.ln(4)
    pdf.multi_cell(
        full_width,
        6,
        f"Purchased fertilisers: {report_data['fertiliser_emissions_tco2e']:.2f} tCO2e",
    )

    # Key metrics
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Key Metrics", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(4)
    pdf.multi_cell(
        full_width,
        6,
        (
            f"Total emissions: {report_data['total_emissions']:.2f} tCO2e\n"
            f"Average emissions intensity: {report_data['intensity_kg_per_ha']:.1f} kgCO2e/ha"
        ),
    )

    # In fpdf2, output(dest="S") returns a bytearray, so we just cast to bytes
    pdf_bytes = bytes(pdf.output(dest="S"))
    return pdf_bytes
