import pandas as pd
import streamlit as st

from database import (
    get_db_connection,
    log_audit
)


def render(user):

    st.header("💊 Medicine Information Management")

    tab1, tab2 = st.tabs([
        "📋 Medicine Catalog",
        "➕ Add Medicine"
    ])

    conn = get_db_connection()

    # =====================================================
    # MEDICINE CATALOG
    # =====================================================

    with tab1:

        # =================================================
        # SEARCH MEDICINES
        # =================================================

        st.subheader("📋 Medicine Catalog")

        search = st.text_input(
            "🔍 Search Medicine",
            placeholder=(
                "Search by medicine name, generic name, "
                "category, dosage, or description..."
            ),
            key="medicine_search"
        )

        # =================================================
        # GET MEDICINES
        # =================================================

        df = pd.read_sql_query(
            """
            SELECT
                id,
                name,
                generic_name,
                brand_name,
                category,
                dosage_strength,
                price,
                description
            FROM medicines
            ORDER BY name ASC
            """,
            conn
        )

        # =================================================
        # FILTER SEARCH RESULTS
        # =================================================

        if not df.empty and search.strip():

            search_text = search.strip().lower()

            searchable_columns = [
                "name",
                "generic_name",
                "brand_name",
                "category",
                "dosage_strength",
                "description"
            ]

            # Create a combined searchable text
            search_mask = pd.Series(
                False,
                index=df.index
            )

            for column in searchable_columns:

                if column in df.columns:

                    search_mask = (
                        search_mask
                        |
                        df[column]
                        .fillna("")
                        .astype(str)
                        .str.lower()
                        .str.contains(
                            search_text,
                            case=False,
                            na=False,
                            regex=False
                        )
                    )

            df = df[search_mask].copy()

        # =================================================
        # SEARCH RESULT COUNT
        # =================================================

        if search.strip():

            st.caption(
                f"🔎 {len(df)} medicine(s) found "
                f"for **'{search.strip()}'**"
            )

        # =================================================
        # NO MEDICINES
        # =================================================

        if df.empty:

            if search.strip():

                st.info(
                    f"🔍 No medicines found for "
                    f"**'{search.strip()}'**."
                )

            else:

                st.info(
                    "📭 No medicines have been added yet."
                )

        else:

            # =================================================
            # ADMIN VIEW
            # =================================================

            if user["role"] == "Administrator":

                for _, medicine in df.iterrows():

                    with st.container(border=True):

                        col1, col2, col3 = st.columns(
                            [6, 1, 1]
                        )

                        # -------------------------------------
                        # MEDICINE DETAILS
                        # -------------------------------------

                        with col1:

                            st.markdown(
                                f"### 💊 {medicine['name']}"
                            )

                            st.write(
                                f"**Generic Name:** "
                                f"{medicine['generic_name'] or 'N/A'}"
                            )

                            st.write(
                                f"**Category:** "
                                f"{medicine['category'] or 'N/A'}"
                            )

                            st.write(
                                f"**Dosage & Strength:** "
                                f"{medicine['dosage_strength'] or 'N/A'}"
                            )

                            st.write(
                                f"**Price:** "
                                f"₱{float(medicine['price']):,.2f}"
                            )

                            if medicine["description"]:

                                st.caption(
                                    f"Description: "
                                    f"{medicine['description']}"
                                )

                        # -------------------------------------
                        # EDIT
                        # -------------------------------------

                        with col2:

                            if st.button(
                                "✏️ Edit",
                                key=f"edit_{medicine['id']}",
                                help="Edit Medicine"
                            ):

                                st.session_state[
                                    "edit_medicine_id"
                                ] = int(medicine["id"])

                                st.session_state.pop(
                                    "delete_medicine_id",
                                    None
                                )

                                st.rerun()

                        # -------------------------------------
                        # DELETE
                        # -------------------------------------

                        with col3:

                            if st.button(
                                "🗑️ Delete",
                                key=f"delete_{medicine['id']}",
                                help="Delete Medicine"
                            ):

                                st.session_state[
                                    "delete_medicine_id"
                                ] = int(medicine["id"])

                                st.session_state.pop(
                                    "edit_medicine_id",
                                    None
                                )

                                st.rerun()

                # =================================================
                # EDIT MEDICINE
                # =================================================

                edit_id = st.session_state.get(
                    "edit_medicine_id"
                )

                if edit_id:

                    medicine_data = df[
                        df["id"] == edit_id
                    ]

                    if not medicine_data.empty:

                        medicine = medicine_data.iloc[0]

                        st.markdown("---")

                        st.subheader(
                            "✏️ Edit Medicine"
                        )

                        with st.form(
                            "edit_medicine_form"
                        ):

                            edit_name = st.text_input(
                                "Brand / Trade Name",
                                value=str(
                                    medicine["name"] or ""
                                )
                            )

                            edit_generic = st.text_input(
                                "Generic Name",
                                value=str(
                                    medicine["generic_name"] or ""
                                )
                            )

                            categories = [
                                "Antibiotic",
                                "Analgesic",
                                "Antipyretic",
                                "Antihypertensive",
                                "Vitamins",
                                "Supplements",
                                "Other"
                            ]

                            current_category = (
                                medicine["category"]
                            )

                            if current_category not in categories:

                                current_category = "Other"

                            edit_category = st.selectbox(
                                "Category",
                                categories,
                                index=categories.index(
                                    current_category
                                )
                            )

                            edit_dosage = st.text_input(
                                "Dosage & Strength",
                                value=str(
                                    medicine["dosage_strength"] or ""
                                )
                            )

                            edit_price = st.number_input(
                                "Unit Price",
                                min_value=0.0,
                                value=float(
                                    medicine["price"]
                                ),
                                step=0.01,
                                format="%.2f"
                            )

                            edit_description = st.text_area(
                                "Medicine Description & Usage",
                                value=str(
                                    medicine["description"] or ""
                                )
                            )

                            col1, col2 = st.columns(2)

                            with col1:

                                save = st.form_submit_button(
                                    "💾 Save Changes",
                                    use_container_width=True
                                )

                            with col2:

                                cancel = st.form_submit_button(
                                    "❌ Cancel",
                                    use_container_width=True
                                )

                            # -------------------------------------
                            # CANCEL
                            # -------------------------------------

                            if cancel:

                                st.session_state.pop(
                                    "edit_medicine_id",
                                    None
                                )

                                st.rerun()

                            # -------------------------------------
                            # SAVE
                            # -------------------------------------

                            if save:

                                if not edit_name.strip():

                                    st.warning(
                                        "⚠️ Please enter the "
                                        "medicine name."
                                    )

                                elif edit_price <= 0:

                                    st.warning(
                                        "⚠️ Please enter a "
                                        "valid price."
                                    )

                                else:

                                    duplicate = conn.execute(
                                        """
                                        SELECT id
                                        FROM medicines
                                        WHERE LOWER(name) =
                                              LOWER(?)
                                        AND id != ?
                                        """,
                                        (
                                            edit_name.strip(),
                                            edit_id
                                        )
                                    ).fetchone()

                                    if duplicate:

                                        st.error(
                                            "⚠️ Another medicine "
                                            "with this name already exists."
                                        )

                                    else:

                                        conn.execute(
                                            """
                                            UPDATE medicines
                                            SET
                                                name = ?,
                                                generic_name = ?,
                                                brand_name = ?,
                                                category = ?,
                                                dosage_strength = ?,
                                                price = ?,
                                                description = ?
                                            WHERE id = ?
                                            """,
                                            (
                                                edit_name.strip(),
                                                edit_generic.strip(),
                                                edit_name.strip(),
                                                edit_category,
                                                edit_dosage.strip(),
                                                edit_price,
                                                edit_description.strip(),
                                                edit_id
                                            )
                                        )

                                        conn.commit()

                                        log_audit(
                                            user["id"],
                                            user["username"],
                                            "Updated Medicine",
                                            f"Medicine ID: {edit_id}, "
                                            f"Name: {edit_name.strip()}"
                                        )

                                        st.session_state.pop(
                                            "edit_medicine_id",
                                            None
                                        )

                                        st.success(
                                            "✅ Medicine updated successfully!"
                                        )

                                        st.rerun()

                # =================================================
                # DELETE MEDICINE
                # =================================================

                delete_id = st.session_state.get(
                    "delete_medicine_id"
                )

                if delete_id:

                    medicine_data = df[
                        df["id"] == delete_id
                    ]

                    if not medicine_data.empty:

                        medicine_name = (
                            medicine_data.iloc[0]["name"]
                        )

                        st.markdown("---")

                        st.warning(
                            f"⚠️ Are you sure you want to "
                            f"delete **{medicine_name}**?"
                        )

                        st.write(
                            "This action cannot be undone."
                        )

                        col1, col2 = st.columns(2)

                        # -----------------------------------------
                        # CONFIRM DELETE
                        # -----------------------------------------

                        with col1:

                            if st.button(
                                "🗑️ Yes, Delete",
                                key="confirm_delete",
                                use_container_width=True
                            ):

                                inventory_count = conn.execute(
                                    """
                                    SELECT COUNT(*) AS count
                                    FROM inventory_batches
                                    WHERE medicine_id = ?
                                    """,
                                    (delete_id,)
                                ).fetchone()["count"]

                                if inventory_count > 0:

                                    st.error(
                                        "❌ Cannot delete this medicine "
                                        "because it has inventory records."
                                    )

                                    st.info(
                                        "Process or remove the related "
                                        "inventory records first."
                                    )

                                else:

                                    conn.execute(
                                        """
                                        DELETE FROM medicines
                                        WHERE id = ?
                                        """,
                                        (delete_id,)
                                    )

                                    conn.commit()

                                    log_audit(
                                        user["id"],
                                        user["username"],
                                        "Deleted Medicine",
                                        f"Medicine ID: {delete_id}, "
                                        f"Name: {medicine_name}"
                                    )

                                    st.session_state.pop(
                                        "delete_medicine_id",
                                        None
                                    )

                                    st.success(
                                        f"✅ {medicine_name} "
                                        f"was deleted successfully!"
                                    )

                                    st.rerun()

                        # -----------------------------------------
                        # CANCEL DELETE
                        # -----------------------------------------

                        with col2:

                            if st.button(
                                "❌ Cancel",
                                key="cancel_delete",
                                use_container_width=True
                            ):

                                st.session_state.pop(
                                    "delete_medicine_id",
                                    None
                                )

                                st.rerun()

            # =================================================
            # PHARMACIST / STAFF / CUSTOMER
            # =================================================

            else:

                display_df = df[
                    [
                        "name",
                        "generic_name",
                        "category",
                        "dosage_strength",
                        "price",
                        "description"
                    ]
                ].copy()

                display_df["price"] = (
                    display_df["price"]
                    .apply(
                        lambda x:
                        f"₱{float(x):,.2f}"
                    )
                )

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

    # =====================================================
    # ADD MEDICINE
    # =====================================================

    with tab2:

        st.subheader(
            "➕ Add New Medicine"
        )

        with st.form(
            "medicine_form",
            clear_on_submit=True
        ):

            name = st.text_input(
                "Brand / Trade Name",
                placeholder="Example: Biogesic"
            )

            generic = st.text_input(
                "Generic Name",
                placeholder="Example: Paracetamol"
            )

            category = st.selectbox(
                "Category",
                [
                    "Antibiotic",
                    "Analgesic",
                    "Antipyretic",
                    "Antihypertensive",
                    "Vitamins",
                    "Supplements",
                    "Other"
                ]
            )

            dosage = st.text_input(
                "Dosage & Strength",
                placeholder="Example: 500 mg"
            )

            price = st.number_input(
                "Unit Price",
                min_value=0.0,
                step=0.01,
                format="%.2f"
            )

            description = st.text_area(
                "Medicine Description & Usage",
                placeholder="Enter medicine description..."
            )

            submit = st.form_submit_button(
                "💾 Save Medicine",
                use_container_width=True
            )

            if submit:

                if not name.strip():

                    st.warning(
                        "⚠️ Please enter the medicine name."
                    )

                elif price <= 0:

                    st.warning(
                        "⚠️ Please enter a valid medicine price."
                    )

                else:

                    clean_name = name.strip()
                    clean_generic = generic.strip()
                    clean_dosage = dosage.strip()

                    # =========================================
                    # CHECK DUPLICATE MEDICINE
                    # =========================================

                    existing = conn.execute(
                        """
                        SELECT
                            id,
                            name,
                            generic_name,
                            category,
                            dosage_strength,
                            price
                        FROM medicines
                        WHERE LOWER(TRIM(name))
                              = LOWER(TRIM(?))
                        AND LOWER(
                            TRIM(
                                COALESCE(generic_name, '')
                            )
                        )
                            = LOWER(TRIM(?))
                        AND LOWER(
                            TRIM(
                                COALESCE(dosage_strength, '')
                            )
                        )
                            = LOWER(TRIM(?))
                        """,
                        (
                            clean_name,
                            clean_generic,
                            clean_dosage
                        )
                    ).fetchone()

                    # =========================================
                    # MEDICINE ALREADY EXISTS
                    # =========================================

                    if existing:

                        st.warning(
                            "⚠️ This medicine is already added."
                        )

                        st.info(
                            f"""
**Medicine:** {existing['name']}

**Generic Name:** {existing['generic_name'] or 'N/A'}

**Category:** {existing['category'] or 'N/A'}

**Dosage & Strength:** {existing['dosage_strength'] or 'N/A'}

**Current Price:** ₱{float(existing['price']):,.2f}

The medicine was **not added again**.
"""
                        )

                    # =========================================
                    # ADD NEW MEDICINE
                    # =========================================

                    else:

                        conn.execute(
                            """
                            INSERT INTO medicines
                            (
                                name,
                                generic_name,
                                brand_name,
                                category,
                                dosage_strength,
                                price,
                                description
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                clean_name,
                                clean_generic,
                                clean_name,
                                category,
                                clean_dosage,
                                price,
                                description.strip()
                            )
                        )

                        conn.commit()

                        log_audit(
                            user["id"],
                            user["username"],
                            "Added Medicine",
                            f"Name: {clean_name}"
                        )

                        st.success(
                            f"✅ {clean_name} "
                            f"has been added successfully!"
                        )

                        st.rerun()

    # =====================================================
    # CLOSE DATABASE
    # =====================================================

    conn.close()