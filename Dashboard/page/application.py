import streamlit as st
import pandas as pd
from components.header import render_header
from components.ui import columns, kpi_card, markdown_html, paginate_dataframe, section_header
from utils.db import fetch_all, execute_query


# ==========================================================
# LOAD DATA FROM POSTGRESQL
# ==========================================================
def load_apps_df() -> pd.DataFrame:
    rows = fetch_all("""
        SELECT
            id,
            app_id,
            app_name,
            description,
            created_at,
            updated_at
        FROM master_apps
        WHERE deleted_at IS NULL
        ORDER BY id
    """)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Tambahkan kolom label agar tetap kompatibel dengan logic lama
    if "label" not in df.columns:
        if "app_name" in df.columns:
            df["label"] = df["app_name"].astype(str)
        else:
            df["label"] = df.astype(str).agg(" | ".join, axis=1)

    return df


def split_frame(input_df: pd.DataFrame, rows: int):
    return [
        input_df.loc[i: i + rows - 1, :].reset_index(drop=True)
        for i in range(0, len(input_df), rows)
    ]


# ==========================================================
# PAGE FUNCTION
# ==========================================================
def read_application():
    render_header("Application Info")

    # ===== Load Data =====
    try:
        dataset = load_apps_df()
    except Exception as e:
        st.error(f"Failed loading application data from database: {e}")
        return

    if "show_create_app_form" not in st.session_state:
        st.session_state.show_create_app_form = False

    if "show_edit_app_form" not in st.session_state:
        st.session_state.show_edit_app_form = False

    if "show_delete_app_form" not in st.session_state:
        st.session_state.show_delete_app_form = False

    described_count = 0
    latest_update = "-"
    if not dataset.empty:
        if "description" in dataset.columns:
            described_count = int(dataset["description"].fillna("").astype(str).str.strip().ne("").sum())
        if "updated_at" in dataset.columns:
            updated_values = dataset["updated_at"].dropna()
            if not updated_values.empty:
                latest_update = str(updated_values.max())[:19]

    stats = st.columns(3)
    with stats[0]:
        kpi_card("Applications", len(dataset), "Active application contexts", tone="blue", icon="AP")
    with stats[1]:
        kpi_card("With Description", described_count, "Records with business notes", tone="green", icon="DS")
    with stats[2]:
        kpi_card("Latest Update", latest_update, "Most recent master-data change", tone="orange", icon="UP")

    markdown_html('<div class="content-spacer sm"></div>')

    with st.container(border=True):
        section_header("Browse applications", "Search, sort, or open a maintenance form.")
        search_query = st.text_input(
            "Search",
            placeholder="Search application name, label, or app_id...",
        )

    sq = search_query.lower().strip()

    if sq:
        dataset = dataset[
            dataset.astype(str)
            .apply(lambda col: col.str.lower().str.contains(sq, na=False))
            .any(axis=1)
        ]

    # ===================================================================
    # SORT + BUTTON LAYOUT
    # ===================================================================
    with st.container(border=True):
        row2 = columns([2.4, 1.2, 1.2, 1, 1, 1], vertical_alignment="bottom")

        with row2[0]:
            sort = st.radio("Sort Data", ["No", "Yes"], horizontal=True)

        with row2[1]:
            if sort == "Yes":
                sort_field = st.selectbox("Sort By", dataset.columns.tolist())
            else:
                st.write("")

        with row2[2]:
            if sort == "Yes":
                sort_direction = st.radio("Direction", ["Asc", "Desc"], horizontal=True)
            else:
                st.write("")

        if sort == "Yes" and not dataset.empty:
            dataset = dataset.sort_values(
                by=sort_field,
                ascending=(sort_direction == "Asc"),
                ignore_index=True
            )

        with row2[3]:
            if st.button("Edit App", use_container_width=True):
                st.session_state.show_edit_app_form = True
                st.session_state.show_create_app_form = False

        with row2[4]:
            if st.button("Create App", use_container_width=True, type="primary"):
                st.session_state.show_create_app_form = True
                st.session_state.show_edit_app_form = False
                st.session_state.show_delete_app_form = False

        with row2[5]:
            if st.button("Delete App", use_container_width=True):
                st.session_state.show_delete_app_form = True
                st.session_state.show_create_app_form = False
                st.session_state.show_edit_app_form = False

    if st.session_state.show_create_app_form:
        with st.container(border=True):
            section_header("Create application", "Add a new application context for detection runs.")
            form = st.form("create_app_form", clear_on_submit=True)
        with form:
            new_app_id = st.text_input("App ID", placeholder="APP001")
            new_app_name = st.text_input("App Name", placeholder="New application name")
            new_description = st.text_area("Description", placeholder="Describe this application")
            create_col1, create_col2 = st.columns(2)
            create_submit = create_col1.form_submit_button("Save App", use_container_width=True)
            create_cancel = create_col2.form_submit_button("Cancel", use_container_width=True)

            if create_submit:
                if not new_app_id.strip() or not new_app_name.strip():
                    st.warning("App ID and App Name are required.")
                else:
                    try:
                        execute_query(
                            """
                            INSERT INTO master_apps (app_id, app_name, description, created_at, updated_at)
                            VALUES (%s, %s, %s, NOW(), NOW())
                            """,
                            (
                                new_app_id.strip(),
                                new_app_name.strip(),
                                new_description.strip() or None,
                            ),
                        )
                        st.session_state.show_create_app_form = False
                        st.success("Application created successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed creating application: {e}")

            if create_cancel:
                st.session_state.show_create_app_form = False
                st.rerun()

    if st.session_state.show_edit_app_form:
        with st.container(border=True):
            section_header("Edit application", "Update the selected application's display name or description.")
            if dataset.empty:
                st.info("No application data available to edit.")
            else:
                options = dataset[["app_id", "app_name"]].copy()
                options["display_name"] = options["app_id"].astype(str) + " - " + options["app_name"].astype(str)
                selected_label = st.selectbox("Select Application", options["display_name"].tolist())
                selected_row = options[options["display_name"] == selected_label].iloc[0]
                current_row = dataset[dataset["app_id"] == selected_row["app_id"]].iloc[0]

                with st.form("edit_app_form"):
                    edit_app_id = st.text_input("App ID", value=str(current_row.get("app_id", "")), disabled=True)
                    edit_app_name = st.text_input("App Name", value=str(current_row.get("app_name", "")))
                    edit_description = st.text_area("Description", value=str(current_row.get("description", "") or ""))
                    edit_col1, edit_col2 = st.columns(2)
                    edit_submit = edit_col1.form_submit_button("Update App", use_container_width=True)
                    edit_cancel = edit_col2.form_submit_button("Cancel", use_container_width=True)

                    if edit_submit:
                        if not edit_app_name.strip():
                            st.warning("App Name is required.")
                        else:
                            try:
                                execute_query(
                                    """
                                    UPDATE master_apps
                                    SET app_name = %s,
                                        description = %s,
                                        updated_at = NOW()
                                    WHERE app_id = %s
                                      AND deleted_at IS NULL
                                    """,
                                    (
                                        edit_app_name.strip(),
                                        edit_description.strip() or None,
                                        edit_app_id.strip(),
                                    ),
                                )
                                st.session_state.show_edit_app_form = False
                                st.success("Application updated successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed updating application: {e}")

                    if edit_cancel:
                        st.session_state.show_edit_app_form = False
                        st.rerun()

    if st.session_state.show_delete_app_form:
        with st.container(border=True):
            section_header("Delete application", "Soft-delete the selected application from master data lists.")
            if dataset.empty:
                st.info("No application data available to delete.")
            else:
                options = dataset[["app_id", "app_name"]].copy()
                options["display_name"] = options["app_id"].astype(str) + " - " + options["app_name"].astype(str)
                selected_label = st.selectbox("Select Application to Delete", options["display_name"].tolist(), key="delete_app_select")

                with st.form("delete_app_form"):
                    confirm_delete = st.checkbox("I understand this application will be hidden from master data lists.")
                    delete_col1, delete_col2 = st.columns(2)
                    delete_submit = delete_col1.form_submit_button("Delete App", use_container_width=True)
                    delete_cancel = delete_col2.form_submit_button("Cancel", use_container_width=True)

                    if delete_submit:
                        if not confirm_delete:
                            st.warning("Please confirm before deleting.")
                        else:
                            delete_app_id = selected_label.split(" - ", 1)[0]
                            try:
                                execute_query(
                                    """
                                    UPDATE master_apps
                                    SET deleted_at = NOW(),
                                        updated_at = NOW()
                                    WHERE app_id = %s
                                      AND deleted_at IS NULL
                                    """,
                                    (delete_app_id,),
                                )
                                st.session_state.show_delete_app_form = False
                                st.success("Application deleted successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed deleting application: {e}")

                    if delete_cancel:
                        st.session_state.show_delete_app_form = False
                        st.rerun()

    paginate_dataframe(dataset, "applications", "apps")
