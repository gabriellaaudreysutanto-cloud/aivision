import streamlit as st
import pandas as pd
from components.header import render_header
from components.ui import columns, kpi_card, paginate_dataframe, section_header
from utils.db import fetch_all, execute_query

css_path = "/home/kai-01/AI-Vision/Dashboard/assets/styles_table.css"


# =====================================================
# FETCH PRODUCT RAW FROM POSTGRESQL
# =====================================================
@st.cache_data(show_spinner=False, ttl=60)
def fetch_products_raw():
    return fetch_all("""
        SELECT
            mp.id,
            mp.app_id,
            mp.product_id,
            mp.product_name,
            mp.short_name,
            mp.category,
            mp.product_type,
            mp.model_status,
            mb.brand_id,
            mb.brand_name,
            mb.brand_group,
            mp.created_at,
            mp.updated_at
        FROM master_products mp
        LEFT JOIN master_brands mb
            ON mp.brand_id = mb.brand_id
        WHERE mp.deleted_at IS NULL
        ORDER BY mp.id
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


@st.cache_data(show_spinner=False, ttl=60)
def fetch_apps():
    return fetch_all("""
        SELECT app_id, app_name
        FROM master_apps
        WHERE deleted_at IS NULL
        ORDER BY app_name
    """)


@st.cache_data(show_spinner=False, ttl=60)
def fetch_brands():
    return fetch_all("""
        SELECT brand_id, brand_name
        FROM master_brands
        WHERE deleted_at IS NULL
        ORDER BY brand_name
    """)


# =====================================================
# MAIN PAGE
# =====================================================
def read_product():
    render_header("Product List")

    try:
        products_raw = fetch_products_raw()
    except Exception as e:
        st.error(f"Failed to load product data from database: {e}")
        return

    if "show_add_product_form" not in st.session_state:
        st.session_state.show_add_product_form = False

    if "show_delete_product_form" not in st.session_state:
        st.session_state.show_delete_product_form = False

    stats = st.columns(3)
    with stats[0]:
        kpi_card("Products", len(products_raw), "Product records", tone="blue", icon="PR")
    with stats[1]:
        brands = len({row.get("brand_id") for row in products_raw if row.get("brand_id")})
        kpi_card("Brands", brands, tone="purple", icon="BR")
    with stats[2]:
        categories = len({row.get("category") for row in products_raw if row.get("category")})
        kpi_card("Categories", categories, tone="orange", icon="CT")

    with st.container(border=True):
        section_header("Browse products", "Search product master data or open add/delete workflows.")
        search = st.text_input("Search", placeholder="Search product name, brand, category, or type...")
        sort_row = columns([3, 1, 1], vertical_alignment="bottom")

        with sort_row[0]:
            sort = st.radio("Sort Data", ["No", "Yes"], horizontal=True)

        with sort_row[1]:
            if st.button("Add Product", use_container_width=True, type="primary"):
                st.session_state.show_add_product_form = True
                st.session_state.show_delete_product_form = False

        with sort_row[2]:
            if st.button("Delete Product", use_container_width=True):
                st.session_state.show_delete_product_form = True
                st.session_state.show_add_product_form = False

    q = (search or "").strip()
    if q:
        products_raw = [p for p in products_raw if item_matches_query(p, q)]
    dataset = pd.DataFrame(products_raw)

    if st.session_state.show_add_product_form:
        with st.container(border=True):
            section_header("Add product", "Create a product record and optionally link it to a brand.")
        try:
            apps = fetch_apps()
            brands = fetch_brands()
        except Exception as e:
            st.error(f"Failed loading form options: {e}")
            return

        app_labels = ["- Select App -"] + [
            f"{row['app_id']} - {row['app_name']}" for row in apps
        ]
        brand_labels = ["- No Brand -"] + [
            f"{row['brand_id']} - {row['brand_name']}" for row in brands
        ]

        with st.form("add_product_form", clear_on_submit=True):
            selected_app = st.selectbox("Application", app_labels)
            product_id = st.text_input("Product ID", placeholder="PROD001")
            product_name = st.text_input("Product Name", placeholder="Product name")
            short_name = st.text_input("Short Name", placeholder="Short product name")
            category = st.text_input("Category", placeholder="Beverage")
            product_type = st.text_input("Product Type", placeholder="owner")
            selected_brand = st.selectbox("Brand", brand_labels)
            form_col1, form_col2 = st.columns(2)
            save_product = form_col1.form_submit_button("Save Product", use_container_width=True)
            cancel_product = form_col2.form_submit_button("Cancel", use_container_width=True)

            if save_product:
                if selected_app == "- Select App -" or not product_id.strip() or not product_name.strip():
                    st.warning("Application, Product ID, and Product Name are required.")
                else:
                    app_id = selected_app.split(" - ", 1)[0]
                    brand_id = None if selected_brand == "- No Brand -" else selected_brand.split(" - ", 1)[0]
                    try:
                        execute_query(
                            """
                            INSERT INTO master_products
                            (app_id, product_id, product_name, short_name, category, product_type, model_status, brand_id, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            """,
                            (
                                app_id,
                                product_id.strip(),
                                product_name.strip(),
                                short_name.strip() or None,
                                category.strip() or None,
                                product_type.strip() or None,
                                "ACTIVE",
                                brand_id,
                            ),
                        )
                        st.cache_data.clear()
                        st.session_state.show_add_product_form = False
                        st.success("Product created successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed creating product: {e}")

            if cancel_product:
                st.session_state.show_add_product_form = False
                st.rerun()

    if st.session_state.show_delete_product_form:
        with st.container(border=True):
            section_header("Delete product", "Soft-delete the selected product from master data lists.")
            if dataset.empty:
                st.info("No product data available to delete.")
            else:
                delete_options = dataset[["product_id", "product_name"]].copy()
                delete_options["display_name"] = delete_options["product_id"].astype(str) + " - " + delete_options["product_name"].astype(str)
                selected_product = st.selectbox("Select Product to Delete", delete_options["display_name"].tolist(), key="delete_product_select")

                with st.form("delete_product_form"):
                    confirm_delete = st.checkbox("I understand this product will be hidden from master data lists.")
                    delete_col1, delete_col2 = st.columns(2)
                    delete_submit = delete_col1.form_submit_button("Delete Product", use_container_width=True)
                    delete_cancel = delete_col2.form_submit_button("Cancel", use_container_width=True)

                    if delete_submit:
                        if not confirm_delete:
                            st.warning("Please confirm before deleting.")
                        else:
                            product_id_to_delete = selected_product.split(" - ", 1)[0]
                            try:
                                execute_query(
                                    """
                                    UPDATE master_products
                                    SET deleted_at = NOW(),
                                        updated_at = NOW()
                                    WHERE product_id = %s
                                      AND deleted_at IS NULL
                                    """,
                                    (product_id_to_delete,),
                                )
                                st.cache_data.clear()
                                st.session_state.show_delete_product_form = False
                                st.success("Product deleted successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed deleting product: {e}")

                    if delete_cancel:
                        st.session_state.show_delete_product_form = False
                        st.rerun()

    if sort == "Yes" and not dataset.empty:
        sort_field = st.selectbox("Sort By", dataset.columns.tolist())
        sort_direction = st.radio("Direction", ["Asc", "Desc"], horizontal=True)
        dataset = dataset.sort_values(
            by=sort_field,
            ascending=(sort_direction == "Asc"),
            ignore_index=True
        )

    paginate_dataframe(dataset, "products", "products")
