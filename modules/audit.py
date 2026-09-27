import pandas as pd
import streamlit as st

from database import get_db_connection


# ==========================================================
# ENSURE AUDIT TABLE
# ==========================================================

def ensure_audit_table():

    conn = get_db_connection()

    try:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

    finally:

        conn.close()


# ==========================================================
# MAIN RENDER
# ==========================================================

def render(user):

    # ======================================================
    # SECURITY CHECK
    # ======================================================

    if user is None:

        st.error(
            "User information is missing."
        )

        return


    if user.get("role") != "Administrator":

        st.error(
            "🚫 Access Denied. "
            "Only Administrators can access "
            "the Audit Trail."
        )

        st.stop()


    # ======================================================
    # INITIALIZE
    # ======================================================

    ensure_audit_table()


    st.header(
        "📜 System Audit Trail"
    )


    st.caption(
        "View system activities and actions."
    )


    # ======================================================
    # LOAD AUDIT LOGS
    # ======================================================

    conn = get_db_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT
                id,
                username,
                action,
                details,
                timestamp
            FROM audit_trail
            ORDER BY id DESC
            """,
            conn
        )

    except Exception as e:

        st.error(
            f"Unable to load audit trail: {e}"
        )

        df = pd.DataFrame()

    finally:

        conn.close()


    # ======================================================
    # DISPLAY AUDIT LOGS
    # ======================================================

    if df.empty:

        st.info(
            "📭 No audit activities found."
        )

    else:

        # ==================================================
        # REMOVE ID FROM DISPLAY
        # ==================================================

        display_df = df.drop(
            columns=["id"],
            errors="ignore"
        )


        # ==================================================
        # RENAME COLUMNS
        # ==================================================

        display_df = display_df.rename(
            columns={
                "username": "Username",
                "action": "Action",
                "details": "Details",
                "timestamp": "Date & Time"
            }
        )


        # ==================================================
        # CUSTOM TABLE CSS
        # ==================================================

        st.markdown(
            """
            <style>

            /* =========================================
               AUDIT TABLE CONTAINER
               ========================================= */

            div[data-testid="stDataFrame"] {
                width: 100% !important;
            }


            /* =========================================
               TABLE
               ========================================= */

            div[data-testid="stDataFrame"] iframe {
                width: 100% !important;
            }


            /* =========================================
               GENERAL DATAFRAME HEIGHT
               ========================================= */

            div[data-testid="stDataFrame"] {
                min-height: 520px !important;
            }


            /* =========================================
               TABLE TEXT
               ========================================= */

            div[data-testid="stDataFrame"] [role="gridcell"] {
                font-size: 15px !important;
            }


            /* =========================================
               TABLE HEADER
               ========================================= */

            div[data-testid="stDataFrame"] [role="columnheader"] {
                font-size: 15px !important;
                font-weight: 700 !important;
            }

            </style>
            """,
            unsafe_allow_html=True
        )


        # ==================================================
        # DISPLAY LARGE TABLE
        # ==================================================

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=600,
            column_config={

                "Username": st.column_config.TextColumn(
                    "Username",
                    width="medium"
                ),

                "Action": st.column_config.TextColumn(
                    "Action",
                    width="medium"
                ),

                "Details": st.column_config.TextColumn(
                    "Details",
                    width="large"
                ),

                "Date & Time": st.column_config.TextColumn(
                    "Date & Time",
                    width="medium"
                )
            }
        )