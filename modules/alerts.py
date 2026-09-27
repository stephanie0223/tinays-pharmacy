import pandas as pd
import streamlit as st

from datetime import date, timedelta

from database import get_db_connection


# ==========================================================
# NOTIFICATIONS & ALERTS
# ==========================================================

def render(user):

    # ======================================================
    # PAGE TITLE
    # ======================================================

    st.header("🔔 Notifications & Alerts")

    conn = get_db_connection()

    try:

        # ==================================================
        # DATE SETTINGS
        # ==================================================

        today = date.today()

        alert_date = today + timedelta(days=30)

        today_str = today.isoformat()
        alert_date_str = alert_date.isoformat()


        # ==================================================
        # GET TOTAL STOCK PER MEDICINE
        # ==================================================
        #
        # Instead of using get_medicine_stock_summary(),
        # calculate the stock directly from inventory_batches.
        #
        # COALESCE makes medicines with no inventory records
        # show as 0 stock.
        #

        medicines = pd.read_sql_query(
            """
            SELECT
                m.id,
                m.name,
                COALESCE(
                    SUM(
                        CASE
                            WHEN b.quantity > 0
                            AND b.expiration_date >= ?
                            THEN b.quantity
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_stock

            FROM medicines m

            LEFT JOIN inventory_batches b
                ON m.id = b.medicine_id

            GROUP BY
                m.id,
                m.name

            ORDER BY
                m.name ASC
            """,
            conn,
            params=[today_str]
        )


        # ==================================================
        # OUT OF STOCK
        # ==================================================

        out_stock = medicines[
            medicines["total_stock"] <= 0
        ].copy()


        # ==================================================
        # LOW STOCK
        # ==================================================
        #
        # 1 to 10 units remaining
        #

        low_stock = medicines[
            (medicines["total_stock"] > 0) &
            (medicines["total_stock"] <= 10)
        ].copy()


        # ==================================================
        # EXPIRED MEDICINES
        # ==================================================

        expired = pd.read_sql_query(
            """
            SELECT
                b.batch_number,
                m.name,
                b.quantity,
                b.expiration_date

            FROM inventory_batches b

            JOIN medicines m
                ON b.medicine_id = m.id

            WHERE b.expiration_date < ?
            AND b.quantity > 0

            ORDER BY
                b.expiration_date ASC
            """,
            conn,
            params=[today_str]
        )


        # ==================================================
        # NEAR EXPIRY
        # ==================================================

        near = pd.read_sql_query(
            """
            SELECT
                b.batch_number,
                m.name,
                b.quantity,
                b.expiration_date

            FROM inventory_batches b

            JOIN medicines m
                ON b.medicine_id = m.id

            WHERE b.expiration_date
                BETWEEN ? AND ?

            AND b.quantity > 0

            ORDER BY
                b.expiration_date ASC
            """,
            conn,
            params=[
                today_str,
                alert_date_str
            ]
        )


        # ==================================================
        # SUMMARY COUNTERS
        # ==================================================

        st.markdown("### 📊 Alert Summary")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "🔴 Out of Stock",
                len(out_stock)
            )

        with c2:
            st.metric(
                "🟡 Low Stock",
                len(low_stock)
            )

        with c3:
            st.metric(
                "☣️ Expired",
                len(expired)
            )

        with c4:
            st.metric(
                "⏳ Near Expiry",
                len(near)
            )


        st.markdown("---")


        # ==================================================
        # ALERT COLUMNS
        # ==================================================

        c1, c2 = st.columns(2)


        # ==================================================
        # LEFT COLUMN
        # ==================================================

        with c1:

            # ----------------------------------------------
            # OUT OF STOCK
            # ----------------------------------------------

            st.subheader("🔴 Out of Stock")

            if out_stock.empty:

                st.success(
                    "No out-of-stock medicines."
                )

            else:

                for _, row in out_stock.iterrows():

                    st.error(
                        f"💊 **{row['name']}** is out of stock."
                    )


            # ----------------------------------------------
            # LOW STOCK
            # ----------------------------------------------

            st.subheader("🟡 Low Stock")

            if low_stock.empty:

                st.info(
                    "No low stock warnings."
                )

            else:

                for _, row in low_stock.iterrows():

                    quantity = int(
                        row["total_stock"]
                    )

                    st.warning(
                        f"💊 **{row['name']}** — "
                        f"{quantity} units remaining"
                    )


        # ==================================================
        # RIGHT COLUMN
        # ==================================================

        with c2:

            # ----------------------------------------------
            # EXPIRED
            # ----------------------------------------------

            st.subheader("☣️ Expired")

            if expired.empty:

                st.success(
                    "No expired inventory."
                )

            else:

                st.error(
                    f"⚠️ {len(expired)} "
                    f"expired batch(es) found."
                )

                st.dataframe(
                    expired,
                    use_container_width=True,
                    hide_index=True
                )


            # ----------------------------------------------
            # NEAR EXPIRY
            # ----------------------------------------------

            st.subheader("⏳ Near Expiry")

            st.caption(
                "Medicines expiring within the next 30 days."
            )

            if near.empty:

                st.info(
                    "No near-expiry medicines."
                )

            else:

                st.warning(
                    f"⏳ {len(near)} "
                    f"batch(es) expiring within 30 days."
                )

                st.dataframe(
                    near,
                    use_container_width=True,
                    hide_index=True
                )


    except Exception as e:

        st.error(
            "⚠️ Unable to load notifications and alerts."
        )

        st.exception(e)


    finally:

        # ==================================================
        # CLOSE DATABASE
        # ==================================================

        conn.close()