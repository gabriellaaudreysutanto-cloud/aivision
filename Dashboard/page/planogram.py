import streamlit as st
import pandas as pd
import base64
import mimetypes
import os
import re
import hashlib
from difflib import SequenceMatcher
from html import escape
from PIL import Image
from components.header import render_header
from components.ui import columns, kpi_card, list_item_card, markdown_html, paginate_dataframe, section_header, warning_card
from utils.db import fetch_all, execute_query

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
css_path = os.path.join(BASE_DIR, "assets", "styles_table.css")
MODEL_PATH = os.getenv("YOLO_MODEL_PATH", os.path.join(BASE_DIR, "models", "best.pt"))
PLANOGRAM_UPLOAD_DIR = os.path.join("uploads", "planogram_checks")
PLANOGRAM_OUTPUT_DIR = os.path.join("output", "planogram_checks")

PRODUCT_NAME_ALIASES = {
    "pocari": "pocari sweat",
    "pocari sweat": "pocari sweat",
    "ion": "ion water",
    "ion water": "ion water",
    "ion water 350": "ion water",
    "ion water 330": "ion water",
    "soy joy": "soyjoy",
    "soyjoy": "soyjoy",
    "or beng": "or beng",
    "fibe": "fibe mini",
    "fibe mini": "fibe mini",
    "adem sari": "adem sari",
    "you c1000": "youc1000",
    "youc1000": "youc1000",
    "hydro coco": "hydrococo",
    "hydrococo": "hydrococo",
    "hemaviton": "hemaviton",
    "isoplus": "isoplus",
}

PACK_VARIANTS = ("orange", "blue", "yellow", "pink", "purple", "white", "teal")


def _product_pack_style(label: str, category: str) -> tuple[str, str]:
    normalized = normalize_product_name(label)
    raw_label = str(label or "").lower()

    if any(token in normalized for token in ["pocari", "ion water", "isoplus", "hydro plus"]):
        color = "blue"
    elif any(token in normalized for token in ["youc1000", "c1000"]):
        color = "yellow"
    elif "fibe" in normalized:
        color = "pink"
    elif any(token in normalized for token in ["hydrococo", "hydro coco"]):
        color = "teal"
    elif "mizone" in normalized:
        color = "purple"
    elif category == "own":
        color = "blue"
    elif category == "competitor":
        color = "orange"
    else:
        color = PACK_VARIANTS[sum(ord(char) for char in raw_label) % len(PACK_VARIANTS)]

    if any(token in raw_label for token in ["can", "kaleng", "330"]):
        shape = "can"
    elif any(token in normalized for token in ["hydrococo", "hydro coco", "soyjoy"]):
        shape = "carton"
    else:
        shape = "bottle"

    return shape, color


def _short_pack_label(label: str) -> str:
    text = normalize_product_name(label) or str(label or "").strip()
    if not text:
        return "-"
    words = text.replace("_", " ").split()
    return " ".join(words[:2])


def _render_planogram_cell(cell: dict) -> str:
    category = escape(str(cell.get("category", "empty")))
    row = escape(str(cell.get("row", "-")))
    col = escape(str(cell.get("col", "-")))
    label = str(cell.get("label", "-"))

    if cell.get("category") == "empty":
        return (
            f"<div class='plano-cell empty' title='Row {row}, Column {col}'>"
            f"<span class='plano-empty-label'>{row}.{col}</span>"
            "</div>"
        )

    image_src = cell.get("image")
    if image_src:
        full_label = escape(label)
        return (
            f"<div class='plano-cell {category} has-image' title='Row {row}, Column {col}: {full_label}'>"
            f"<img class='plano-product-image' src='{escape(str(image_src), quote=True)}' alt='{full_label}'>"
            f"<div class='plano-product-name'>{full_label}</div>"
            "</div>"
        )

    shape, color = _product_pack_style(label, str(cell.get("category", "")))
    pack_label = escape(_short_pack_label(label))
    full_label = escape(label)
    star_badge = "<span class='plano-pocari-star' title='Produk Pocari'></span>" if cell.get("category") == "own" else ""
    return (
        f"<div class='plano-cell {category}' title='Row {row}, Column {col}: {full_label}'>"
        f"{star_badge}"
        f"<div class='plano-pack {escape(shape)} {escape(color)}'>"
        "<span class='plano-pack-cap'></span>"
        "<div class='plano-pack-body'>"
        f"<span class='plano-pack-label'>{pack_label}</span>"
        "</div>"
        "</div>"
        f"<div class='plano-product-name'>{full_label}</div>"
        "</div>"
    )


@st.cache_data(show_spinner=False, ttl=60)
def load_planogram_list() -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            mp.planogram_id,
            mp.app_id,
            mp.name AS planogram_name,
            mp.content,
            mp.created_at,
            mp.updated_at
        FROM master_planograms mp
        WHERE mp.deleted_at IS NULL
        ORDER BY mp.updated_at DESC
        """
    )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False, ttl=60)
def load_planogram_items(planogram_id: str) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            mpi.planogram_id,
            mpi.shelf_row,
            mpi.shelf_column,
            mpi.expected_count,
            mpi.product_id,
            mp.product_name,
            mp.short_name,
            mp.product_image,
            mp.product_type,
            mb.brand_name,
            mb.brand_group
        FROM master_planogram_items mpi
        LEFT JOIN master_products mp
            ON mpi.product_id = mp.product_id
        LEFT JOIN master_brands mb
            ON mp.brand_id = mb.brand_id
        WHERE mpi.planogram_id = %s
        ORDER BY mpi.shelf_row, mpi.shelf_column
        """,
        (planogram_id,)
    )
    return pd.DataFrame(rows)


def apply_planogram_styles():
    markdown_html(
        """
        <style>
            .plano-workspace {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: 18px;
                padding: 22px;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.05);
                margin-top: 16px;
            }
            .plano-panel-title {
                color: var(--text);
                font-size: 20px;
                font-weight: 650;
                margin: 0 0 8px 0;
            }
            .plano-muted {
                color: var(--text-secondary);
                font-size: 13px;
                margin-bottom: 12px;
            }
            .plano-empty-photo {
                min-height: 360px;
                border: 1.5px dashed rgba(0, 113, 227, 0.24);
                border-radius: 18px;
                background: #f9f9fb;
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--text-secondary);
                font-weight: 600;
                text-align: center;
                padding: 24px;
            }
            .plano-toolbar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
                margin: 4px 0 14px 0;
                flex-wrap: wrap;
            }
            .plano-legend {
                display: flex;
                gap: 16px;
                align-items: center;
                flex-wrap: wrap;
                color: #435069;
                font-size: 13px;
                font-weight: 500;
            }
            .plano-legend-item {
                display: inline-flex;
                align-items: center;
                gap: 7px;
            }
            .plano-swatch {
                width: 18px;
                height: 18px;
                border-radius: 6px;
                border: 1px solid rgba(24, 45, 80, 0.14);
                display: inline-block;
            }
            .plano-grid-wrap {
                overflow-x: auto;
                padding: 8px 2px 4px 2px;
            }
            .plano-grid {
                display: grid;
                gap: 10px;
                min-width: 680px;
            }
            .plano-cell {
                align-items: center;
                aspect-ratio: 0.84;
                background: rgba(255, 255, 255, 0.94);
                border: 1.4px solid rgba(24, 45, 80, 0.12);
                border-radius: 14px;
                box-sizing: border-box;
                color: var(--text-secondary);
                display: flex;
                flex-direction: column;
                gap: 5px;
                justify-content: center;
                min-height: 86px;
                overflow: hidden;
                padding: 7px;
                position: relative;
                text-align: center;
            }
            .plano-cell:after {
                background: linear-gradient(180deg, rgba(255,255,255,0.0), rgba(0,0,0,0.035));
                bottom: 0;
                content: "";
                height: 34%;
                left: 0;
                pointer-events: none;
                position: absolute;
                right: 0;
            }
            .plano-cell.own {
                border-color: rgba(0, 113, 227, 0.42);
                box-shadow: inset 0 0 0 1px rgba(0, 113, 227, 0.08);
            }
            .plano-pocari-star {
                background: #ffd60a;
                box-shadow: 0 2px 6px rgba(18, 35, 66, 0.16);
                clip-path: polygon(
                    50% 0%,
                    61% 34%,
                    98% 34%,
                    68% 55%,
                    79% 91%,
                    50% 70%,
                    21% 91%,
                    32% 55%,
                    2% 34%,
                    39% 34%
                );
                height: 18px;
                position: absolute;
                right: 7px;
                top: 7px;
                width: 18px;
                z-index: 3;
            }
            .plano-cell.competitor {
                border-color: rgba(191, 91, 0, 0.38);
                box-shadow: inset 0 0 0 1px rgba(191, 91, 0, 0.08);
            }
            .plano-cell.other {
                border-color: rgba(142, 86, 207, 0.36);
                box-shadow: inset 0 0 0 1px rgba(142, 86, 207, 0.08);
            }
            .plano-cell.empty {
                background: #f7fbff;
                border-color: rgba(24, 45, 80, 0.08);
                color: #a1a1a6;
            }
            .plano-empty-label {
                color: var(--text-tertiary);
                font-size: 12px;
                font-weight: 700;
                position: relative;
                z-index: 1;
            }
            .plano-pack {
                align-items: center;
                display: flex;
                flex-direction: column;
                height: 72%;
                justify-content: center;
                max-width: 74px;
                position: relative;
                width: 70%;
                z-index: 1;
            }
            .plano-pack-cap {
                background: #d2d2d7;
                border: 1px solid rgba(0,0,0,0.14);
                border-radius: 6px 6px 3px 3px;
                height: 8px;
                margin-bottom: -1px;
                width: 28%;
                z-index: 2;
            }
            .plano-pack-body {
                align-items: center;
                background: linear-gradient(180deg, var(--pack-top), var(--pack-main));
                border: 1px solid rgba(0,0,0,0.16);
                border-radius: 12px 12px 10px 10px;
                box-shadow:
                    inset 8px 0 10px rgba(255,255,255,0.22),
                    inset -6px 0 10px rgba(0,0,0,0.10),
                    0 4px 12px rgba(0,0,0,0.08);
                display: flex;
                height: 74%;
                justify-content: center;
                overflow: hidden;
                padding: 5px;
                position: relative;
                width: 58%;
            }
            .plano-pack.can .plano-pack-body {
                border-radius: 7px;
                height: 72%;
                width: 58%;
            }
            .plano-pack.carton .plano-pack-body {
                border-radius: 8px 8px 6px 6px;
                height: 78%;
                width: 62%;
            }
            .plano-pack.carton .plano-pack-cap {
                opacity: 0;
            }
            .plano-pack-label {
                background: rgba(255,255,255,0.88);
                border-radius: 8px;
                color: var(--pack-text);
                display: block;
                font-size: clamp(0.48rem, 0.65vw, 0.64rem);
                font-weight: 900;
                line-height: 1.05;
                max-height: 3.2em;
                overflow: hidden;
                padding: 4px 3px;
                text-transform: uppercase;
                width: 100%;
                word-break: break-word;
            }
            .plano-product-name {
                color: #3a3a3c;
                display: block;
                font-size: clamp(0.46rem, 0.58vw, 0.56rem);
                font-weight: 800;
                line-height: 1;
                max-width: 100%;
                overflow: hidden;
                position: relative;
                text-transform: uppercase;
                text-overflow: ellipsis;
                white-space: nowrap;
                z-index: 1;
            }
            .plano-cell.has-image {
                gap: 6px;
                padding: 8px;
            }
            .plano-product-image {
                display: block;
                height: 72%;
                max-height: 88px;
                max-width: 86%;
                object-fit: contain;
                position: relative;
                width: 86%;
                z-index: 1;
            }
            .plano-pack.orange {
                --pack-top: #ffd078;
                --pack-main: #f97316;
                --pack-text: #b45309;
            }
            .plano-pack.blue {
                --pack-top: #73c7ff;
                --pack-main: #0b74d1;
                --pack-text: #075985;
            }
            .plano-pack.yellow {
                --pack-top: #fff176;
                --pack-main: #facc15;
                --pack-text: #a16207;
            }
            .plano-pack.pink {
                --pack-top: #fecdd3;
                --pack-main: #fb7185;
                --pack-text: #be123c;
            }
            .plano-pack.purple {
                --pack-top: #c4b5fd;
                --pack-main: #6d28d9;
                color: #ffffff;
                --pack-text: #4c1d95;
            }
            .plano-pack.white {
                --pack-top: #ffffff;
                --pack-main: #e2e8f0;
                --pack-text: #1d4ed8;
            }
            .plano-pack.teal {
                --pack-top: #b2f5ea;
                --pack-main: #14b8a6;
                --pack-text: #0f766e;
            }
            @media (max-width: 900px) {
                .plano-grid {
                    min-width: 620px;
                }
                .plano-cell {
                    min-height: 92px;
                }
            }
            .distribution-card {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: 18px;
                padding: 24px 26px;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.05);
                margin-top: 22px;
            }
            .distribution-title {
                display: flex;
                align-items: center;
                gap: 12px;
                color: var(--text);
                font-size: 20px;
                font-weight: 650;
                margin-bottom: 22px;
            }
            .distribution-icon {
                width: 22px;
                height: 22px;
                border: 2px solid #0071e3;
                border-radius: 50%;
                position: relative;
                box-sizing: border-box;
            }
            .distribution-icon:after {
                content: "";
                position: absolute;
                width: 9px;
                height: 9px;
                right: -2px;
                top: -2px;
                background: #ffffff;
                border-left: 2px solid #0071e3;
                border-bottom: 2px solid #0071e3;
            }
            .distribution-row {
                margin: 16px 0 24px 0;
            }
            .distribution-head {
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                gap: 16px;
                color: var(--text);
                font-size: 15px;
                font-weight: 600;
                margin-bottom: 10px;
            }
            .distribution-count {
                color: var(--text-secondary);
                font-size: 13px;
                font-weight: 400;
                margin-top: 8px;
            }
            .distribution-percent {
                font-size: 16px;
                font-weight: 600;
            }
            .distribution-track {
                width: 100%;
                height: 10px;
                border-radius: 999px;
                background: rgba(0, 0, 0, 0.06);
                overflow: hidden;
            }
            .distribution-fill {
                height: 100%;
                border-radius: 999px;
            }
            .compliance-card {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: 18px;
                padding: 24px 26px;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.05);
                margin-top: 22px;
            }
            .compliance-title {
                color: var(--text);
                font-size: 20px;
                font-weight: 650;
                margin-bottom: 18px;
            }
            .compliance-metrics {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 12px;
                margin-bottom: 18px;
            }
            .compliance-metric {
                border: 1px solid rgba(24, 45, 80, 0.10);
                border-radius: 14px;
                padding: 14px;
                background: #f9f9fb;
            }
            .compliance-metric-label {
                color: var(--text-secondary);
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                margin-bottom: 8px;
            }
            .compliance-metric-value {
                color: var(--text);
                font-size: 24px;
                font-weight: 600;
                line-height: 1;
            }
            .compliance-message {
                border-radius: 14px;
                padding: 12px 14px;
                margin: 8px 0;
                font-size: 14px;
                font-weight: 500;
                line-height: 1.45;
            }
            .compliance-message.match {
                background: #f1faf1;
                color: #248a3d;
                border: 1px solid rgba(36, 138, 61, 0.16);
            }
            .compliance-message.mismatch {
                background: #fff7ed;
                color: #bf5b00;
                border: 1px solid rgba(191, 91, 0, 0.16);
            }
            .compliance-message.missing {
                background: #fff2f4;
                color: #d70015;
                border: 1px solid rgba(215, 0, 21, 0.16);
            }
            .compliance-message.unexpected {
                background: #f0f7ff;
                color: #0071e3;
                border: 1px solid rgba(0, 113, 227, 0.14);
            }
            @media (max-width: 900px) {
                .compliance-metrics {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
            }
        </style>
        """
    )


def resolve_product_image_path(image_path):
    if image_path is None:
        return None

    try:
        if pd.isna(image_path):
            return None
    except (TypeError, ValueError):
        pass

    raw_path = str(image_path).strip()
    if not raw_path:
        return None

    expanded_path = os.path.expanduser(raw_path)
    file_name = os.path.basename(expanded_path)

    if os.path.isabs(expanded_path):
        candidate_paths = [
            expanded_path,
            os.path.join(BASE_DIR, "assets", file_name),
            os.path.join(PROJECT_DIR, "assets", file_name),
        ]
    else:
        candidate_paths = [
            os.path.join(PROJECT_DIR, expanded_path),
            os.path.join(BASE_DIR, expanded_path),
            os.path.join(os.getcwd(), expanded_path),
            os.path.join(BASE_DIR, "assets", file_name),
        ]

    for candidate in dict.fromkeys(candidate_paths):
        if candidate and os.path.exists(candidate) and os.path.isfile(candidate):
            return candidate
    return None


@st.cache_data(show_spinner=False)
def product_image_to_src(image_path: str):
    if image_path is None:
        return None

    raw_path = str(image_path).strip()
    if raw_path.lower().startswith(("data:image/", "http://", "https://")):
        return raw_path

    resolved_path = resolve_product_image_path(raw_path)
    if not resolved_path:
        return None

    mime_type = mimetypes.guess_type(resolved_path)[0] or "image/png"
    with open(resolved_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def classify_planogram_item(row: pd.Series) -> str:
    product_id = row.get("product_id")
    product_name = row.get("product_name")
    if pd.isna(product_id) or not str(product_id).strip() or pd.isna(product_name):
        return "empty"

    values = " ".join(
        str(row.get(field, "") or "").lower()
        for field in ["product_type", "brand_name", "brand_group"]
    )

    if any(token in values for token in ["competitor", "pesaing"]):
        return "competitor"
    if any(token in values for token in ["own", "owner", "owned", "pocari", "principal"]):
        return "own"
    return "other"


def build_planogram_cells(df: pd.DataFrame, rows: int, cols: int):
    cells = []
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            cell = df[(df["shelf_row"] == r) & (df["shelf_column"] == c)]
            if cell.empty:
                cells.append(
                    {
                        "row": r,
                        "col": c,
                        "label": f"{r}.{c}",
                        "image": None,
                        "category": "empty",
                    }
                )
                continue

            item = cell.iloc[0]
            label = f"{r}.{c}"
            for field in ["short_name", "product_name"]:
                value = item.get(field)
                if not pd.isna(value) and str(value).strip():
                    label = str(value).strip()
                    break

            expected_count = item.get("expected_count")
            if not pd.isna(expected_count) and int(expected_count or 0) > 1:
                label = f"{label} ({int(expected_count)})"

            cells.append(
                {
                    "row": r,
                    "col": c,
                    "label": str(label),
                    "image": product_image_to_src(item.get("product_image")),
                    "category": classify_planogram_item(item),
                }
            )
    return cells


@st.cache_resource(show_spinner=False)
def load_yolo_model():
    if YOLO is None:
        raise RuntimeError("Ultralytics YOLO is not installed or could not be imported.")
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"YOLO model file was not found: {MODEL_PATH}")
    return YOLO(MODEL_PATH)


def normalize_product_name(value) -> str:
    if value is None or pd.isna(value):
        return ""

    text = str(value).lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    prefix_words = {
        "kompetitor",
        "competitor",
        "customer",
        "owner",
        "own",
        "product",
        "produk",
        "brand",
    }
    text = " ".join(token for token in text.split() if token not in prefix_words)

    if text in PRODUCT_NAME_ALIASES:
        return PRODUCT_NAME_ALIASES[text]

    for alias, canonical in PRODUCT_NAME_ALIASES.items():
        if alias in text:
            return canonical

    stop_words = {"ml", "ltr", "liter", "botol", "bottle", "pet", "pack", "pcs"}
    tokens = [token for token in text.split() if token not in stop_words and not token.isdigit()]
    return " ".join(tokens)


def names_match(expected_name: str, detected_name: str) -> bool:
    expected = normalize_product_name(expected_name)
    detected = normalize_product_name(detected_name)

    if not expected or not detected:
        return False
    if expected == detected:
        return True
    if expected in detected or detected in expected:
        return True

    return SequenceMatcher(None, expected, detected).ratio() >= 0.72


def expected_planogram_positions(df: pd.DataFrame):
    expected = {}
    for _, row in df.iterrows():
        shelf_row = row.get("shelf_row")
        shelf_col = row.get("shelf_column")
        product_name = row.get("short_name")
        if pd.isna(product_name) or not str(product_name).strip():
            product_name = row.get("product_name")

        if pd.isna(shelf_row) or pd.isna(shelf_col) or pd.isna(product_name):
            continue

        position = (int(shelf_row), int(shelf_col))
        expected[position] = {
            "row": int(shelf_row),
            "col": int(shelf_col),
            "product_id": row.get("product_id"),
            "product_name": str(product_name).strip(),
            "canonical_name": normalize_product_name(product_name),
            "expected_count": int(row.get("expected_count") or 1),
            "match_values": [
                row.get("product_id"),
                row.get("short_name"),
                row.get("product_name"),
            ],
        }
    return expected


def detection_matches_expected(expected, detection) -> bool:
    detected_name = detection.get("class_name")
    return any(
        names_match(match_value, detected_name)
        for match_value in expected.get("match_values", [])
        if match_value is not None and not pd.isna(match_value)
    )


def save_uploaded_planogram_image(uploaded_image, planogram_id: str, image_hash: str) -> str:
    os.makedirs(PLANOGRAM_UPLOAD_DIR, exist_ok=True)
    extension = os.path.splitext(uploaded_image.name or "")[1].lower()
    if extension not in {".jpg", ".jpeg", ".png"}:
        extension = ".jpg"

    safe_planogram_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(planogram_id))
    image_path = os.path.join(
        PLANOGRAM_UPLOAD_DIR,
        f"{safe_planogram_id}_{image_hash[:12]}{extension}",
    )

    with open(image_path, "wb") as image_file:
        image_file.write(uploaded_image.getvalue())

    return image_path


def run_yolo_detection(image_path: str, image_hash: str):
    model = load_yolo_model()
    results = model.predict(source=image_path, conf=0.1, imgsz=640, save=False)
    if not results:
        return [], None

    result = results[0]
    detections = []

    with Image.open(image_path) as image:
        image_width, image_height = image.size

    if result.boxes is not None:
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            bbox = [round(float(value), 2) for value in box.xyxy[0].tolist()]
            label = str(model.names.get(class_id, class_id))

            detections.append(
                {
                    "class_id": class_id,
                    "class_name": label,
                    "canonical_name": normalize_product_name(label),
                    "confidence": round(confidence, 4),
                    "bbox": bbox,
                    "center_x": (bbox[0] + bbox[2]) / 2,
                    "center_y": (bbox[1] + bbox[3]) / 2,
                    "image_width": image_width,
                    "image_height": image_height,
                }
            )

    annotated_path = None
    try:
        os.makedirs(PLANOGRAM_OUTPUT_DIR, exist_ok=True)
        annotated_path = os.path.join(PLANOGRAM_OUTPUT_DIR, f"{image_hash[:12]}_detected.jpg")
        plotted = result.plot()
        Image.fromarray(plotted[..., ::-1]).save(annotated_path)
    except Exception:
        annotated_path = None

    return detections, annotated_path


def map_detections_to_shelf_positions(detections, rows: int, cols: int):
    if not detections:
        return []

    sorted_detections = sorted(detections, key=lambda item: item.get("center_y", 0))
    box_heights = [
        abs(item["bbox"][3] - item["bbox"][1])
        for item in sorted_detections
        if isinstance(item.get("bbox"), list) and len(item["bbox"]) >= 4
    ]
    median_box_height = sorted(box_heights)[len(box_heights) // 2] if box_heights else 0
    image_height = sorted_detections[0].get("image_height") or 1
    row_threshold = max(median_box_height * 0.75, image_height / max(rows * 3, 1))

    row_groups = []
    for detection in sorted_detections:
        center_y = float(detection.get("center_y", 0))
        if not row_groups:
            row_groups.append([detection])
            continue

        last_group = row_groups[-1]
        last_center = sum(float(item.get("center_y", 0)) for item in last_group) / len(last_group)
        if abs(center_y - last_center) <= row_threshold:
            last_group.append(detection)
        else:
            row_groups.append([detection])

    while len(row_groups) > rows:
        closest_index = min(
            range(len(row_groups) - 1),
            key=lambda index: abs(
                (
                    sum(float(item.get("center_y", 0)) for item in row_groups[index]) / len(row_groups[index])
                )
                - (
                    sum(float(item.get("center_y", 0)) for item in row_groups[index + 1]) / len(row_groups[index + 1])
                )
            ),
        )
        row_groups[closest_index].extend(row_groups.pop(closest_index + 1))

    mapped = []
    for row_index, row_group in enumerate(row_groups, start=1):
        row_group = sorted(row_group, key=lambda item: item.get("center_x", 0))
        left = min(float(item.get("center_x", 0)) for item in row_group)
        right = max(float(item.get("center_x", 0)) for item in row_group)
        width = max(right - left, 1)

        for group_index, detection in enumerate(row_group):
            if len(row_group) >= cols:
                shelf_col = min(cols, max(1, int(group_index * cols / len(row_group)) + 1))
            else:
                normalized_x = (float(detection.get("center_x", 0)) - left) / width
                shelf_col = min(cols, max(1, int(round(normalized_x * (cols - 1))) + 1))

            mapped.append(
                {
                    **detection,
                    "shelf_row": min(rows, row_index),
                    "shelf_col": shelf_col,
                    "position": (min(rows, row_index), shelf_col),
                }
            )

    mapped.sort(key=lambda item: (item["shelf_row"], item["shelf_col"], -item["confidence"]))
    return mapped


def best_detection_for_position(mapped_detections, position):
    candidates = [item for item in mapped_detections if item["position"] == position]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item["confidence"])


def _compliance_item(
    status,
    row,
    col,
    expected,
    detected="-",
    confidence=None,
    note="",
    detected_col=None,
    expected_count=None,
    detected_count=None,
):
    row_label = f"Row {row}, Column {col}"
    return {
        "status": status,
        "row": row,
        "col": col,
        "position": row_label,
        "expected": expected or "-",
        "detected": detected or "-",
        "confidence": confidence,
        "detected_col": detected_col,
        "expected_count": expected_count,
        "detected_count": detected_count,
        "note": note,
        "message": f"{row_label}: {note}" if note else row_label,
    }


def compare_planogram_to_detections(expected_positions, mapped_detections):
    messages = []
    matched = 0
    misplaced = 0
    mismatched = 0
    missing = 0
    used_detection_ids = set()

    for position, expected in sorted(expected_positions.items()):
        position_detections = [
            item for item in mapped_detections
            if item["position"] == position and id(item) not in used_detection_ids
        ]
        actual = max(position_detections, key=lambda item: item["confidence"]) if position_detections else None
        row_label = f"Row {position[0]}, Column {position[1]}"
        expected_count = max(1, int(expected.get("expected_count") or 1))

        matching_detections = [
            item for item in position_detections
            if detection_matches_expected(expected, item)
        ]

        nearby_matching_detections = []
        if len(matching_detections) < expected_count:
            nearby_matching_detections = [
                item for item in mapped_detections
                if id(item) not in used_detection_ids
                and item["shelf_row"] == position[0]
                and abs(item["shelf_col"] - position[1]) <= 1
                and item["position"] != position
                and detection_matches_expected(expected, item)
            ]

        same_row_matching_detections = []
        if len(matching_detections) + len(nearby_matching_detections) < expected_count:
            same_row_matching_detections = [
                item for item in mapped_detections
                if id(item) not in used_detection_ids
                and item["shelf_row"] == position[0]
                and item["position"] != position
                and item not in nearby_matching_detections
                and detection_matches_expected(expected, item)
            ]

        all_matching_detections = (
            matching_detections
            + nearby_matching_detections
            + same_row_matching_detections
        )

        if len(all_matching_detections) >= expected_count:
            selected_matches = sorted(
                all_matching_detections,
                key=lambda item: (
                    0 if item["position"] == position else 1,
                    abs(item["shelf_col"] - position[1]),
                    -item["confidence"],
                ),
            )[:expected_count]
            used_detection_ids.update(id(item) for item in selected_matches)
            best_match = max(selected_matches, key=lambda item: item["confidence"])
            if best_match["position"] == position:
                matched += 1
                note = f"Matched with {len(selected_matches)} detected facing(s)."
                status = "match"
            elif abs(best_match["shelf_col"] - position[1]) <= 1:
                matched += 1
                note = f"Matched nearby at Column {best_match['shelf_col']}."
                status = "match"
            else:
                misplaced += 1
                note = f"Detected on the same shelf at Column {best_match['shelf_col']}."
                status = "misplaced"

            messages.append(
                _compliance_item(
                    status=status,
                    row=position[0],
                    col=position[1],
                    expected=expected["product_name"],
                    detected=best_match["class_name"],
                    confidence=best_match["confidence"],
                    note=note,
                    detected_col=best_match["shelf_col"],
                    expected_count=expected_count,
                    detected_count=len(selected_matches),
                )
            )
            continue

        if all_matching_detections:
            mismatched += 1
            used_detection_ids.update(id(item) for item in all_matching_detections)
            best_match = max(all_matching_detections, key=lambda item: item["confidence"])
            messages.append(
                _compliance_item(
                    status="mismatch",
                    row=position[0],
                    col=position[1],
                    expected=expected["product_name"],
                    detected=best_match["class_name"],
                    confidence=best_match["confidence"],
                    note=(
                        f"Expected {expected_count} facing(s), "
                        f"detected {len(all_matching_detections)} matching facing(s)."
                    ),
                    detected_col=best_match["shelf_col"],
                    expected_count=expected_count,
                    detected_count=len(all_matching_detections),
                )
            )
        elif actual is None:
            missing += 1
            messages.append(
                _compliance_item(
                    status="missing",
                    row=position[0],
                    col=position[1],
                    expected=expected["product_name"],
                    detected="No product detected",
                    note="No product detected in this shelf position.",
                    expected_count=expected_count,
                    detected_count=0,
                )
            )
        else:
            mismatched += 1
            used_detection_ids.add(id(actual))
            messages.append(
                _compliance_item(
                    status="mismatch",
                    row=position[0],
                    col=position[1],
                    expected=expected["product_name"],
                    detected=actual["class_name"],
                    confidence=actual["confidence"],
                    note="Different product detected in this position.",
                    detected_col=actual["shelf_col"],
                    expected_count=expected_count,
                    detected_count=1,
                )
            )

    unexpected_positions = []
    for detection in mapped_detections:
        if id(detection) not in used_detection_ids and detection["position"] not in expected_positions:
            unexpected_positions.append(detection)

    for detection in unexpected_positions:
        messages.append(
            _compliance_item(
                status="unexpected",
                row=detection["shelf_row"],
                col=detection["shelf_col"],
                expected="Not in planogram",
                detected=detection["class_name"],
                confidence=detection["confidence"],
                note="Extra product detected outside expected shelf positions.",
                detected_col=detection["shelf_col"],
                detected_count=1,
            )
        )

    total_expected = len(expected_positions)
    score = round(((matched + misplaced) / total_expected) * 100, 2) if total_expected else 0

    return {
        "score": score,
        "matched": matched,
        "misplaced": misplaced,
        "mismatched": mismatched,
        "missing": missing,
        "unexpected": len(unexpected_positions),
        "total_expected": total_expected,
        "total_detected": len(mapped_detections),
        "messages": messages,
    }


def _readable_product_name(value) -> str:
    text = str(value or "-").strip()
    if not text or text == "-":
        return "-"
    if text.lower() == "no product detected":
        return "Tidak ada produk terbaca"
    if text.lower() == "not in planogram":
        return "Tidak ada di planogram"

    text = text.replace("_", " ")
    words = []
    for word in text.split():
        if word.lower() == "kompetitor":
            words.append("Kompetitor")
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


def _readable_position(row, col) -> str:
    return f"Baris {row}, Kolom {col}"


def _readable_compliance_note(item: dict, expected: str, detected: str, detected_col_label: str) -> str:
    status = item.get("status")
    if status == "match":
        return f"Produk sudah sesuai. Di slot ini seharusnya {expected}, dan kamera juga membaca {detected}."
    if status == "misplaced":
        return f"Produknya benar, tetapi posisinya bergeser. Kamera membaca produk ini di {detected_col_label}."
    if status == "missing":
        return f"Produk {expected} seharusnya ada di slot ini, tetapi tidak terlihat jelas di foto."
    if status == "unexpected":
        return f"Kamera menemukan {detected}, tetapi produk ini tidak tercatat untuk slot planogram ini."
    return f"Di slot ini seharusnya {expected}, tetapi kamera membaca {detected}."


def _render_compliance_cards(items):
    status_meta = {
        "match": {"label": "Sesuai", "icon": "OK", "tone": "match"},
        "misplaced": {"label": "Posisi bergeser", "icon": "PINDAH", "tone": "misplaced"},
        "mismatch": {"label": "Produk berbeda", "icon": "BEDA", "tone": "mismatch"},
        "missing": {"label": "Produk kosong", "icon": "KOSONG", "tone": "missing"},
        "unexpected": {"label": "Produk tambahan", "icon": "BARU", "tone": "unexpected"},
    }

    cards = []
    for item in items:
        meta = status_meta.get(item.get("status"), status_meta["mismatch"])
        confidence = item.get("confidence")
        confidence_pct = int(round(float(confidence) * 100)) if confidence is not None else 0
        confidence_label = f"{confidence_pct}%" if confidence is not None else "-"
        detected_col = item.get("detected_col")
        detected_col_label = f"Kolom {detected_col}" if detected_col else "-"
        expected_count = item.get("expected_count")
        detected_count = item.get("detected_count")
        facing_label = "-"
        if expected_count is not None or detected_count is not None:
            facing_label = f"{detected_count or 0} dari {expected_count or '-'}"

        expected_label = _readable_product_name(item.get("expected", "-"))
        detected_label = _readable_product_name(item.get("detected", "-"))
        position_label = _readable_position(item.get("row", "-"), item.get("col", "-"))
        simple_note = _readable_compliance_note(item, expected_label, detected_label, detected_col_label)

        cards.append(
            f"""
            <div class="compliance-result-card {meta['tone']}">
                <div class="compliance-result-top">
                    <div class="compliance-status-mark">{escape(meta['icon'])}</div>
                    <div class="compliance-result-head">
                        <div class="compliance-result-position">{escape(position_label)}</div>
                        <div class="compliance-result-note">{escape(simple_note)}</div>
                    </div>
                    <div class="compliance-status-badge">{escape(meta['label'])}</div>
                </div>
                <div class="compliance-compare-grid">
                    <div class="compliance-compare-cell">
                        <span>Seharusnya</span>
                        <strong>{escape(expected_label)}</strong>
                    </div>
                    <div class="compliance-compare-cell">
                        <span>Terbaca kamera</span>
                        <strong>{escape(detected_label)}</strong>
                    </div>
                    <div class="compliance-compare-cell compact">
                        <span>Posisi terbaca</span>
                        <strong>{escape(detected_col_label)}</strong>
                    </div>
                    <div class="compliance-compare-cell compact">
                        <span>Jumlah facing</span>
                        <strong>{escape(facing_label)}</strong>
                    </div>
                </div>
                <div class="compliance-confidence">
                    <div class="compliance-confidence-copy">
                        <span>Keyakinan AI</span>
                        <strong>{escape(confidence_label)}</strong>
                    </div>
                    <div class="compliance-confidence-track">
                        <span style="width: {confidence_pct}%;"></span>
                    </div>
                </div>
            </div>
            """
        )

    markdown_html(
        f"""
        <style>
            .compliance-result-list {{
                display: grid;
                gap: 0.78rem;
                margin-top: 1rem;
            }}
            .compliance-result-card {{
                --status-color: #0071e3;
                --status-bg: #f0f7ff;
                --status-bg-strong: #e1f0ff;
                --status-border: rgba(0, 113, 227, 0.24);
                background:
                    linear-gradient(135deg, var(--status-bg) 0%, rgba(255, 255, 255, 0.96) 46%, rgba(255, 255, 255, 0.94) 100%);
                border: 1px solid var(--status-border);
                border-left: 6px solid var(--status-color);
                border-radius: 18px;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.05);
                padding: 1rem;
                position: relative;
            }}
            .compliance-result-card.match {{
                --status-color: #248a3d;
                --status-bg: #f0f9f2;
                --status-bg-strong: #dff3e4;
                --status-border: rgba(36, 138, 61, 0.24);
            }}
            .compliance-result-card.misplaced {{
                --status-color: #0071e3;
                --status-bg: #f0f7ff;
                --status-bg-strong: #e1f0ff;
                --status-border: rgba(0, 113, 227, 0.24);
            }}
            .compliance-result-card.mismatch {{
                --status-color: #bf5b00;
                --status-bg: #fff7ed;
                --status-bg-strong: #ffe8cc;
                --status-border: rgba(191, 91, 0, 0.26);
            }}
            .compliance-result-card.missing {{
                --status-color: #d70015;
                --status-bg: #fff2f4;
                --status-bg-strong: #ffdfe5;
                --status-border: rgba(215, 0, 21, 0.24);
            }}
            .compliance-result-card.unexpected {{
                --status-color: #8e56cf;
                --status-bg: #f8f1ff;
                --status-bg-strong: #eee0ff;
                --status-border: rgba(142, 86, 207, 0.24);
            }}
            .compliance-result-top {{
                align-items: flex-start;
                display: flex;
                gap: 0.72rem;
            }}
            .compliance-status-mark {{
                align-items: center;
                background: var(--status-bg-strong);
                border: 1px solid var(--status-border);
                border-radius: 14px;
                color: var(--status-color);
                display: flex;
                flex: 0 0 54px;
                font-size: 0.58rem;
                font-weight: 800;
                height: 42px;
                justify-content: center;
                line-height: 1;
                text-align: center;
            }}
            .compliance-result-head {{
                flex: 1;
                min-width: 0;
            }}
            .compliance-result-position {{
                color: var(--text);
                font-size: 1rem;
                font-weight: 650;
                line-height: 1.2;
            }}
            .compliance-result-note {{
                color: var(--text-secondary);
                font-size: 0.84rem;
                line-height: 1.5;
                margin-top: 0.24rem;
            }}
            .compliance-status-badge {{
                background: var(--status-bg-strong);
                border: 1px solid var(--status-border);
                border-radius: 999px;
                color: var(--status-color);
                flex: 0 0 auto;
                font-size: 0.72rem;
                font-weight: 590;
                padding: 0.42rem 0.72rem;
            }}
            .compliance-compare-grid {{
                display: grid;
                gap: 0.55rem;
                grid-template-columns: 1.35fr 1.35fr 0.8fr 0.7fr;
                margin-top: 0.9rem;
            }}
            .compliance-compare-cell {{
                background: rgba(255, 255, 255, 0.76);
                border: 1px solid var(--status-border);
                border-radius: 14px;
                min-width: 0;
                padding: 0.62rem 0.68rem;
            }}
            .compliance-compare-cell span,
            .compliance-confidence-copy span {{
                color: var(--text-tertiary);
                display: block;
                font-size: 0.7rem;
                font-weight: 590;
            }}
            .compliance-compare-cell strong {{
                color: var(--text);
                display: block;
                font-size: 0.88rem;
                font-weight: 650;
                line-height: 1.25;
                margin-top: 0.25rem;
                overflow-wrap: anywhere;
            }}
            .compliance-confidence {{
                align-items: center;
                display: grid;
                gap: 0.7rem;
                grid-template-columns: 110px 1fr;
                margin-top: 0.75rem;
            }}
            .compliance-confidence-copy strong {{
                color: var(--text);
                display: block;
                font-size: 0.86rem;
                font-weight: 650;
                margin-top: 0.18rem;
            }}
            .compliance-confidence-track {{
                background: rgba(0, 0, 0, 0.06);
                border-radius: 999px;
                height: 9px;
                overflow: hidden;
            }}
            .compliance-confidence-track span {{
                background: var(--status-color);
                border-radius: inherit;
                display: block;
                height: 100%;
            }}
            @media (max-width: 900px) {{
                .compliance-result-top {{
                    align-items: flex-start;
                    flex-wrap: wrap;
                }}
                .compliance-compare-grid {{
                    grid-template-columns: 1fr 1fr;
                }}
                .compliance-confidence {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
        <div class="compliance-result-list">
            {''.join(cards)}
        </div>
        """
    )


def render_compliance_summary(comparison):
    section_header("Hasil pengecekan rak", "Kartu di bawah menjelaskan posisi mana yang sudah sesuai dan mana yang perlu diperbaiki.")
    metric_cols = st.columns(5)
    with metric_cols[0]:
        kpi_card("Nilai Cocok", f"{comparison['score']}%", tone="blue", icon="SC")
    with metric_cols[1]:
        kpi_card("Sesuai", comparison["matched"], tone="green", icon="OK")
    with metric_cols[2]:
        kpi_card("Bergeser", comparison["misplaced"], tone="purple", icon="MV")
    with metric_cols[3]:
        kpi_card("Produk Beda", comparison["mismatched"], tone="orange", icon="MM")
    with metric_cols[4]:
        kpi_card("Kosong", comparison["missing"], tone="orange", icon="MS")
    st.caption(
        f"AI membandingkan {comparison['total_detected']} produk yang terbaca di foto dengan "
        f"{comparison['total_expected']} posisi yang seharusnya ada di planogram. "
        f"Produk tambahan: {comparison['unexpected']}."
    )

    _render_compliance_cards(comparison["messages"])


def render_distribution_summary(cells):
    occupied_cells = [cell for cell in cells if cell["category"] != "empty"]
    total = len(occupied_cells)
    groups = [
        ("Pocari Products", "own", "#0071e3"),
        ("Competitor Products", "competitor", "#bf5b00"),
        ("Other Brands", "other", "#6e6e73"),
    ]

    rows = []
    for label, key, color in groups:
        count = len([cell for cell in occupied_cells if cell["category"] == key])
        percent = round((count / total) * 100) if total else 0
        rows.append(
            f"""
            <div class="distribution-row">
                <div class="distribution-head">
                    <div>
                        <div>{escape(label)}</div>
                        <div class="distribution-count">{count} products</div>
                    </div>
                    <div class="distribution-percent" style="color: {color};">{percent}%</div>
                </div>
                <div class="distribution-track">
                    <div class="distribution-fill" style="width: {percent}%; background: {color};"></div>
                </div>
            </div>
            """
        )

    markdown_html(
        f"""
        <div class="distribution-card">
            <div class="distribution-title">
                <span class="distribution-icon"></span>
                Shelf product distribution
            </div>
            {''.join(rows)}
        </div>
        """
    )


def render_planogram_grid(planogram_id: str):
    df = load_planogram_items(planogram_id)

    if df.empty:
        st.warning(f"Tidak ada layout item untuk planogram {planogram_id}")
        return

    max_row = int(df["shelf_row"].max())
    max_col = int(df["shelf_column"].max())
    cells = build_planogram_cells(df, max_row, max_col)
    filled_count = len([cell for cell in cells if cell["category"] != "empty"])
    comparison = None

    left, right = st.columns([0.95, 1.45], gap="large")

    with left:
        st.subheader("Planogram Photo")
        uploaded_image = st.file_uploader(
            "Upload shelf image",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
            key=f"planogram_image_{planogram_id}",
        )
        if uploaded_image:
            image_bytes = uploaded_image.getvalue()
            image_hash = hashlib.sha256(image_bytes).hexdigest()
            inference_key = f"planogram_compliance_{planogram_id}_{image_hash}"

            if inference_key not in st.session_state:
                with st.spinner("Running shelf detection and checking compliance..."):
                    try:
                        image_path = save_uploaded_planogram_image(
                            uploaded_image,
                            planogram_id,
                            image_hash,
                        )
                        detections, annotated_path = run_yolo_detection(image_path, image_hash)
                        mapped_detections = map_detections_to_shelf_positions(
                            detections,
                            max_row,
                            max_col,
                        )
                        expected_positions = expected_planogram_positions(df)
                        comparison = compare_planogram_to_detections(
                            expected_positions,
                            mapped_detections,
                        )
                        st.session_state[inference_key] = {
                            "image_path": image_path,
                            "annotated_path": annotated_path,
                            "detections": detections,
                            "mapped_detections": mapped_detections,
                            "comparison": comparison,
                        }
                    except Exception as e:
                        st.session_state[inference_key] = {
                            "error": str(e),
                            "comparison": None,
                        }

            inference_result = st.session_state.get(inference_key, {})
            comparison = inference_result.get("comparison")
            if inference_result.get("error"):
                st.error(f"Failed running shelf compliance check: {inference_result['error']}")
                st.image(uploaded_image, use_column_width=True)
            elif inference_result.get("annotated_path") and os.path.exists(inference_result["annotated_path"]):
                st.image(inference_result["annotated_path"], use_column_width=True)
            else:
                st.image(uploaded_image, use_column_width=True)
        else:
            st.info("Upload shelf photo: JPG, JPEG, or PNG.")

    with right:
        st.subheader("Planogram Grid")
        st.caption(f"{planogram_id} - {max_row} rows - {max_col} columns - {filled_count} filled cells")
        grid_items = "".join(_render_planogram_cell(cell) for cell in cells)
        markdown_html(
            f"""
            <div class="plano-grid-wrap">
                <div class="plano-grid" style="grid-template-columns: repeat({max_col}, minmax(78px, 1fr));">
                    {grid_items}
                </div>
            </div>
            """
        )

    render_distribution_summary(cells)
    if comparison:
        render_compliance_summary(comparison)

def split_frame(input_df: pd.DataFrame, rows: int):
    return [
        input_df.loc[i: i + rows - 1, :].reset_index(drop=True)
        for i in range(0, len(input_df), rows)
    ]


@st.cache_data(show_spinner=False, ttl=60)
def fetch_apps():
    return fetch_all("""
        SELECT app_id, app_name
        FROM master_apps
        WHERE deleted_at IS NULL
        ORDER BY app_name
    """)


def read_planogram():
    render_header("Manajemen Rak Swalayan", "Kelola master planogram, detail layout, dan evaluasi kepatuhan shelf photo.", chip="Planogram Monitor")
    apply_planogram_styles()

    try:
        dataset = load_planogram_list()
    except Exception as e:
        st.error(f"Failed to load planogram data from database: {e}")
        return

    if "show_add_planogram_form" not in st.session_state:
        st.session_state.show_add_planogram_form = False

    if "show_add_layout_form" not in st.session_state:
        st.session_state.show_add_layout_form = False

    if "show_delete_planogram_form" not in st.session_state:
        st.session_state.show_delete_planogram_form = False

    layout_ready_count = 0
    app_count = 0
    latest_update = "-"
    if not dataset.empty:
        if "content" in dataset.columns:
            layout_ready_count = int(dataset["content"].fillna("").astype(str).str.strip().ne("").sum())
        if "app_id" in dataset.columns:
            app_count = int(dataset["app_id"].dropna().astype(str).nunique())
        if "updated_at" in dataset.columns:
            updated_values = dataset["updated_at"].dropna()
            if not updated_values.empty:
                latest_update = str(updated_values.max())[:19]

    stats = st.columns(4)
    with stats[0]:
        kpi_card("Planograms", len(dataset), "Active shelf layouts", tone="blue", icon="PG")
    with stats[1]:
        kpi_card("Layout Ready", layout_ready_count, "Records with layout content", tone="green", icon="LY")
    with stats[2]:
        kpi_card("Applications", app_count, "Linked app contexts", tone="purple", icon="AP")
    with stats[3]:
        kpi_card("Latest Update", latest_update, "Most recent planogram change", tone="orange", icon="UP")

    with st.container(border=True):
        section_header("Browse planograms", "Search layouts, maintain planogram records, or preview a shelf grid.")
        search = st.text_input("Search", placeholder="Search planogram name, app_id, or planogram_id...")

        sort_row = columns([2.2, 1.8], vertical_alignment="bottom")

        with sort_row[0]:
            sort = st.radio("Sort Data", ["No", "Yes"], horizontal=True)

        with sort_row[1]:
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            if btn_col1.button("Add", use_container_width=True, type="primary"):
                st.session_state.show_add_planogram_form = True
                st.session_state.show_add_layout_form = False
                st.session_state.show_delete_planogram_form = False
            if btn_col2.button("Layout", use_container_width=True):
                st.session_state.show_add_layout_form = True
                st.session_state.show_add_planogram_form = False
                st.session_state.show_delete_planogram_form = False
            if btn_col3.button("Delete", use_container_width=True):
                st.session_state.show_delete_planogram_form = True
                st.session_state.show_add_planogram_form = False
                st.session_state.show_add_layout_form = False

    q = (search or "").strip().lower()
    if q:
        dataset = dataset[
            dataset.astype(str)
            .apply(lambda col: col.str.lower().str.contains(q, na=False))
            .any(axis=1)
        ]

    if st.session_state.show_add_planogram_form:
        with st.container(border=True):
            section_header("Add planogram", "Create a planogram shell before adding detailed shelf layout data.")
        try:
            apps = fetch_apps()
        except Exception as e:
            st.error(f"Failed loading application options: {e}")
            return

        app_labels = ["- Select App -"] + [
            f"{row['app_id']} - {row['app_name']}" for row in apps
        ]

        with st.form("add_planogram_form", clear_on_submit=True):
            selected_app = st.selectbox("Application", app_labels)
            planogram_id = st.text_input("Planogram ID", placeholder="PL001")
            planogram_name = st.text_input("Planogram Name", placeholder="Shelf layout A")
            content = st.text_area("Content", placeholder='{"rows": []}', height=140)
            form_col1, form_col2 = st.columns(2)
            save_planogram = form_col1.form_submit_button("Save Planogram", use_container_width=True)
            cancel_planogram = form_col2.form_submit_button("Cancel", use_container_width=True)

            if save_planogram:
                if selected_app == "- Select App -" or not planogram_id.strip() or not planogram_name.strip():
                    st.warning("Application, Planogram ID, and Planogram Name are required.")
                else:
                    app_id = selected_app.split(" - ", 1)[0]
                    try:
                        execute_query(
                            """
                            INSERT INTO master_planograms
                            (planogram_id, app_id, name, content, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, NOW(), NOW())
                            """,
                            (
                                planogram_id.strip(),
                                app_id,
                                planogram_name.strip(),
                                content.strip() or None,
                            ),
                        )
                        st.cache_data.clear()
                        st.session_state.show_add_planogram_form = False
                        st.success("Planogram created successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed creating planogram: {e}")

            if cancel_planogram:
                st.session_state.show_add_planogram_form = False
                st.rerun()

    if st.session_state.show_add_layout_form:
        with st.container(border=True):
            section_header("Add layout detail", "Attach JSON layout detail to an existing planogram.")
            if dataset.empty:
                st.info("No planogram available. Create a planogram first.")
            else:
                planogram_labels = [
                    f"{row['planogram_id']} - {row['planogram_name']}" for _, row in dataset.iterrows()
                ]
                with st.form("add_layout_form", clear_on_submit=True):
                    selected_planogram = st.selectbox("Planogram", planogram_labels)
                    layout_content = st.text_area("Layout Detail", placeholder='{"layout": []}', height=180)
                    form_col1, form_col2 = st.columns(2)
                    save_layout = form_col1.form_submit_button("Save Layout Detail", use_container_width=True)
                    cancel_layout = form_col2.form_submit_button("Cancel", use_container_width=True)

                    if save_layout:
                        if not layout_content.strip():
                            st.warning("Layout detail content is required.")
                        else:
                            current_planogram_id = selected_planogram.split(" - ", 1)[0]
                            try:
                                execute_query(
                                    """
                                    UPDATE master_planograms
                                    SET content = %s,
                                        updated_at = NOW()
                                    WHERE planogram_id = %s
                                      AND deleted_at IS NULL
                                    """,
                                    (
                                        layout_content.strip(),
                                        current_planogram_id,
                                    ),
                                )
                                st.cache_data.clear()
                                st.session_state.show_add_layout_form = False
                                st.success("Layout detail saved successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed saving layout detail: {e}")

                    if cancel_layout:
                        st.session_state.show_add_layout_form = False
                        st.rerun()

    if st.session_state.show_delete_planogram_form:
        with st.container(border=True):
            section_header("Delete planogram", "Soft-delete the selected planogram from master data lists.")
            warning_card("Perhatian", "Planogram yang dihapus akan disembunyikan dari daftar master data dan pilihan analisis.")
            if dataset.empty:
                st.info("No planogram data available to delete.")
            else:
                delete_options = [
                    f"{row['planogram_id']} - {row['planogram_name']}" for _, row in dataset.iterrows()
                ]
                selected_planogram = st.selectbox("Select Planogram to Delete", delete_options, key="delete_planogram_select")

                with st.form("delete_planogram_form"):
                    confirm_delete = st.checkbox("I understand this planogram will be hidden from master data lists.")
                    delete_col1, delete_col2 = st.columns(2)
                    delete_submit = delete_col1.form_submit_button("Delete Planogram", use_container_width=True)
                    delete_cancel = delete_col2.form_submit_button("Cancel", use_container_width=True)

                    if delete_submit:
                        if not confirm_delete:
                            st.warning("Please confirm before deleting.")
                        else:
                            planogram_id_to_delete = selected_planogram.split(" - ", 1)[0]
                            try:
                                execute_query(
                                    """
                                    UPDATE master_planograms
                                    SET deleted_at = NOW(),
                                        updated_at = NOW()
                                    WHERE planogram_id = %s
                                      AND deleted_at IS NULL
                                    """,
                                    (planogram_id_to_delete,),
                                )
                                st.cache_data.clear()
                                st.session_state.show_delete_planogram_form = False
                                st.success("Planogram deleted successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed deleting planogram: {e}")

                    if delete_cancel:
                        st.session_state.show_delete_planogram_form = False
                        st.rerun()

    if sort == "Yes" and not dataset.empty:
        sort_col = st.selectbox("Sort By", dataset.columns.tolist())
        sort_dir = st.radio("Direction", ["Asc", "Desc"], horizontal=True)
        dataset = dataset.sort_values(
            by=sort_col,
            ascending=(sort_dir == "Asc"),
            ignore_index=True
        )

    if len(dataset) == 0:
        st.info("No matching planogram found.")
        return

    paginate_dataframe(dataset, "planograms", "planograms")

    # Preview grid planogram
    if not dataset.empty:
        section_header("Planogram preview and compliance", "Select a planogram to inspect the grid and optionally upload a shelf photo for compliance checking.")
        preview = dataset.head(3)
        for _, row in preview.iterrows():
            list_item_card(
                str(row.get("planogram_name", row.get("planogram_id", "Planogram"))),
                f"{row.get('app_id', '-')} - {row.get('planogram_id', '-')}",
                badge="Layout Ready" if row.get("content") else "Need Layout",
                badge_tone="success" if row.get("content") else "warning",
                thumb="PL",
            )
        selected_planogram_id = st.selectbox(
            "Preview Grid Planogram",
            dataset["planogram_id"].dropna().astype(str).unique().tolist()
        )
        render_planogram_grid(selected_planogram_id)
