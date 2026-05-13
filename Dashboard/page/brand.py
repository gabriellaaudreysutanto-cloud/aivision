import streamlit as st
import pandas as pd
from components.header import render_header
from components.ui import columns, kpi_card, paginate_dataframe, section_header
from utils.db import fetch_all, execute_query


# =====================================================
# FETCH BRAND RAW FROM POSTGRESQL
# =====================================================
@st.cache_data(show_spinner=False, ttl=60)
def fetch_brands_raw():
    return fetch_all("""
        SELECT
            id,
            brand_id,
            app_id,
            brand_name,
            brand_group,
            created_at,
            updated_at
        FROM master_brands
        WHERE deleted_at IS NULL
        ORDER BY id
    """)


# =====================================================
# SEARCH MATCHER
# =====================================================
def item_matches_query(item: dict, q: str) -> bool:
    if not q:
        return True

    q = q.lower()
    for v in item.values():
        if q in str(v).lower():
            return True
    return False


# =====================================================
# PAGINATION HELPER
# =====================================================
def split_frame(input_df: pd.DataFrame, rows: int):
    return [
        input_df.iloc[i:i + rows, :].reset_index(drop=True)
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


# =====================================================
# MAIN PAGE
# =====================================================
def read_brand():
    render_header("Brand List")

    if "show_add_brand_form" not in st.session_state:
        st.session_state.show_add_brand_form = False

    if "show_delete_brand_form" not in st.session_state:
        st.session_state.show_delete_brand_form = False

    try:
        brands_raw = fetch_brands_raw()
    except Exception as e:
        st.error(f"Failed to load brand data from database: {e}")
        return

    stats = st.columns(3)
    with stats[0]:
        kpi_card("Brands", len(brands_raw), "Active records", tone="purple", icon="BR")
    with stats[1]:
        grouped = len({row.get("brand_group") for row in brands_raw if row.get("brand_group")})
        kpi_card("Brand Groups", grouped, tone="blue", icon="GP")
    with stats[2]:
        apps = len({row.get("app_id") for row in brands_raw if row.get("app_id")})
        kpi_card("Applications", apps, tone="green", icon="AP")

    with st.container(border=True):
        section_header("Browse brands", "Search the brand catalog or open a maintenance form.")
        search = st.text_input("Search", placeholder="Search brand name, group, or app_id...")

        sort_row = columns([3, 1, 1], vertical_alignment="bottom")

        with sort_row[0]:
            sort = st.radio("Sort Data", ["No", "Yes"], horizontal=True, index=0)

        with sort_row[1]:
            if st.button("Add Brand", use_container_width=True, type="primary"):
                st.session_state.show_add_brand_form = True
                st.session_state.show_delete_brand_form = False

        with sort_row[2]:
            if st.button("Delete Brand", use_container_width=True):
                st.session_state.show_delete_brand_form = True
                st.session_state.show_add_brand_form = False

    if st.session_state.show_add_brand_form:
        with st.container(border=True):
            section_header("Add brand", "Create a new brand and attach it to an application.")
        try:
            apps = fetch_apps()
        except Exception as e:
            st.error(f"Failed loading application options: {e}")
            return

        app_labels = ["- Select App -"] + [
            f"{row['app_id']} - {row['app_name']}" for row in apps
        ]

        with st.form("add_brand_form", clear_on_submit=True):
            selected_app = st.selectbox("Application", app_labels)
            brand_id = st.text_input("Brand ID", placeholder="BR001")
            brand_name = st.text_input("Brand Name", placeholder="Brand name")
            brand_group = st.text_input("Brand Group", placeholder="Group A")
            form_col1, form_col2 = st.columns(2)
            save_brand = form_col1.form_submit_button("Save Brand", use_container_width=True)
            cancel_brand = form_col2.form_submit_button("Cancel", use_container_width=True)

            if save_brand:
                if selected_app == "- Select App -" or not brand_id.strip() or not brand_name.strip():
                    st.warning("Application, Brand ID, and Brand Name are required.")
                else:
                    app_id = selected_app.split(" - ", 1)[0]
                    try:
                        execute_query(
                            """
                            INSERT INTO master_brands
                            (brand_id, app_id, brand_name, brand_group, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, NOW(), NOW())
                            """,
                            (
                                brand_id.strip(),
                                app_id,
                                brand_name.strip(),
                                brand_group.strip() or None,
                            ),
                        )
                        st.cache_data.clear()
                        st.session_state.show_add_brand_form = False
                        st.success("Brand created successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed creating brand: {e}")

            if cancel_brand:
                st.session_state.show_add_brand_form = False
                st.rerun()

    if st.session_state.show_delete_brand_form:
        with st.container(border=True):
            section_header("Delete brand", "Soft-delete the selected brand from master data lists.")
            if not brands_raw:
                st.info("No brand data available to delete.")
            else:
                delete_options = pd.DataFrame(brands_raw)[["brand_id", "brand_name"]].copy()
                delete_options["display_name"] = delete_options["brand_id"].astype(str) + " - " + delete_options["brand_name"].astype(str)
                selected_brand = st.selectbox("Select Brand to Delete", delete_options["display_name"].tolist(), key="delete_brand_select")

                with st.form("delete_brand_form"):
                    confirm_delete = st.checkbox("I understand this brand will be hidden from master data lists.")
                    delete_col1, delete_col2 = st.columns(2)
                    delete_submit = delete_col1.form_submit_button("Delete Brand", use_container_width=True)
                    delete_cancel = delete_col2.form_submit_button("Cancel", use_container_width=True)

                    if delete_submit:
                        if not confirm_delete:
                            st.warning("Please confirm before deleting.")
                        else:
                            brand_id_to_delete = selected_brand.split(" - ", 1)[0]
                            try:
                                execute_query(
                                    """
                                    UPDATE master_brands
                                    SET deleted_at = NOW(),
                                        updated_at = NOW()
                                    WHERE brand_id = %s
                                      AND deleted_at IS NULL
                                    """,
                                    (brand_id_to_delete,),
                                )
                                st.cache_data.clear()
                                st.session_state.show_delete_brand_form = False
                                st.success("Brand deleted successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed deleting brand: {e}")

                    if delete_cancel:
                        st.session_state.show_delete_brand_form = False
                        st.rerun()

    q = (search or "").strip()
    if q:
        brands_raw = [b for b in brands_raw if item_matches_query(b, q)]

    dataset = pd.DataFrame(brands_raw)

    if sort == "Yes" and not dataset.empty:
        sort_field = st.selectbox("Sort By", list(dataset.columns))
        sort_dir = st.radio("Direction", ["Asc", "Desc"], horizontal=True)
        dataset = dataset.sort_values(
            sort_field,
            ascending=(sort_dir == "Asc"),
            ignore_index=True
        )

    paginate_dataframe(dataset, "brands", "brands")
