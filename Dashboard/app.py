import streamlit as st
import os
USE_MOCK = os.getenv("USE_MOCK", "1") == "1"

# --------------- PAGE CONFIG ---------------
st.set_page_config(page_title="AI Vision Dashboard",
                   layout="wide",
                   initial_sidebar_state="expanded")

# --------------- IMPORT SETELAH PAGE CONFIG ---------------
from components.sidebar import render_sidebar
from components.style import global_style
from page.home_page import render_home_page
from page.planogram import read_planogram  
from page.brand import read_brand
from page.result_page import render_result_page
from page.product import read_product

# --------------- INITIAL SETUP ---------------
os.makedirs("output", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Apply style
global_style()

# Render sidebar
page = render_sidebar()

# --------------- ROUTING ---------------
if page == "Home":
    render_home_page()
elif page == "Planogram":
    read_planogram()
elif page == "Product":
    read_product()
elif page == "Brand":
    read_brand()
elif page == "Result":
    render_result_page()

# --------------- FOOTER ---------------
st.markdown(
    """
    <div class="footer">
        Powered by <b>Bosnet AI Vision</b> (C) 2025
    </div>
    """,
    unsafe_allow_html=True,
)
