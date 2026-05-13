import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from components.header import render_header
from components.ui import kpi_card, section_header, status_pill, warning_card
from utils.db import fetch_analysis_results, fetch_latest_analysis_result


OWN_PRODUCT_HINTS = (
    "owner",
    "owned",
    "company",
    "customer",
    "pocari",
    "ion water",
    "soyjoy",
    "or beng",
    "fibe mini",
    "adem sari",
)


def classify_facing_type(label: str, item_type=None) -> str:
    if item_type:
        normalized_type = str(item_type).strip().lower()
        if normalized_type in {"owner", "owned", "company", "customer"}:
            return "owner"
        if normalized_type in {"competitor", "other", "detected"}:
            return normalized_type

    normalized_label = str(label or "").strip().lower()
    if any(token in normalized_label for token in OWN_PRODUCT_HINTS):
        return "owner"
    return "detected"


def format_bbox(bbox) -> str:
    if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
        return "-"
    return ", ".join(str(round(float(value), 1)) for value in bbox[:4])


def normalize_product_facing_rows(inner: dict) -> pd.DataFrame:
    if not isinstance(inner, dict):
        return pd.DataFrame()

    rows = []
    detections = inner.get("detections") or inner.get("detected_products") or []
    if isinstance(detections, list):
        for index, item in enumerate(detections, start=1):
            if not isinstance(item, dict):
                continue

            label = item.get("label") or item.get("name") or item.get("product_name") or "-"
            item_type = classify_facing_type(label, item.get("type"))
            bbox = item.get("bbox") or item.get("xyxy")
            confidence = item.get("confidence", "-")
            if isinstance(confidence, (int, float)):
                confidence = round(float(confidence), 4)

            rows.append(
                {
                    "Facing No": index,
                    "Product ID": item.get("product_id", "-"),
                    "Product Name": label,
                    "Type": item_type,
                    "Confidence": confidence,
                    "X": round(float(bbox[0]), 1) if isinstance(bbox, (list, tuple)) and len(bbox) >= 1 else "-",
                    "Y": round(float(bbox[1]), 1) if isinstance(bbox, (list, tuple)) and len(bbox) >= 2 else "-",
                    "BBox": format_bbox(bbox),
                }
            )

    return pd.DataFrame(rows)


def clean_value(value, fallback: str = "-") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "nan"}:
        return fallback
    if "<" in text or ">" in text:
        return fallback
    return text


def format_run_at(value) -> str:
    text = clean_value(value)
    if text == "-":
        return text

    try:
        run_dt = datetime.fromisoformat(text)
        if run_dt.tzinfo is None:
            run_dt = run_dt.replace(tzinfo=ZoneInfo("Asia/Jakarta"))
        else:
            run_dt = run_dt.astimezone(ZoneInfo("Asia/Jakarta"))
        return run_dt.strftime("%d %B %Y, %H:%M:%S WIB")
    except ValueError:
        return text


def render_metric_card(label: str, value, help_text: str = "", tone: str = "blue", icon: str = ""):
    kpi_card(label, value, help_text, tone=tone, icon=icon)


def restore_latest_result_from_database() -> bool:
    try:
        latest = fetch_latest_analysis_result()
    except Exception as e:
        st.session_state.result_restore_warning = f"Tidak bisa mengambil hasil terakhir dari database: {e}"
        return False

    if not latest:
        return False

    payload = latest.get("payload") or {}
    if not isinstance(payload, dict):
        return False

    st.session_state.result = payload
    st.session_state.request_id = latest.get("request_id")
    st.session_state.uploaded_path = latest.get("input_image_path")
    st.session_state.output_path = latest.get("output_image_path")
    st.session_state.run_at = str(latest.get("run_at") or "")
    st.session_state.result_restore_warning = ""
    return True


def load_analysis_history(limit: int = 50) -> list[dict]:
    try:
        st.session_state.result_history_warning = ""
        return fetch_analysis_results(limit)
    except Exception as e:
        st.session_state.result_history_warning = f"Tidak bisa mengambil history hasil deteksi dari database: {e}"
        return []


def build_history_frame(history: list[dict]) -> pd.DataFrame:
    rows = []
    for item in history:
        rows.append(
            {
                "Request ID": clean_value(item.get("request_id")),
                "Foto": os.path.basename(clean_value(item.get("input_image_path"), "")) or "-",
                "Status": clean_value(item.get("status")).upper(),
                "Deteksi": item.get("detection_count", 0),
                "App": clean_value(item.get("app_id")),
                "Planogram": clean_value(item.get("planogram_id")),
                "Run At": format_run_at(item.get("run_at") or item.get("created_at")),
            }
        )
    return pd.DataFrame(rows)


def hydrate_result_from_history(item: dict):
    payload = item.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}

    st.session_state.result = payload
    st.session_state.request_id = item.get("request_id")
    st.session_state.uploaded_path = item.get("input_image_path")
    st.session_state.output_path = item.get("output_image_path")
    st.session_state.run_at = str(item.get("run_at") or "")
    return payload


def build_rack_conclusion(detection_count: int, owner_count: int, avg_conf, detections_df: pd.DataFrame):
    avg_conf_value = avg_conf if isinstance(avg_conf, (int, float)) else 0.0
    owner_ratio = (owner_count / detection_count) if detection_count else 0.0

    score = 0
    reasons = []

    if detection_count >= 8:
        score += 1
        reasons.append("jumlah objek yang terbaca sudah cukup banyak")
    elif detection_count == 0:
        reasons.append("belum ada objek yang berhasil terdeteksi")
    else:
        reasons.append("jumlah objek terdeteksi masih terbatas")

    if avg_conf_value >= 0.6:
        score += 1
        reasons.append("confidence model tergolong baik")
    else:
        reasons.append("confidence deteksi masih perlu diperhatikan")

    if owner_ratio >= 0.5:
        score += 1
        reasons.append("porsi produk owner cukup dominan di rak")
    else:
        reasons.append("porsi produk owner belum dominan di rak")

    if detection_count == 0:
        verdict = "Belum cukup baik"
        tone = "warning"
        summary = "Rak belum bisa dinilai dengan baik karena hasil deteksi masih kosong."
    elif score >= 3:
        verdict = "Sudah cukup baik"
        tone = "success"
        summary = "Secara umum kondisi rak terlihat cukup baik dan hasil deteksinya mendukung review lanjutan."
    elif score >= 2:
        verdict = "Cukup baik, tetapi masih perlu review"
        tone = "warning"
        summary = "Kondisi rak sudah lumayan, tetapi masih ada beberapa indikator yang sebaiknya ditinjau lagi."
    else:
        verdict = "Belum cukup baik"
        tone = "warning"
        summary = "Kondisi rak masih perlu perhatian karena indikator hasil deteksi belum cukup kuat."

    return {
        "verdict": verdict,
        "tone": tone,
        "summary": summary,
        "details": reasons,
        "owner_ratio": round(owner_ratio * 100, 2),
    }


def render_result_page():
    render_header(
        "Hasil Deteksi",
        "History foto yang sudah dieksekusi untuk deteksi, lengkap dengan output gambar, metadata run, dan detail objek.",
        chip="Detection History",
    )

    history = load_analysis_history()
    if st.session_state.get("result_history_warning"):
        st.warning(st.session_state.result_history_warning)

    if history:
        section_header("Riwayat eksekusi", "Pilih salah satu foto/request untuk membuka hasil deteksi detail.")
        history_frame = build_history_frame(history)
        st.dataframe(history_frame, use_container_width=True, hide_index=True)

        request_options = [item.get("request_id") for item in history if item.get("request_id")]
        current_request = st.session_state.get("selected_result_request_id") or st.session_state.get("request_id")
        selected_index = request_options.index(current_request) if current_request in request_options else 0
        selected_request = st.selectbox(
            "Buka hasil deteksi",
            request_options,
            index=selected_index,
            format_func=lambda value: next(
                (
                    f"{clean_value(item.get('request_id'))[:12]}... | "
                    f"{os.path.basename(clean_value(item.get('input_image_path'), '')) or '-'} | "
                    f"{format_run_at(item.get('run_at') or item.get('created_at'))}"
                    for item in history
                    if item.get("request_id") == value
                ),
                value,
            ),
        )
        st.session_state.selected_result_request_id = selected_request
        selected_history = next((item for item in history if item.get("request_id") == selected_request), history[0])
        raw_result = hydrate_result_from_history(selected_history)
    else:
        raw_result = st.session_state.get("result", {}) or {}
        if not raw_result:
            restore_latest_result_from_database()
            raw_result = st.session_state.get("result", {}) or {}

    inner = raw_result.get("result", raw_result) if isinstance(raw_result, dict) else {}
    overview = inner.get("overview", {}) if isinstance(inner, dict) else {}
    image_path = st.session_state.get("output_path") or clean_value(overview.get("output_image_path"), "")
    original_path = st.session_state.get("uploaded_path")

    if not raw_result and not (image_path and os.path.exists(image_path)):
        if st.session_state.get("result_restore_warning"):
            st.caption(st.session_state.result_restore_warning)
        warning_card(
            "Belum ada history hasil deteksi",
            "Mulai dari halaman Dashboard, unggah gambar, lalu jalankan analisis. Setelah selesai, foto dan hasilnya akan muncul sebagai history di halaman ini.",
        )
        quick_cols = st.columns(2)
        if quick_cols[0].button("Kembali ke Dashboard", type="primary", use_container_width=True):
            st.session_state.menu_selected = "Home"
            st.rerun()
        if quick_cols[1].button("Reset Workspace", use_container_width=True):
            for key in ["result", "output_path", "uploaded_path", "request_id", "_last_inputs"]:
                st.session_state.pop(key, None)
            st.session_state.menu_selected = "Home"
            st.rerun()
        return

    if st.session_state.get("result_persist_warning"):
        st.warning(st.session_state.result_persist_warning)

    detections_df = normalize_product_facing_rows(inner)
    detection_count = len(detections_df)
    owner_count = len(detections_df[detections_df["Type"].astype(str).str.lower() == "owner"]) if not detections_df.empty else 0
    avg_conf = (
        round(pd.to_numeric(detections_df["Confidence"], errors="coerce").dropna().mean(), 3)
        if not detections_df.empty
        else "-"
    )
    conclusion = build_rack_conclusion(detection_count, owner_count, avg_conf, detections_df)

    status = clean_value(raw_result.get("status"), "success")
    request_id = clean_value(raw_result.get("request_id"))
    app_id = clean_value(raw_result.get("app_id"))
    planogram_id = clean_value(overview.get("planogram_id"))
    output_image_path = clean_value(overview.get("output_image_path"))
    run_at_display = format_run_at(overview.get("run_at") or st.session_state.get("run_at"))

    summary_cols = st.columns(4)
    with summary_cols[0]:
        render_metric_card("Detections", detection_count, "Jumlah objek yang terdeteksi.", tone="blue", icon="DT")
    with summary_cols[1]:
        render_metric_card("Owner Facing", owner_count, "Objek yang teridentifikasi sebagai milik brand sendiri.", tone="green", icon="OF")
    with summary_cols[2]:
        render_metric_card("Avg Confidence", avg_conf, "Rata-rata confidence untuk objek terdeteksi.", tone="purple", icon="CF")
    with summary_cols[3]:
        render_metric_card("App ID", app_id, "Konteks aplikasi saat run dijalankan.", tone="orange", icon="AP")

    top_left, top_right = st.columns([1.25, 0.95], gap="large")

    with top_left:
        section_header("Visual review", "Bandingkan gambar input dengan output bounding box untuk validasi cepat.")
        image_tabs = st.tabs(["Annotated", "Original"])

        with image_tabs[0]:
            if image_path and os.path.exists(image_path):
                with st.container(border=True):
                    st.image(image_path, use_column_width=True)
            else:
                st.info("Output image belum tersedia.")

        with image_tabs[1]:
            if original_path and os.path.exists(original_path):
                with st.container(border=True):
                    st.image(original_path, use_column_width=True)
            else:
                st.info("Original image belum tersedia.")

        action_cols = st.columns(2)
        with action_cols[0]:
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    st.download_button(
                        "Download Annotated Image",
                        data=image_file.read(),
                        file_name=os.path.basename(image_path),
                        mime="image/jpeg",
                        use_container_width=True,
                    )
        with action_cols[1]:
            if st.button("Back to Dashboard", use_container_width=True):
                st.session_state.menu_selected = "Home"
                st.rerun()

    with top_right:
        section_header("Run overview", "Metadata penting untuk audit trail dan review hasil.")
        status_pill(str(status).upper(), "success" if str(status).lower() == "success" else "warning")

        meta_cols = st.columns(2)
        with meta_cols[0]:
            render_metric_card("Request ID", request_id[:12] + "..." if request_id != "-" and len(request_id) > 12 else request_id, tone="blue", icon="ID")
        with meta_cols[1]:
            render_metric_card("Planogram ID", planogram_id, tone="green", icon="PG")

        render_metric_card("Run Analysis", run_at_display, "Tanggal dan jam saat analisis dijalankan.", tone="orange", icon="TM")

        with st.container(border=True):
            st.markdown("**Execution Notes**")
            st.write(clean_value(overview.get("note"), "Inference selesai tanpa catatan tambahan."))
            st.caption(f"Output image path: {output_image_path}")

        with st.container(border=True):
            st.markdown("**Kesimpulan Kondisi Rak**")
            status_pill(conclusion["verdict"].upper(), conclusion["tone"])
            st.write(conclusion["summary"])
            st.caption(
                f"Owner ratio: {conclusion['owner_ratio']}% | Detections: {detection_count} | Avg confidence: {avg_conf}"
            )

    tabs = st.tabs(["Detection Table", "Insights", "Raw Data"])

    with tabs[0]:
        section_header("Detection detail", "Daftar objek hasil inferensi dengan posisi, jenis, dan confidence.")
        if detections_df.empty:
            st.info("Belum ada data deteksi yang bisa ditampilkan.")
        else:
            type_filter = st.selectbox("Filter type", ["All", "owner", "detected", "competitor", "other"])

            display_df = detections_df.copy()
            if type_filter != "All":
                display_df = display_df[display_df["Type"].astype(str).str.lower() == type_filter]

            display_df["Confidence"] = pd.to_numeric(display_df["Confidence"], errors="coerce")
            display_df["Confidence"] = display_df["Confidence"].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "-")

            st.dataframe(display_df, use_container_width=True, hide_index=True)

    with tabs[1]:
        section_header("Operational insights", "Ringkasan cepat untuk membantu interpretasi hasil inferensi.")
        insights_cols = st.columns(3)
        with insights_cols[0]:
            render_metric_card("Total Facing", detection_count, tone="blue", icon="FC")
        with insights_cols[1]:
            render_metric_card("Owner Ratio", f"{round((owner_count / detection_count) * 100, 2)}%" if detection_count else "0%", tone="green", icon="OR")
        with insights_cols[2]:
            render_metric_card("Detection Quality", "Good" if detection_count >= 5 else "Review", tone="purple", icon="QL")

        with st.container(border=True):
            st.markdown("**Interpretation**")
            if detections_df.empty:
                st.write("Belum ada pola yang bisa disimpulkan karena hasil deteksi kosong.")
            else:
                strongest = detections_df.sort_values(by="Confidence", ascending=False).head(5)
                st.write("Produk dengan confidence tertinggi untuk pengecekan cepat:")
                st.dataframe(
                    strongest[["Product Name", "Type", "Confidence", "BBox"]],
                    use_container_width=True,
                    hide_index=True,
                )

    with tabs[2]:
        section_header("Raw response", "Payload mentah disediakan untuk debugging atau audit teknis.")
        st.json(raw_result)
