import pandas as pd
import streamlit as st

from datetime import date, timedelta

from database import get_db_connection


def render(user):

    st.header(
        "🏷️ Batch & Expiration Tracking"
    )

    conn = get_db_connection()

    today = date.today().isoformat()

    alert_date = (
        date.today() +
        timedelta(days=60)
    ).isoformat()

    # ======================================================
    # ALL BATCHES
    # ======================================================

    batches = pd.read_sql_query(
        """
        SELECT
            m.name AS medicine_name,
            b.batch_number,
            b.quantity,
            b.expiration_date,
            s.name AS supplier
        FROM inventory_batches b
        JOIN medicines m
            ON b.medicine_id = m.id
        LEFT JOIN suppliers s
            ON b.supplier_id = s.id
        ORDER BY
            b.expiration_date
        """,
        conn
    )

    # ======================================================
    # DISPLAY ALL BATCHES
    # ======================================================

    st.dataframe(
        batches,
        use_container_width=True,
        hide_index=True
    )

    # ======================================================
    # ALERT COLUMNS
    # ======================================================

    c1, c2 = st.columns(2)

    # ======================================================
    # EXPIRED BATCHES
    # ======================================================

    with c1:

        st.error(
            "🚨 Expired Batches"
        )

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
            params=[today]
        )

        if expired.empty:

            st.success(
                "✅ No expired batches."
            )

        else:

            st.dataframe(
                expired,
                use_container_width=True,
                hide_index=True
            )

    # ======================================================
    # EXPIRING WITHIN 60 DAYS
    # ======================================================

    with c2:

        st.warning(
            "⚠️ Expiring Within 60 Days"
        )

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
                today,
                alert_date
            ]
        )

        if near.empty:

            st.success(
                "✅ No batches expiring within 60 days."
            )

        else:

            st.dataframe(
                near,
                use_container_width=True,
                hide_index=True
            )

    # ======================================================
    # CLOSE DATABASE
    # ======================================================

    conn.close()