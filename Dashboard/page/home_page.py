import os
import uuid
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

import streamlit as st

from components.ui import markdown_html, warning_card
from utils.api_handler import analyze_display_api
from utils.db import save_analysis_result


APP_OPTIONS = [
    "Choose an option",
    "APP001",
    "APP002",
    "APP003",
]

PLANOGRAM_OPTIONS = [
    "None",
    "PG001",
    "PG002",
    "PG003",
]


def _get_last_result_summary() -> tuple[str, str]:
    result = st.session_state.get("result") or {}
    inner = result.get("result", result) if isinstance(result, dict) else {}
    detections = inner.get("detections") or []
    detection_count = str(len(detections)) if isinstance(detections, list) else "0"
    status = str(result.get("status", "idle")).upper() if isinstance(result, dict) else "IDLE"
    return detection_count, status


def _current_run_timestamp() -> tuple[str, str]:
    run_dt = datetime.now(ZoneInfo("Asia/Jakarta"))
    iso_value = run_dt.isoformat(timespec="seconds")
    display_value = run_dt.strftime("%d %B %Y, %H:%M:%S WIB")
    return iso_value, display_value


def _save_uploaded_file(file) -> str:
    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)

    filename = f"{uuid.uuid4()}_{file.name}"
    save_path = os.path.join(upload_folder, filename)

    with open(save_path, "wb") as image_file:
        image_file.write(file.getbuffer())

    st.session_state.uploaded_path = save_path
    st.session_state.uploaded_filename = filename
    st.session_state.original_filename = file.name
    st.session_state.uploaded_mime_type = file.type
    st.session_state.uploaded_size = file.size
    return save_path


def _record_history(result: dict, request_id: str, run_at_display: str, selected_app: str, image_path: str):
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []

    inner = result.get("result", result) if isinstance(result, dict) else {}
    detections = inner.get("detections") or []
    history_entry = {
        "request_id": request_id,
        "run_at_display": run_at_display,
        "status": str(result.get("status", "unknown")).upper() if isinstance(result, dict) else "UNKNOWN",
        "app_id": selected_app if selected_app != "Choose an option" else "-",
        "detections": len(detections) if isinstance(detections, list) else 0,
        "image_name": os.path.basename(image_path),
    }

    history = [entry for entry in st.session_state.analysis_history if entry.get("request_id") != request_id]
    history.insert(0, history_entry)
    st.session_state.analysis_history = history[:8]


def _render_history_cards(history: list[dict]):
    if not history:
        st.info("Belum ada riwayat analisis pada sesi ini. Setelah menjalankan inferensi, hasilnya akan muncul di sini.")
        return

    for entry in history[:6]:
        with st.container(border=True):
            st.write(f"**{entry.get('image_name', '-')}**")
            st.caption(f"App ID: {entry.get('app_id', '-')} | Run: {entry.get('run_at_display', '-')}")
            cols = st.columns(3)
            cols[0].metric("Detections", entry.get("detections", 0))
            cols[1].metric("Status", entry.get("status", "-"))
            cols[2].metric("App", entry.get("app_id", "-"))


def _clear_workspace():
    for key in [
        "uploaded_path",
        "uploaded_filename",
        "original_filename",
        "uploaded_mime_type",
        "uploaded_size",
        "request_id",
        "result",
        "output_path",
        "_last_inputs",
        "manual_uploaded_image",
        "analysis_history",
    ]:
        st.session_state.pop(key, None)


def _render_home_styles():
    markdown_html(
        """
        <style>
        [data-testid="stMain"] .block-container {
            max-width: 1280px;
            padding-top: 1.85rem;
        }

        [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.92) !important;
            border: 1px solid rgba(0, 0, 0, 0.06) !important;
            border-radius: 18px !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.05) !important;
        }

        [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
            gap: 0.82rem;
        }

        .home-shell {
            margin: 0 auto;
            max-width: 1280px;
        }

        .home-header {
            align-items: flex-start;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 18px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.05);
            display: flex;
            gap: 1.5rem;
            justify-content: space-between;
            margin-bottom: 1.2rem;
            overflow: hidden;
            padding: 1.55rem 1.7rem;
            position: relative;
        }

        .home-header:before {
            content: "";
            display: none;
        }

        .home-title {
            color: #1d1d1f;
            font-size: clamp(2rem, 2.6vw, 2.55rem);
            font-weight: 700;
            line-height: 1.08;
            margin: 0 0 0.62rem;
        }

        .home-subtitle {
            color: #6e6e73;
            font-size: 1rem;
            line-height: 1.52;
            margin: 0;
            max-width: 780px;
        }

        .home-chip {
            background: #f0f7ff;
            border: 1px solid rgba(0, 113, 227, 0.14);
            border-radius: 999px;
            color: #0071e3;
            flex: 0 0 auto;
            font-size: 0.78rem;
            font-weight: 590;
            margin-top: 0.12rem;
            padding: 0.46rem 0.74rem;
        }

        .monitor-hero {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 18px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.05);
            color: #1d1d1f;
            margin-bottom: 1.2rem;
            overflow: hidden;
            padding: 1.55rem 1.65rem 1.35rem;
            position: relative;
        }

        .monitor-hero-top {
            align-items: flex-start;
            display: flex;
            gap: 1rem;
            justify-content: space-between;
            position: relative;
            z-index: 1;
        }

        .monitor-kicker {
            color: #6e6e73;
            font-size: 0.76rem;
            font-weight: 590;
            margin-bottom: 0.38rem;
            text-transform: uppercase;
        }

        .monitor-title {
            color: #1d1d1f;
            font-size: 1.55rem;
            font-weight: 700;
            line-height: 1.15;
            margin: 0 0 0.52rem;
        }

        .monitor-copy {
            color: #6e6e73;
            font-size: 0.94rem;
            line-height: 1.52;
            margin: 0;
            max-width: 720px;
        }

        .monitor-icon {
            align-items: center;
            background: #f0f7ff;
            border: 1px solid rgba(0, 113, 227, 0.14);
            border-radius: 14px;
            color: #0071e3;
            display: flex;
            flex: 0 0 48px;
            font-size: 0.92rem;
            font-weight: 700;
            height: 48px;
            justify-content: center;
            position: relative;
            width: 48px;
            z-index: 1;
        }

        .monitor-stats {
            display: grid;
            gap: 0.85rem;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin-top: 1.18rem;
            position: relative;
            z-index: 1;
        }

        .monitor-stat {
            background: #f9f9fb;
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 14px;
            padding: 0.9rem 0.95rem;
        }

        .monitor-stat:nth-child(2) {
            background: #f9f9fb;
            border-color: rgba(0, 0, 0, 0.06);
        }

        .monitor-stat:nth-child(3) {
            background: #f9f9fb;
            border-color: rgba(0, 0, 0, 0.06);
        }

        .monitor-stat-value {
            color: #1d1d1f;
            font-size: 1.32rem;
            font-weight: 700;
            line-height: 1;
            overflow-wrap: anywhere;
        }

        .monitor-stat-label {
            color: #6e6e73;
            font-size: 0.75rem;
            font-weight: 500;
            line-height: 1.35;
            margin-top: 0.48rem;
        }

        .home-panel-head {
            align-items: flex-start;
            display: flex;
            gap: 0.75rem;
        }

        .home-panel-step {
            align-items: center;
            background: #f0f7ff;
            border: 1px solid rgba(0, 113, 227, 0.14);
            border-radius: 12px;
            color: #0071e3;
            display: flex;
            flex: 0 0 34px;
            font-size: 0.82rem;
            font-weight: 700;
            height: 34px;
            justify-content: center;
            width: 34px;
        }

        .home-panel-title {
            color: #1d1d1f;
            font-size: 1.04rem;
            font-weight: 650;
            line-height: 1.25;
            margin: 0 0 0.32rem;
        }

        .home-panel-copy {
            color: #6e6e73;
            font-size: 0.9rem;
            line-height: 1.45;
            margin: 0 0 0.95rem;
        }

        .upload-preview {
            background: #f9f9fb;
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 14px;
            margin-top: 1rem;
            padding: 0.84rem 0.9rem;
        }

        .upload-meta {
            color: #6e6e73;
            font-size: 0.81rem;
            line-height: 1.45;
            margin: 0;
        }

        .home-run-spacer {
            height: 0.15rem;
        }

        div[data-testid="stButton"] > button[kind="primary"] {
            background: #0071e3 !important;
            border: 1px solid #0071e3 !important;
            border-radius: 999px !important;
            box-shadow: none !important;
            color: #ffffff !important;
            min-height: 48px;
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background: #0077ed !important;
            border-color: #0077ed !important;
            box-shadow: none !important;
        }

        @media (max-width: 760px) {
            .home-header {
                display: flex;
                flex-direction: column;
            }

            .home-chip {
                display: inline-flex;
                margin-top: 0;
            }

            .monitor-stats {
                grid-template-columns: 1fr;
            }

            .monitor-hero {
                padding: 1.25rem;
            }
        }
        </style>
        """
    )


def _render_home_header():
    markdown_html(
        """
        <div class="home-shell">
            <div class="home-header">
                <div>
                    <h1 class="home-title">Dashboard Monitoring</h1>
                    <p class="home-subtitle">Pantau kepatuhan planogram dan jalankan analisis AI Vision untuk foto rak swalayan.</p>
                </div>
                <div class="home-chip">AI Vision Workspace</div>
            </div>
        </div>
        """
    )


def _render_monitor_hero(detection_count: str, history_count: int, run_status: str):
    markdown_html(
        f"""
        <div class="home-shell">
            <section class="monitor-hero">
                <div class="monitor-hero-top">
                    <div>
                        <div class="monitor-kicker">Dashboard monitoring</div>
                        <h2 class="monitor-title">Cabang Pocari - Regional Jakarta</h2>
                        <p class="monitor-copy">Upload foto rak, pilih konteks aplikasi, lalu jalankan deteksi untuk menghasilkan output visual, metadata run, dan tabel facing.</p>
                    </div>
                    <div class="monitor-icon">AI</div>
                </div>
                <div class="monitor-stats">
                    <div class="monitor-stat">
                        <div class="monitor-stat-value">{escape(str(detection_count))}</div>
                        <div class="monitor-stat-label">Deteksi terakhir</div>
                    </div>
                    <div class="monitor-stat">
                        <div class="monitor-stat-value">{escape(str(history_count))}</div>
                        <div class="monitor-stat-label">Riwayat sesi</div>
                    </div>
                    <div class="monitor-stat">
                        <div class="monitor-stat-value">{escape(str(run_status))}</div>
                        <div class="monitor-stat-label">Status terakhir</div>
                    </div>
                </div>
            </section>
        </div>
        """
    )


def render_home_page():
    detection_count, run_status = _get_last_result_summary()
    history = st.session_state.get("analysis_history", [])
    history_count = len(history)

    _render_home_styles()
    _render_monitor_hero(detection_count, history_count, run_status)

    left_col, right_col = st.columns([1.15, 0.95], gap="large")
    uploaded_path = st.session_state.get("uploaded_path")

    with left_col:
        with st.container(border=True):
            markdown_html(
                """
                <div class="home-panel-head">
                    <div class="home-panel-step">1</div>
                    <div>
                        <div class="home-panel-title">Upload foto rak</div>
                        <div class="home-panel-copy">Ambil atau unggah foto rak yang jelas untuk dianalisis oleh AI Vision.</div>
                    </div>
                </div>
                """
            )

            file = st.file_uploader(
                "Upload Image",
                type=["jpg", "jpeg", "png"],
                key="home_upload_image",
            )

            if file:
                uploaded_path = _save_uploaded_file(file)
                st.success("Gambar berhasil diunggah dan siap dianalisis.")

            original_name = st.session_state.get("original_filename", "-")
            uploaded_size = st.session_state.get("uploaded_size", 0)

            if uploaded_path and os.path.exists(uploaded_path):
                size_label = f"{uploaded_size / (1024 * 1024):.2f} MB" if uploaded_size else "-"
                markdown_html(
                    f"""
                    <div class="upload-preview">
                        <div class="upload-meta"><strong>{escape(original_name)}</strong> - {escape(size_label)}</div>
                    </div>
                    """
                )
                st.image(uploaded_path, use_column_width=True)
            else:
                st.info("Belum ada gambar aktif. Unggah satu file untuk memulai analisis.")

    with right_col:
        with st.container(border=True):
            markdown_html(
                """
                <div class="home-panel-head">
                    <div class="home-panel-step">2</div>
                    <div>
                        <div class="home-panel-title">Konfigurasi analisis</div>
                        <div class="home-panel-copy">Pilih aplikasi dan planogram opsional sebelum eksekusi.</div>
                    </div>
                </div>
                """
            )

            selected_app = st.selectbox(
                "App ID *",
                APP_OPTIONS,
                key="selected_app",
            )
            planogram_selection = st.selectbox(
                "Planogram ID",
                PLANOGRAM_OPTIONS,
                key="selected_planogram_id",
            )
            pricetag_enabled = False

    st.markdown('<div class="home-run-spacer"></div>', unsafe_allow_html=True)
    run_clicked = st.button("Run Analysis", type="primary", use_container_width=True)

    if run_clicked:
        if not uploaded_path or not os.path.exists(uploaded_path):
            warning_card("Upload diperlukan", "Unggah gambar terlebih dahulu sebelum menjalankan analisis.")
            return

        request_id = str(uuid.uuid4())
        run_at_iso, run_at_display = _current_run_timestamp()
        with st.spinner("Menjalankan deteksi gambar..."):
            result = analyze_display_api(
                image_path=uploaded_path,
                request_id=request_id,
                app_id=None if selected_app == "Choose an option" else selected_app,
                planogram_id=None if planogram_selection == "None" else planogram_selection,
                run_at=run_at_iso,
                pricetag=pricetag_enabled,
            )

        if not isinstance(result, dict) or result.get("status") != "success":
            warning_card(
                "Analisis gagal",
                str(result.get("message", "Model tidak berhasil memproses gambar.")) if isinstance(result, dict) else "Model tidak berhasil memproses gambar.",
            )
            return

        st.session_state.request_id = request_id
        st.session_state.run_at = run_at_iso
        st.session_state.run_at_display = run_at_display
        st.session_state.result = result
        result_body = result.get("result", {}) if isinstance(result, dict) else {}
        overview = result_body.get("overview", {}) if isinstance(result_body, dict) else {}
        st.session_state.output_path = overview.get("output_image_path") or os.path.join("output", f"{request_id}_output.jpg")
        try:
            save_analysis_result(
                request_id=request_id,
                payload=result,
                input_image_path=uploaded_path,
                output_image_path=st.session_state.output_path,
            )
            st.session_state.result_persist_warning = ""
        except Exception as e:
            st.session_state.result_persist_warning = f"Hasil analisis tidak tersimpan ke database: {e}"
        st.session_state._last_inputs = {
            "image_path": uploaded_path,
            "request_id": request_id,
            "app_id": None if selected_app == "Choose an option" else selected_app,
            "planogram_id": None if planogram_selection == "None" else planogram_selection,
            "run_at": run_at_iso,
            "pricetag": pricetag_enabled,
        }
        _record_history(
            result=result,
            request_id=request_id,
            run_at_display=run_at_display,
            selected_app=None if selected_app == "Choose an option" else selected_app,
            image_path=uploaded_path,
        )
        st.session_state.menu_selected = "Result"
        st.rerun()
