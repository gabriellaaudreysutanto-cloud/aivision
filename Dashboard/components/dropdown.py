import streamlit as st
from components.ui import markdown_html

def render_action_dropdown():

    # ==============================
    #   DEFAULT VALUE
    # ==============================
    if "brand_action" not in st.session_state:
        st.session_state.brand_action = "add"

    # ==============================
    #   ACTION SELECT CSS
    # ==============================
    markdown_html(
        """
        <style>
            .premium-selectbox label p {
                font-size: 14px !important;
                font-weight: 600 !important;
                color: #1d1d1f !important;
                margin-bottom: 4px !important;
            }

            .premium-selectbox div[data-baseweb="select"] > div {
                background: #ffffff !important;
                border-radius: 10px !important;
                border: 1px solid rgba(0, 0, 0, 0.10) !important;
                padding: 6px 10px !important;
                font-size: 14px !important;
            }

            .premium-selectbox div[data-baseweb="select"] > div:focus-within {
                border: 1px solid rgba(0, 113, 227, 0.55) !important;
                box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.18) !important;
                background: #ffffff !important;
            }

            .premium-selectbox div[data-baseweb="menu"] div {
                font-size: 14px !important;
                padding: 8px 12px !important;
            }

            .premium-selectbox div[data-baseweb="menu"] div:hover {
                background: #e8f6ff !important;
                color: #0071e3 !important;
            }

            .premium-selectbox div[aria-selected="true"] {
                background: #f0f7ff !important;
                font-weight: 600 !important;
            }
        </style>
        """
    )

    # ==============================
    #   ACTION LABELS
    # ==============================
    options = {
        "add": "Add",
        "edit": "Edit",
        "delete": "Delete"
    }

    # Convert readable to key for backend
    readable_list = list(options.values())
    reverse_map = {v: k for k, v in options.items()}

    current_readable = options[st.session_state.brand_action]

    # ==============================
    #   STREAMLIT SELECTBOX (PREMIUM)
    # ==============================
    with st.container():
        chosen = st.selectbox(
            "Actions",
            readable_list,
            index=readable_list.index(current_readable),
            key="premium_action_dropdown"
        )

    # Save result in session_state
    selected_action = reverse_map[chosen]
    st.session_state.brand_action = selected_action

    return selected_action
