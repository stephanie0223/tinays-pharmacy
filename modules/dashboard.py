import pandas as pd
import streamlit as st

from datetime import date, timedelta

from database import (
    get_db_connection,
    get_medicine_stock_summary
)


# ==========================================================
# GET STOCK COLUMN SAFELY
# ==========================================================

def get_stock_column(df):
    """
    Returns the correct stock column from the medicine
    stock summary.

    Supports:
    - available_stock
    - total_stock
    - stock
    """

    if df.empty:
        return None

    possible_columns = [
        "available_stock",
        "total_stock",
        "stock",
        "quantity"
    ]

    for column in possible_columns:
        if column in df.columns:
            return column

    return None


# ==========================================================
# RENDER DASHBOARD
# ==========================================================

def render(user):

    st.header("📊 Dashboard")

    conn = None

    try:

        # ==================================================
        # DATABASE CONNECTION
        # ==================================================

        conn = get_db_connection()

        # ==================================================
        # GET CURRENT INVENTORY
        # ==================================================

        med_df = get_medicine_stock_summary()

        # Make sure we have a DataFrame
        if med_df is None:
            med_df = pd.DataFrame()

        elif not isinstance(med_df, pd.DataFrame):
            try:
                med_df = pd.DataFrame(med_df)
            except Exception:
                med_df = pd.DataFrame()

        # ==================================================
        # DETERMINE STOCK COLUMN
        # ==================================================

        stock_column = get_stock_column(med_df)

        # ==================================================
        # TOTAL MEDICINES
        # ==================================================

        total_medicines = len(med_df)

        # ==================================================
        # TOTAL CURRENT STOCK
        # ==================================================

        if (
            not med_df.empty
            and stock_column is not None
        ):

            # Convert stock values safely to numbers
            med_df[stock_column] = pd.to_numeric(
                med_df[stock_column],
                errors="coerce"
            ).fillna(0)

            total_stock = med_df[
                stock_column
            ].sum()

        else:

            total_stock = 0

        # ==================================================
        # LOW STOCK
        # ==================================================

        if (
            not med_df.empty
            and stock_column is not None
        ):

            low_stock = len(
                med_df[
                    (med_df[stock_column] > 0)
                    &
                    (med_df[stock_column] <= 10)
                ]
            )

        else:

            low_stock = 0

        # ==================================================
        # OUT OF STOCK
        # ==================================================

        if (
            not med_df.empty
            and stock_column is not None
        ):

            out_stock = len(
                med_df[
                    med_df[stock_column] <= 0
                ]
            )

        else:

            out_stock = 0

        # ==================================================
        # EXPIRATION DATES
        # ==================================================

        today = date.today().isoformat()

        thirty_days = (
            date.today()
            + timedelta(days=30)
        ).isoformat()

        # ==================================================
        # EXPIRED
        # ==================================================

        try:

            expired_result = pd.read_sql_query(
                """
                SELECT COUNT(*) AS cnt
                FROM inventory_batches
                WHERE expiration_date < ?
                AND quantity > 0
                """,
                conn,
                params=[today]
            )

            expired = int(
                expired_result.iloc[0]["cnt"]
            )

        except Exception:

            expired = 0

        # ==================================================
        # NEAR EXPIRY
        # ==================================================

        try:

            near_expiry_result = pd.read_sql_query(
                """
                SELECT COUNT(*) AS cnt
                FROM inventory_batches
                WHERE expiration_date
                BETWEEN ? AND ?
                AND quantity > 0
                """,
                conn,
                params=[
                    today,
                    thirty_days
                ]
            )

            near_expiry = int(
                near_expiry_result.iloc[0]["cnt"]
            )

        except Exception:

            near_expiry = 0

        # ==================================================
        # DASHBOARD CARDS
        # ==================================================

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Total Medicines",
            total_medicines
        )

        c2.metric(
            "Available Stock",
            int(total_stock)
        )

        c3.metric(
            "Low Stock",
            low_stock
        )

        c4.metric(
            "Out of Stock",
            out_stock
        )

        c5.metric(
            "Expired / Near Expiry",
            f"{expired} / {near_expiry}"
        )

        st.markdown("---")

        # ==================================================
        # INVENTORY OVERVIEW
        # ==================================================

        left, right = st.columns(
            [2, 1],
            gap="medium"
        )

        # ==================================================
        # LEFT - INVENTORY
        # ==================================================

        with left:

            st.subheader(
                "📦 Inventory Stock Overview"
            )

            if not med_df.empty:

                # ------------------------------------------
                # CREATE DISPLAY DATAFRAME
                # ------------------------------------------

                display_columns = []

                # Medicine name
                if "name" in med_df.columns:
                    display_columns.append("name")

                # Generic name
                if "generic_name" in med_df.columns:
                    display_columns.append(
                        "generic_name"
                    )

                # Category
                if "category" in med_df.columns:
                    display_columns.append(
                        "category"
                    )

                # Price
                if "price" in med_df.columns:
                    display_columns.append(
                        "price"
                    )

                # Correct stock column
                if stock_column is not None:
                    display_columns.append(
                        stock_column
                    )

                # ------------------------------------------
                # CHECK IF DATA EXISTS
                # ------------------------------------------

                if display_columns:

                    inventory_display = med_df[
                        display_columns
                    ].copy()

                    # --------------------------------------
                    # RENAME STOCK COLUMN
                    # --------------------------------------

                    if stock_column is not None:

                        inventory_display = (
                            inventory_display.rename(
                                columns={
                                    stock_column:
                                        "available_stock"
                                }
                            )
                        )

                        inventory_display[
                            "available_stock"
                        ] = pd.to_numeric(
                            inventory_display[
                                "available_stock"
                            ],
                            errors="coerce"
                        ).fillna(0).astype(int)

                    # --------------------------------------
                    # RENAME COLUMNS FOR DISPLAY
                    # --------------------------------------

                    rename_map = {

                        "name":
                            "Medicine",

                        "generic_name":
                            "Generic Name",

                        "category":
                            "Category",

                        "price":
                            "Price",

                        "available_stock":
                            "Available Stock"
                    }

                    inventory_display = (
                        inventory_display.rename(
                            columns=rename_map
                        )
                    )

                    # --------------------------------------
                    # FORMAT PRICE
                    # --------------------------------------

                    if "Price" in inventory_display.columns:

                        inventory_display[
                            "Price"
                        ] = pd.to_numeric(
                            inventory_display[
                                "Price"
                            ],
                            errors="coerce"
                        ).fillna(0)

                        inventory_display[
                            "Price"
                        ] = inventory_display[
                            "Price"
                        ].map(
                            lambda x:
                            f"₱{x:,.2f}"
                        )

                    # --------------------------------------
                    # DISPLAY TABLE
                    # --------------------------------------

                    st.dataframe(
                        inventory_display,
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info(
                        "No inventory columns are available."
                    )

            else:

                st.info(
                    "No medicines registered yet."
                )

        # ==================================================
        # RIGHT - RECENT ACTIVITIES
        # ==================================================

        with right:

            st.subheader(
                "🕒 Recent Activities"
            )

            try:

                recent = pd.read_sql_query(
                    """
                    SELECT
                        st.transaction_type,
                        m.name AS medicine,
                        st.quantity,
                        st.notes,
                        st.timestamp
                    FROM stock_transactions st
                    JOIN medicines m
                        ON st.medicine_id = m.id
                    ORDER BY st.timestamp DESC
                    LIMIT 6
                    """,
                    conn
                )

            except Exception:

                recent = pd.DataFrame()

            if not recent.empty:

                st.dataframe(
                    recent,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No stock transactions yet."
                )

        # ==================================================
        # STOCK OUT SUMMARY
        # ==================================================

        st.markdown("---")

        st.subheader(
            "📤 Recent Stock Out"
        )

        try:

            stock_out = pd.read_sql_query(
                """
                SELECT
                    st.id,
                    m.name AS medicine,
                    st.quantity AS quantity_out,
                    st.notes,
                    u.username AS processed_by,
                    st.timestamp
                FROM stock_transactions st
                JOIN medicines m
                    ON st.medicine_id = m.id
                LEFT JOIN users u
                    ON st.user_id = u.id
                WHERE st.transaction_type = 'OUT'
                ORDER BY st.timestamp DESC
                LIMIT 10
                """,
                conn
            )

        except Exception:

            stock_out = pd.DataFrame()

        if not stock_out.empty:

            st.dataframe(
                stock_out,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No Stock Out transactions yet."
            )

    except Exception as e:

        # ==================================================
        # DASHBOARD ERROR
        # ==================================================

        st.error(
            f"⚠️ Unable to load dashboard: {e}"
        )

    finally:

        # ==================================================
        # CLOSE DATABASE
        # ==================================================

        if conn is not None:

            try:
                conn.close()
            except Exception:
                pass