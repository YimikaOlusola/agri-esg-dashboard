# utils/report_defs.py

REPORT_DEFINITIONS = {
    "emissions_performance": {
        "label": "Emissions & Performance",
        "stakeholder": "Banks / lenders",
        # What formats this report should offer
        "formats": ["pdf", "excel"],
    },
    "scope3_supply_chain": {
        "label": "Scope 3 Supply Chain Report",
        "stakeholder": "Supermarkets / buyers",
        "formats": ["excel", "csv"],
    },
    "sfi_plan": {
        "label": "SFI Plan",
        "stakeholder": "SFI / Government",
        # Right now we have CSV only – we'll add PDF later
        "formats": ["csv"],
    },
    "csv_esg_summary": {
        "label": "CSV & ESG Summary",
        "stakeholder": "Advisors, agronomists",
        "formats": ["csv"],
    },
    "sustainability_summary": {
        "label": "Sustainability Summary",
        "stakeholder": "Farmers",
        "formats": ["pdf"],
    },
}
