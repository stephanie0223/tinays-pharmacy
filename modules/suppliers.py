import pandas as pd
import streamlit as st

from database import (
    get_db_connection,
    log_audit
)


def render(user):

    st.header(
        "🚚 Supplier Management"
    )

    tab1, tab2 = st.tabs([
        "Supplier Directory",
        "Register Supplier"
    ])

    conn = get_db_connection()

    with tab1:

        df = pd.read_sql_query(
            "SELECT * FROM suppliers",
            conn
        )

        st.dataframe(
            df,
            use_container_width=True
        )

    with tab2:

        with st.form(
            "supplier_form"
        ):

            name = st.text_input(
                "Supplier Company Name"
            )

            contact = st.text_input(
                "Contact Person"
            )

            phone = st.text_input(
                "Phone Number"
            )

            email = st.text_input(
                "Email Address"
            )

            address = st.text_area(
                "Address"
            )

            submit = st.form_submit_button(
                "Register Supplier"
            )

            if submit and name:

                conn.execute(
                    """
                    INSERT INTO suppliers
                    (
                        name,
                        contact_person,
                        phone,
                        email,
                        address
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        contact,
                        phone,
                        email,
                        address
                    )
                )

                conn.commit()

                log_audit(
                    user["id"],
                    user["username"],
                    "Added Supplier",
                    f"Supplier: {name}"
                )

                st.success(
                    "Supplier registered!"
                )

                st.rerun()

    conn.close()