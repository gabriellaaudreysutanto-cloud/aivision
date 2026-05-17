import base64
import os
from typing import Optional
from urllib.parse import quote

import streamlit as st


NAV_ITEMS = [
    {"name": "Home", "label": "Dashboard", "icon": "home.png", "group": "Menu Utama", "badge": ""},
    {"name": "Planogram", "label": "Planogram", "icon": "planogram.png", "group": "Master Data", "badge": ""},
    {"name": "Product", "label": "Products", "icon": "product.png", "group": "Master Data", "badge": ""},
    {"name": "Brand", "label": "Brands", "icon": "brand.png", "group": "Master Data", "badge": ""},
    {"name": "Result", "label": "Hasil Deteksi", "icon": "planogram.png", "group": "Analysis", "badge": ""},
]


def _image_to_base64(path: str) -> Optional[str]:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except OSError:
        return None


def _get_query_menu():
    try:
        return st.query_params.get("menu")
    except Exception:
        menu = st.experimental_get_query_params().get("menu", [None])
        return menu[0] if isinstance(menu, list) else menu


def _render_sidebar_css():
    st.markdown(
        """
        <style>
        :root {
            --sidebar-bg: #fafbfe;
            --sidebar-surface: #ffffff;
            --sidebar-text: #333842;
            --sidebar-muted: #7d8491;
            --sidebar-line: rgba(31, 41, 55, 0.08);
            --sidebar-soft: #eef6ff;
            --sidebar-blue: #3478df;
        }

        section[data-testid="stSidebar"],
        [data-testid="stSidebar"] {
            background: var(--sidebar-bg) !important;
            border-right: 1px solid var(--sidebar-line);
            box-shadow: 16px 0 36px rgba(15, 23, 42, 0.04);
            font-family: "Plus Jakarta Sans", ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        section[data-testid="stSidebar"] > div,
        [data-testid="stSidebar"] > div:first-child {
            background: transparent !important;
            padding: 0 !important;
        }

        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"] {
            background: transparent !important;
        }

        [data-testid="stSidebar"] a {
            text-decoration: none !important;
        }

        .sb-shell {
            color: var(--sidebar-text);
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            padding: 6.2rem 1.35rem 1.25rem;
        }

        .sb-brand-card {
            align-items: center;
            background: var(--sidebar-surface);
            border: 1px solid var(--sidebar-line);
            border-radius: 16px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
            display: flex;
            gap: 0.78rem;
            margin: 0 0 1.45rem;
            min-height: 72px;
            padding: 0.82rem 0.92rem;
        }

        .sb-logo {
            align-items: center;
            background: #eff6ff;
            border: 1px solid rgba(52, 120, 223, 0.16);
            border-radius: 14px;
            color: var(--sidebar-blue);
            display: flex;
            flex: 0 0 44px;
            font-size: 0.95rem;
            font-weight: 700;
            height: 44px;
            justify-content: center;
            overflow: hidden;
            padding: 5px;
            width: 44px;
        }

        .sb-logo img {
            border-radius: 10px;
            height: 34px;
            object-fit: cover;
            width: 34px;
        }

        .sb-brand-title {
            color: #1f2937;
            font-size: 0.95rem;
            font-weight: 700;
            line-height: 1.15;
            white-space: nowrap;
        }

        .sb-brand-meta {
            color: var(--sidebar-muted);
            font-size: 0.71rem;
            font-weight: 600;
            line-height: 1.28;
            margin-top: 0.24rem;
        }

        .sb-group-title {
            color: var(--sidebar-muted);
            font-size: 0.66rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            margin: 1.05rem 0 0.46rem 0.62rem;
            text-transform: uppercase;
        }

        .sb-nav-link {
            align-items: center;
            border: 1px solid transparent;
            border-radius: 14px;
            color: var(--sidebar-text) !important;
            display: flex;
            gap: 0.74rem;
            margin: 0.16rem 0;
            min-height: 44px;
            padding: 0.5rem 0.72rem;
            position: relative;
            transition: all 0.18s ease;
        }

        .sb-nav-link:before {
            background: transparent;
            border-radius: 999px;
            content: "";
            height: 22px;
            left: -0.42rem;
            position: absolute;
            width: 3px;
        }

        .sb-nav-link:hover {
            background: rgba(52, 120, 223, 0.06);
            border-color: rgba(52, 120, 223, 0.08);
            color: var(--sidebar-blue) !important;
            transform: translateX(2px);
        }

        .sb-nav-link.active {
            background: var(--sidebar-soft);
            border-color: rgba(52, 120, 223, 0.14);
            box-shadow: none;
            color: var(--sidebar-blue) !important;
        }

        .sb-nav-link.active:before {
            background: var(--sidebar-blue);
        }

        .sb-nav-icon {
            align-items: center;
            background: var(--sidebar-surface);
            border: 1px solid var(--sidebar-line);
            border-radius: 999px;
            display: flex;
            flex: 0 0 30px;
            height: 30px;
            justify-content: center;
            width: 30px;
        }

        .sb-nav-icon img {
            filter: grayscale(1);
            height: 14px;
            object-fit: contain;
            opacity: 0.62;
            width: 14px;
        }

        .sb-nav-link.active .sb-nav-icon {
            background: var(--sidebar-surface);
            border-color: rgba(52, 120, 223, 0.16);
        }

        .sb-nav-link.active .sb-nav-icon img {
            filter: none;
            opacity: 0.82;
        }

        .sb-nav-text {
            font-size: 0.88rem;
            font-weight: 700;
            line-height: 1.2;
        }

        .sb-badge {
            align-items: center;
            background: var(--sidebar-blue);
            border-radius: 999px;
            color: #ffffff;
            display: flex;
            font-size: 0.66rem;
            font-weight: 700;
            height: 20px;
            justify-content: center;
            margin-left: auto;
            min-width: 20px;
            padding: 0 0.35rem;
        }

        @media (max-height: 760px) {
            .sb-shell {
                padding-top: 4.4rem;
            }

            .sb-brand-card {
                margin-bottom: 1rem;
            }

            .sb-group-title {
                margin-top: 0.78rem;
            }
        }

        @media (max-width: 640px) {
            .sb-shell {
                min-height: auto;
                padding: 1rem 0.85rem;
            }

            .sb-brand-card {
                border-radius: 14px;
                margin-bottom: 1rem;
                min-height: auto;
                padding: 0.75rem;
            }

            .sb-brand-title {
                white-space: normal;
            }

            .sb-group-title {
                margin-left: 0.35rem;
                margin-top: 0.85rem;
            }

            .sb-nav-link {
                border-radius: 12px;
                min-height: 42px;
                padding: 0.48rem 0.62rem;
            }

            .sb-nav-text {
                font-size: 0.84rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_sidebar():
    if "menu_selected" not in st.session_state:
        st.session_state.menu_selected = "Home"

    query_menu = _get_query_menu()
    valid_pages = {item["name"] for item in NAV_ITEMS}
    if query_menu in valid_pages:
        st.session_state.menu_selected = query_menu
        try:
            st.query_params.clear()
        except Exception:
            st.experimental_set_query_params()

    _render_sidebar_css()
    current_page = st.session_state.get("menu_selected", "Home")
    if current_page not in valid_pages:
        current_page = "Home"
        st.session_state.menu_selected = "Home"

    components_dir = os.path.dirname(__file__)
    logo_b64 = _image_to_base64(os.path.join(os.path.dirname(components_dir), "bosnet_logo.png"))
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Bosnet">' if logo_b64 else "AI"
    result_badge = "1" if st.session_state.get("result") else ""

    html_parts = [
        '<div class="sb-shell">',
        (
            '<div class="sb-brand-card">'
            f'<div class="sb-logo">{logo_html}</div>'
            '<div>'
            '<div class="sb-brand-title">Pocari Vision</div>'
            '<div class="sb-brand-meta">Enterprise Shelf Intelligence</div>'
            '</div>'
            '</div>'
        ),
    ]

    current_group = None
    for item in NAV_ITEMS:
        if item["group"] != current_group:
            current_group = item["group"]
            html_parts.append(f'<div class="sb-group-title">{current_group}</div>')

        icon_b64 = _image_to_base64(os.path.join(components_dir, item["icon"]))
        icon_html = f'<img src="data:image/png;base64,{icon_b64}" alt="">' if icon_b64 else ""
        active = "active" if current_page == item["name"] else ""
        badge = result_badge if item["name"] == "Result" else item.get("badge", "")
        badge_html = f'<span class="sb-badge">{badge}</span>' if badge else ""
        html_parts.append(
            (
                f'<a href="?menu={quote(item["name"])}" target="_self" class="sb-nav-link {active}">'
                f'<span class="sb-nav-icon">{icon_html}</span>'
                f'<span class="sb-nav-text">{item["label"]}</span>'
                f'{badge_html}'
                '</a>'
            )
        )

    html_parts.append("</div>")

    st.sidebar.markdown("".join(html_parts), unsafe_allow_html=True)
    return current_page
