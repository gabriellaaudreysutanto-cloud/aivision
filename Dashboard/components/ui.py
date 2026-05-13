import html
import math
import textwrap
from typing import Optional

import pandas as pd
import streamlit as st


def markdown_html(markup: str):
    cleaned = textwrap.dedent(markup).strip()
    cleaned = "".join(line.strip() for line in cleaned.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def columns(spec, **kwargs):
    try:
        return st.columns(spec, **kwargs)
    except TypeError:
        compatible_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key in {"gap"}
        }
        return st.columns(spec, **compatible_kwargs)


def page_header(title: str, description: str = "", eyebrow: str = "AI Vision", chip: str = ""):
    chip_html = (
        f'<div class="app-page-chip">{html.escape(chip)}</div>'
        if chip
        else ""
    )
    eyebrow_html = (
        f'<div class="app-page-kicker">{html.escape(eyebrow)}</div>'
        if eyebrow
        else ""
    )
    description_html = (
        f'<p class="app-page-description">{html.escape(description)}</p>'
        if description
        else ""
    )
    markdown_html(
        f"""
        <div class="app-page-header">
            <div class="app-page-header-main">
                {eyebrow_html}
                <h1 class="app-page-title">{html.escape(title)}</h1>
                {description_html}
            </div>
            <div class="app-page-header-side">{chip_html}</div>
        </div>
        """
    )


def section_header(title: str, description: str = ""):
    description_html = (
        f'<p class="section-description">{html.escape(description)}</p>'
        if description
        else ""
    )
    markdown_html(
        f"""
        <div class="section-head">
            <h2 class="section-title">{html.escape(title)}</h2>
            {description_html}
        </div>
        """
    )

def kpi_card(label: str, value, help_text: str = "", accent: Optional[str] = None, tone: str = "blue", icon: str = ""):
    tone_class = html.escape(tone or "blue")
    icon_html = f'<div class="kpi-icon">{html.escape(icon)}</div>' if icon else ""
    help_html = f'<div class="kpi-help">{html.escape(help_text)}</div>' if help_text else ""
    markdown_html(
        f"""
        <div class="kpi-card {tone_class}">
            <div class="kpi-top">
                <div class="kpi-label">{html.escape(label)}</div>
                {icon_html}
            </div>
            <div class="kpi-value">{html.escape(str(value))}</div>
            {help_html}
        </div>
        """
    )


def status_pill(label: str, tone: str = "neutral"):
    markdown_html(f'<span class="status-pill {html.escape(tone)}">{html.escape(label)}</span>')


def role_hero(title: str, subtitle: str, stats: list[tuple[str, str]], kicker: str = "Selamat datang,", icon: str = "AI"):
    stats_html = "".join(
        f"""
        <div class="role-hero-stat">
            <div class="role-hero-stat-value">{html.escape(str(value))}</div>
            <div class="role-hero-stat-label">{html.escape(str(label))}</div>
        </div>
        """
        for value, label in stats
    )
    markdown_html(
        f"""
        <section class="role-hero">
            <div class="role-hero-top">
                <div>
                    <div class="role-hero-kicker">{html.escape(kicker)}</div>
                    <h2 class="role-hero-title">{html.escape(title)}</h2>
                    <div class="role-hero-subtitle">{html.escape(subtitle)}</div>
                </div>
                <div class="role-hero-icon">{html.escape(icon)}</div>
            </div>
            <div class="role-hero-stats">{stats_html}</div>
        </section>
        """
    )


def insight_strip(items: list[tuple[str, str, str]]):
    cards = "".join(
        f"""
        <div class="insight-strip-card">
            <div class="insight-strip-label">{html.escape(str(label))}</div>
            <div class="insight-strip-value">{html.escape(str(value))}</div>
            <div class="insight-strip-copy">{html.escape(str(copy))}</div>
        </div>
        """
        for label, value, copy in items
    )
    markdown_html(f'<div class="insight-strip">{cards}</div>')


def action_banner(title: str, copy: str, icon: str = "UP"):
    markdown_html(
        f"""
        <div class="action-banner">
            <div class="action-banner-main">
                <div class="action-banner-icon">{html.escape(icon)}</div>
                <div>
                    <div class="action-banner-title">{html.escape(title)}</div>
                    <div class="action-banner-copy">{html.escape(copy)}</div>
                </div>
            </div>
        </div>
        """
    )


def warning_card(title: str, copy: str, icon: str = "!"):
    markdown_html(
        f"""
        <div class="warning-card">
            <div class="warning-card-icon">{html.escape(icon)}</div>
            <div>
                <div class="warning-card-title">{html.escape(title)}</div>
                <div class="warning-card-copy">{html.escape(copy)}</div>
            </div>
        </div>
        """
    )


def list_item_card(title: str, meta: str, badge: str = "", badge_tone: str = "neutral", thumb: str = "AI"):
    badge_html = (
        f'<span class="list-card-badge {html.escape(badge_tone or "neutral")}">{html.escape(badge)}</span>'
        if badge
        else ""
    )
    markdown_html(
        f"""
        <div class="list-card">
            <div class="list-card-thumb">{html.escape(thumb)}</div>
            <div class="list-card-content">
                <div class="list-card-head">
                    <div class="list-card-title">{html.escape(title)}</div>
                    {badge_html}
                </div>
                <div class="list-card-meta">{html.escape(meta)}</div>
            </div>
        </div>
        """
    )


def paginate_dataframe(dataset: pd.DataFrame, label: str, key_prefix: str):
    if dataset.empty:
        st.info(f"No {label} found.")
        return

    toolbar = st.container(border=True)
    with toolbar:
        left, page_col, size_col = columns((4, 1, 1), vertical_alignment="bottom")
        with size_col:
            batch_size = st.selectbox("Page Size", [25, 50, 100], index=0, key=f"{key_prefix}_page_size")

        total_pages = max(1, math.ceil(len(dataset) / batch_size))
        with page_col:
            current_page = st.number_input("Page", 1, total_pages, step=1, key=f"{key_prefix}_page")

        with left:
            markdown_html(
                f"""
                <div class="section-head">
                    <div class="section-title">Data table</div>
                    <p class="section-description">Page <strong>{current_page}</strong> of <strong>{total_pages}</strong> - showing <strong>{len(dataset)}</strong> {html.escape(label)}.</p>
                </div>
                """
            )

    pages = [
        dataset.iloc[i:i + batch_size, :].reset_index(drop=True)
        for i in range(0, len(dataset), batch_size)
    ]
    idx = min(int(current_page) - 1, len(pages) - 1)
    st.dataframe(pages[idx], use_container_width=True, hide_index=True)
