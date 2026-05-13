import streamlit as st
from typing import Optional
from components.ui import page_header


PAGE_COPY = {
    "AI Vision Dashboard": "Upload a shelf image, choose the application context, and run product detection with optional price-tag extraction.",
    "Dashboard Monitoring": "Pantau performa analisis rak, kelengkapan data master, dan hasil compliance dari satu dashboard yang rapi dan terpusat.",
    "Planogram List": "Maintain shelf planograms, preview layouts, and verify uploaded shelf photos against expected product positions.",
    "Product List": "Review product master data, ownership metadata, brand links, and model status.",
    "Brand List": "Manage brand master data used for product grouping and share-of-space analysis.",
    "Analysis Result": "Inspect detection output, product facings, share of space, planogram compliance, and raw API payloads.",
    "Hasil Deteksi": "Tinjau hasil inferensi, kualitas facing, share of space, dan indikasi non-compliance dalam satu workspace.",
}


def render_header(title: str, description: Optional[str] = None, eyebrow: str = "Pocari Vision - Planogram Monitor", chip: str = ""):
    page_header(title, description if description is not None else PAGE_COPY.get(title, ""), eyebrow, chip or "AI Vision")
