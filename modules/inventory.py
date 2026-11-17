import pandas as pd
import streamlit as st

from datetime import date, datetime, timedelta

from database import (
    get_db_connection,
    log_audit
)


# ==========================================================
# SUCCESS NOTIFICATION
# ==========================================================

def _set_success_notification(message, icon="✅"):

    st.session_state["success_notification"] = {
        "message": message,
        "icon": icon
    }


def _show_success_notification():

    notification = st.session_state.get(
        "success_notification"
    )

    if not notification:
        return

    st.toast(
        notification.get("message", ""),
        icon=notification.get("icon", "✅")
    )

    st.session_state.pop(
        "success_notification",
        None
    )


# ==========================================================
# MAIN RENDER
# ==========================================================

def render(user):

    st.header("📦 Inventory Management")

    # ======================================================
    # SHOW SUCCESS POPUP
    # ======================================================

    _show_success_notification()

    # ======================================================
    # TABS
    # ======================================================

    tab_stock_in, tab_stock_out, tab_history = st.tabs(
        [
            "📥 Stock In",
            "📤 Stock Out",
            "📜 History"
        ]
    )

    # ======================================================
    # DATABASE
    # ======================================================

    conn = get_db_connection()

    # ======================================================
    # MEDICINES
    # ======================================================

    medicines = pd.read_sql_query(
        """
        SELECT
            id,
            name
        FROM medicines
        ORDER BY name
        """,
        conn
    )

    med_dict = {}

    if not medicines.empty:

        med_dict = dict(
            zip(
                medicines["name"],
                medicines["id"]
            )
        )

    # ======================================================
    # SUPPLIERS
    # ======================================================

    suppliers = pd.read_sql_query(
        """
        SELECT
            id,
            name
        FROM suppliers
        ORDER BY name
        """,
        conn
    )

    supplier_dict = {}

    if not suppliers.empty:

        supplier_dict = dict(
            zip(
                suppliers["name"],
                suppliers["id"]
            )
        )

    # ======================================================
    # ======================================================
    # STOCK IN
    # ======================================================
    # ======================================================

    with tab_stock_in:

        st.subheader("📥 Add Medicine Stock")

        st.caption(
            "Add new medicine quantities to the pharmacy inventory."
        )

        st.divider()

        if med_dict:

            with st.form("stock_in_form"):

                # ------------------------------------------
                # MEDICINE
                # ------------------------------------------

                medicine = st.selectbox(
                    "💊 Medicine",
                    list(med_dict),
                    key="stock_in_medicine"
                )

                # ------------------------------------------
                # SUPPLIER
                # ------------------------------------------

                supplier = st.selectbox(
                    "🏢 Supplier",
                    ["None"] + list(supplier_dict),
                    key="stock_in_supplier"
                )

                # ------------------------------------------
                # BATCH
                # ------------------------------------------

                batch = st.text_input(
                    "📋 Batch Number",
                    value=(
                        "BATCH-" +
                        datetime.now().strftime(
                            "%Y%m%d%H%M"
                        )
                    ),
                    key="stock_in_batch"
                )

                # ------------------------------------------
                # QUANTITY
                # ------------------------------------------

                quantity = st.number_input(
                    "📦 Quantity to Add",
                    min_value=1,
                    step=1,
                    value=1,
                    key="stock_in_quantity"
                )

                # ------------------------------------------
                # EXPIRATION
                # ------------------------------------------

                expiration = st.date_input(
                    "📅 Expiration Date",
                    value=(
                        date.today()
                        +
                        timedelta(days=365)
                    ),
                    key="stock_in_expiration"
                )

                # ------------------------------------------
                # NOTES
                # ------------------------------------------

                notes = st.text_input(
                    "📝 Notes",
                    key="stock_in_notes"
                )

                # ------------------------------------------
                # SUBMIT
                # ------------------------------------------

                submit = st.form_submit_button(
                    "📥 Record Stock In",
                    use_container_width=True
                )

                if submit:

                    med_id = med_dict[
                        medicine
                    ]

                    supplier_id = supplier_dict.get(
                        supplier
                    )

                    # ======================================
                    # VALIDATION
                    # ======================================

                    if not batch.strip():

                        st.error(
                            "❌ Please enter a batch number."
                        )

                    elif expiration <= date.today():

                        st.error(
                            "❌ Expiration date must be in the future."
                        )

                    else:

                        try:

                            cur = conn.cursor()

                            # ==================================
                            # INSERT INVENTORY BATCH
                            # ==================================

                            cur.execute(
                                """
                                INSERT INTO inventory_batches
                                (
                                    medicine_id,
                                    supplier_id,
                                    batch_number,
                                    quantity,
                                    expiration_date
                                )
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    med_id,
                                    supplier_id,
                                    batch.strip(),
                                    int(quantity),
                                    expiration.isoformat()
                                )
                            )

                            batch_id = cur.lastrowid

                            # ==================================
                            # RECORD TRANSACTION
                            # ==================================

                            cur.execute(
                                """
                                INSERT INTO stock_transactions
                                (
                                    medicine_id,
                                    batch_id,
                                    transaction_type,
                                    quantity,
                                    notes,
                                    user_id
                                )
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    med_id,
                                    batch_id,
                                    "IN",
                                    int(quantity),
                                    notes,
                                    user["id"]
                                )
                            )

                            # ==================================
                            # COMMIT
                            # ==================================

                            conn.commit()

                            # ==================================
                            # AUDIT
                            # ==================================

                            log_audit(
                                user["id"],
                                user["username"],
                                "Stock In",
                                (
                                    f"{medicine}: "
                                    f"+{quantity}"
                                )
                            )

                            # ==================================
                            # POPUP
                            # ==================================

                            _set_success_notification(
                                (
                                    f"Stock In Already Done — "
                                    f"{medicine} +{quantity} "
                                    f"successfully added to inventory."
                                ),
                                icon="📥"
                            )

                            st.rerun()

                        except Exception as e:

                            conn.rollback()

                            st.error(
                                f"❌ Stock In failed: {e}"
                            )

        else:

            st.warning(
                "⚠️ No medicines available. "
                "Please add a medicine first."
            )

    # ======================================================
    # ======================================================
    # STOCK OUT
    # ======================================================
    # ======================================================

    with tab_stock_out:

        st.subheader("📤 Stock Out")
        st.caption(
            "Search for medicines, select one or more items, "
            "set the quantity for each, and record them together."
        )
        st.divider()

        if med_dict:

            # --------------------------------------------------
            # GET CURRENT STOCK FOR EACH MEDICINE
            # --------------------------------------------------

            stock_cards = pd.read_sql_query(
                """
                SELECT
                    m.id AS medicine_id,
                    m.name AS medicine_name,
                    COALESCE(SUM(ib.quantity), 0) AS current_stock
                FROM medicines m
                LEFT JOIN inventory_batches ib
                    ON ib.medicine_id = m.id
                GROUP BY m.id, m.name
                ORDER BY m.name
                """,
                conn
            )

            # Keep selected medicine IDs between Streamlit reruns.
            selected_ids = st.session_state.get(
                "stock_out_selected_medicine_ids", []
            )
            selected_ids = [int(item) for item in selected_ids]

            # Remove selections for medicines that no longer exist.
            valid_ids = set(stock_cards["medicine_id"].astype(int).tolist())
            selected_ids = [item for item in selected_ids if item in valid_ids]
            st.session_state["stock_out_selected_medicine_ids"] = selected_ids

            # --------------------------------------------------
            # SEARCH
            # --------------------------------------------------

            search_text = st.text_input(
                "🔍 Search Medicine",
                placeholder="Type a medicine name to search...",
                key="stock_out_medicine_search"
            ).strip()

            if search_text:
                visible_cards = stock_cards[
                    stock_cards["medicine_name"].str.contains(
                        search_text, case=False, na=False, regex=False
                    )
                ].copy()
            else:
                visible_cards = stock_cards.copy()

            # --------------------------------------------------
            # SELECT / DESELECT MEDICINES
            # --------------------------------------------------

            st.markdown("#### 💊 Select Medicines")
            st.caption(
                f"{len(selected_ids)} medicine(s) selected. "
                "You can select multiple medicines."
            )

            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if st.button(
                    "☑️ Select All Results",
                    key="stock_out_select_all",
                    use_container_width=True,
                    disabled=visible_cards.empty
                ):
                    selectable_ids = visible_cards[
                        visible_cards["current_stock"] > 0
                    ]["medicine_id"].astype(int).tolist()
                    st.session_state["stock_out_selected_medicine_ids"] = sorted(
                        set(selected_ids).union(selectable_ids)
                    )
                    st.rerun()

            with action_col2:
                if st.button(
                    "✖ Clear Selection",
                    key="stock_out_clear_selection",
                    use_container_width=True,
                    disabled=not selected_ids
                ):
                    st.session_state["stock_out_selected_medicine_ids"] = []
                    st.rerun()

            if visible_cards.empty:
                st.warning("No medicines match your search.")
            else:
                card_columns = st.columns(3)

                for index, medicine_row in visible_cards.iterrows():
                    medicine_id = int(medicine_row["medicine_id"])
                    medicine_name = str(medicine_row["medicine_name"])
                    current_stock = int(medicine_row["current_stock"] or 0)
                    checkbox_key = f"stock_out_select_checkbox_{medicine_id}"

                    with card_columns[index % 3]:
                        with st.container(border=True):
                            st.markdown(f"**💊 {medicine_name}**")
                            st.metric("Available Stock", current_stock)

                            if current_stock <= 0:
                                st.caption("🔴 Out of stock")
                            elif current_stock <= 10:
                                st.caption("🟠 Low stock")
                            else:
                                st.caption("🟢 Available")

                            checked = medicine_id in selected_ids
                            new_checked = st.checkbox(
                                "Select medicine",
                                value=checked,
                                key=checkbox_key,
                                disabled=(current_stock <= 0)
                            )

                            if new_checked and medicine_id not in selected_ids:
                                selected_ids.append(medicine_id)
                            elif not new_checked and medicine_id in selected_ids:
                                selected_ids.remove(medicine_id)

                # Persist checkbox changes after rendering all cards.
                st.session_state["stock_out_selected_medicine_ids"] = sorted(
                    set(selected_ids)
                )

            # --------------------------------------------------
            # QUANTITY FORM FOR ALL SELECTED MEDICINES
            # --------------------------------------------------

            selected_rows = stock_cards[
                stock_cards["medicine_id"].isin(
                    st.session_state["stock_out_selected_medicine_ids"]
                )
            ].copy()

            if not selected_rows.empty:
                st.divider()
                st.markdown("#### 📤 Stock Out Selected Medicines")
                st.info(
                    "Enter the quantity to remove for each selected medicine. "
                    "The system deducts stock using FIFO (earliest expiration first)."
                )

                with st.form("stock_out_multiple_form"):
                    quantities = {}

                    for _, selected_row in selected_rows.iterrows():
                        med_id = int(selected_row["medicine_id"])
                        medicine_name = str(selected_row["medicine_name"])
                        current_stock = int(selected_row["current_stock"] or 0)

                        st.markdown(f"**💊 {medicine_name}**")
                        st.caption(f"Available stock: {current_stock}")

                        quantities[med_id] = st.number_input(
                            f"Quantity to remove — {medicine_name}",
                            min_value=1,
                            max_value=max(1, current_stock),
                            value=1,
                            step=1,
                            key=f"stock_out_multi_quantity_{med_id}",
                            disabled=(current_stock <= 0)
                        )

                    reference = st.text_input(
                        "🧾 Reference Number / Order Number",
                        placeholder="Example: SO-2026-0001",
                        key="stock_out_multi_reference"
                    )

                    notes = st.text_input(
                        "📝 Reason / Notes",
                        key="stock_out_multi_notes"
                    )

                    submit = st.form_submit_button(
                        "📤 Stock Out All Selected",
                        use_container_width=True,
                        type="primary"
                    )

                if submit:
                    try:
                        # Validate every selected medicine before changing stock.
                        stock_plan = []
                        for _, selected_row in selected_rows.iterrows():
                            med_id = int(selected_row["medicine_id"])
                            medicine_name = str(selected_row["medicine_name"])
                            requested = int(quantities[med_id])

                            stock_result = conn.execute(
                                """
                                SELECT COALESCE(SUM(quantity), 0)
                                FROM inventory_batches
                                WHERE medicine_id = ?
                                """,
                                (med_id,)
                            ).fetchone()
                            latest_stock = int(stock_result[0] or 0)

                            if requested < 1:
                                raise Exception(
                                    f"Enter a quantity of at least 1 for {medicine_name}."
                                )
                            if requested > latest_stock:
                                raise Exception(
                                    f"Insufficient stock for {medicine_name}. "
                                    f"Available: {latest_stock}; requested: {requested}."
                                )

                            stock_plan.append(
                                (med_id, medicine_name, requested)
                            )

                        # Deduct each medicine using FIFO. All changes are
                        # committed together, or rolled back if any step fails.
                        for med_id, medicine_name, requested in stock_plan:
                            remaining = requested

                            batches = pd.read_sql_query(
                                """
                                SELECT id, quantity
                                FROM inventory_batches
                                WHERE medicine_id = ?
                                  AND quantity > 0
                                ORDER BY expiration_date ASC, id ASC
                                """,
                                conn,
                                params=[med_id]
                            )

                            for _, batch_row in batches.iterrows():
                                if remaining <= 0:
                                    break

                                batch_id = int(batch_row["id"])
                                batch_quantity = int(batch_row["quantity"])
                                deduct = min(remaining, batch_quantity)

                                if deduct > 0:
                                    update_result = conn.execute(
                                        """
                                        UPDATE inventory_batches
                                        SET quantity = quantity - ?
                                        WHERE id = ?
                                          AND quantity >= ?
                                        """,
                                        (deduct, batch_id, deduct)
                                    )

                                    if update_result.rowcount != 1:
                                        raise Exception(
                                            f"Stock changed while processing {medicine_name}. "
                                            "Please try again."
                                        )

                                    remaining -= deduct

                            if remaining > 0:
                                raise Exception(
                                    f"Unable to deduct the full quantity for {medicine_name}."
                                )

                            transaction_notes = (
                                f"Reference: {reference.strip() or 'N/A'} | "
                                f"{notes.strip() or 'No notes'}"
                            )

                            conn.execute(
                                """
                                INSERT INTO stock_transactions
                                (
                                    medicine_id,
                                    transaction_type,
                                    quantity,
                                    notes,
                                    user_id
                                )
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    med_id,
                                    "OUT",
                                    requested,
                                    transaction_notes,
                                    user["id"]
                                )
                            )

                        conn.commit()

                        # Audit each medicine after the inventory transaction commits.
                        summary_parts = []
                        for med_id, medicine_name, requested in stock_plan:
                            new_stock_result = conn.execute(
                                """
                                SELECT COALESCE(SUM(quantity), 0)
                                FROM inventory_batches
                                WHERE medicine_id = ?
                                """,
                                (med_id,)
                            ).fetchone()
                            new_stock = int(new_stock_result[0] or 0)

                            log_audit(
                                user["id"],
                                user["username"],
                                "Stock Out",
                                (
                                    f"{medicine_name}: -{requested} | "
                                    f"Reference: {reference.strip() or 'N/A'} | "
                                    f"Remaining: {new_stock}"
                                )
                            )
                            summary_parts.append(
                                f"{medicine_name} -{requested} "
                                f"(remaining: {new_stock})"
                            )

                        st.session_state["stock_out_selected_medicine_ids"] = []
                        _set_success_notification(
                            "Stock Out completed — " + "; ".join(summary_parts),
                            icon="📤"
                        )
                        st.rerun()

                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Stock Out failed: {e}")

            else:
                st.caption(
                    "Search for medicines and select one or more available "
                    "medicine cards to enter stock-out quantities."
                )

        else:
            st.warning(
                "⚠️ No medicines available. Please add a medicine first."
            )

    # ======================================================
    # ======================================================
    # HISTORY
    # ======================================================
    # ======================================================

    with tab_history:

        st.subheader(
            "📜 Stock Transaction History"
        )

        st.caption(
            "Search for a medicine to view its Stock In and Stock Out transactions."
        )

        st.divider()

        # ==================================================
        # GET TRANSACTION HISTORY
        # ==================================================

        df = pd.read_sql_query(
            """
            SELECT
                st.id AS transaction_id,
                st.batch_id,
                m.name AS medicine,
                st.transaction_type,
                st.quantity,
                st.notes,
                u.username,
                st.timestamp

            FROM stock_transactions st

            JOIN medicines m
                ON st.medicine_id = m.id

            LEFT JOIN users u
                ON st.user_id = u.id

            WHERE st.transaction_type IN ('IN', 'OUT', 'VOID')

            ORDER BY
                m.name ASC,
                st.timestamp DESC
            """,
            conn
        )

        # ==================================================
        # NO TRANSACTIONS
        # ==================================================

        if df.empty:

            st.info(
                "📭 No stock transactions recorded yet."
            )

        else:

            # ==================================================
            # CLEAN EMPTY VALUES
            # ==================================================

            df["notes"] = df["notes"].fillna("")
            df["username"] = df["username"].fillna("Unknown")

            # ==================================================
            # SEARCH
            # ==================================================

            search = st.text_input(
                "🔍 Search Medicine",
                placeholder="Type medicine name...",
                key="history_medicine_search"
            )

            search = search.strip()

            # ==================================================
            # FILTER BY MEDICINE
            # ==================================================

            if search:

                filtered_df = df[
                    df["medicine"]
                    .str.contains(
                        search,
                        case=False,
                        na=False,
                        regex=False
                    )
                ].copy()

            else:

                filtered_df = df.copy()

            # ==================================================
            # NO SEARCH RESULTS
            # ==================================================

            if filtered_df.empty:

                st.warning(
                    f"🔍 No transaction history found for "
                    f"'{search}'."
                )

            else:

                # ==================================================
                # GET MEDICINES WITH HISTORY
                # ==================================================

                medicines_with_history = (
                    filtered_df["medicine"]
                    .drop_duplicates()
                    .tolist()
                )

                # ==================================================
                # DISPLAY EACH MEDICINE
                # ==================================================

                for medicine_name in medicines_with_history:

                    medicine_df = filtered_df[
                        filtered_df["medicine"] == medicine_name
                    ].copy()

                    # ------------------------------------------
                    # TRANSACTION COUNTS
                    # ------------------------------------------

                    stock_in_count = len(
                        medicine_df[
                            medicine_df["transaction_type"] == "IN"
                        ]
                    )

                    stock_out_count = len(
                        medicine_df[
                            medicine_df["transaction_type"] == "OUT"
                        ]
                    )

                    void_count = len(
                        medicine_df[
                            medicine_df["transaction_type"] == "VOID"
                        ]
                    )

                    total_transactions = len(
                        medicine_df
                    )

                    # ------------------------------------------
                    # MEDICINE EXPANDER
                    # ------------------------------------------

                    with st.expander(
                        f"💊 {medicine_name}   •   "
                        f"{total_transactions} transaction(s)",
                        expanded=False
                    ):

                        # --------------------------------------
                        # SUMMARY
                        # --------------------------------------

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:

                            st.metric(
                                "📥 Stock In",
                                stock_in_count
                            )

                        with col2:

                            st.metric(
                                "📤 Stock Out",
                                stock_out_count
                            )

                        with col3:

                            st.metric(
                                "🚫 Voided",
                                void_count
                            )

                        with col4:

                            st.metric(
                                "📋 Transactions",
                                total_transactions
                            )

                        st.divider()

                        # --------------------------------------
                        # TRANSACTIONS
                        # --------------------------------------

                        for _, transaction in medicine_df.iterrows():

                            transaction_type = str(
                                transaction["transaction_type"]
                            )

                            transaction_id = int(
                                transaction["transaction_id"]
                            )

                            batch_id = transaction["batch_id"]

                            # ==================================================
                            # STOCK IN
                            # ==================================================

                            if transaction_type == "IN":

                                col_a, col_b = st.columns(
                                    [5, 1.5]
                                )

                                with col_a:

                                    st.markdown(
                                        f"""
                                        **📥 STOCK IN**

                                        **Quantity:** {int(transaction["quantity"])}

                                        **Recorded By:** {transaction["username"]}

                                        **Date & Time:** {transaction["timestamp"]}

                                        **Notes:** {transaction["notes"] or "None"}
                                        """
                                    )

                                # ----------------------------------------------
                                # ADMIN VOID BUTTON
                                # ----------------------------------------------

                                with col_b:

                                    if user.get("role") == "Administrator":

                                        if st.button(
                                            "🚫 Void Stock In",
                                            key=f"void_stock_in_{transaction_id}",
                                            use_container_width=True
                                        ):

                                            # ==================================
                                            # CHECK BATCH
                                            # ==================================

                                            if pd.isna(batch_id):

                                                st.error(
                                                    "❌ This Stock In has no batch information and cannot be voided."
                                                )

                                            else:

                                                batch_id = int(
                                                    batch_id
                                                )

                                                batch_result = conn.execute(
                                                    """
                                                    SELECT
                                                        quantity,
                                                        batch_number
                                                    FROM inventory_batches
                                                    WHERE id = ?
                                                    """,
                                                    (batch_id,)
                                                ).fetchone()

                                                if not batch_result:

                                                    st.error(
                                                        "❌ The inventory batch no longer exists."
                                                    )

                                                else:

                                                    current_batch_quantity = int(
                                                        batch_result[0] or 0
                                                    )

                                                    batch_number = str(
                                                        batch_result[1] or "Unknown"
                                                    )

                                                    original_quantity = int(
                                                        transaction["quantity"]
                                                    )

                                                    # ==================================
                                                    # CHECK IF ENOUGH STOCK REMAINS
                                                    # ==================================

                                                    if current_batch_quantity < original_quantity:

                                                        st.error(
                                                            f"""
❌ Cannot Void Stock In

The batch does not have enough remaining stock.

📋 Batch: {batch_number}

📥 Original Stock In: {original_quantity}

📦 Remaining in Batch: {current_batch_quantity}

Some of this stock may already have been removed through Stock Out.
"""
                                                        )

                                                    else:

                                                        # ==================================
                                                        # CONFIRM VOID
                                                        # ==================================

                                                        st.session_state[
                                                            f"confirm_void_{transaction_id}"
                                                        ] = True

                            # ==================================================
                            # VOID CONFIRMATION
                            # ==================================================

                            if (
                                transaction_type == "IN"
                                and
                                user.get("role") == "Administrator"
                                and
                                st.session_state.get(
                                    f"confirm_void_{transaction_id}",
                                    False
                                )
                            ):

                                st.warning(
                                    f"""
⚠️ **Void Stock In Confirmation**

You are about to void:

💊 Medicine: **{medicine_name}**

📥 Stock In Quantity: **{int(transaction["quantity"])}**

📋 Transaction: **#{transaction_id}**

This will remove the Stock In quantity from the inventory.
"""
                                )

                                confirm_col, cancel_col = st.columns(2)

                                with confirm_col:

                                    if st.button(
                                        "✅ Yes, Void Stock In",
                                        key=f"confirm_void_button_{transaction_id}",
                                        use_container_width=True
                                    ):

                                        try:

                                            # ==================================
                                            # GET BATCH AGAIN
                                            # ==================================

                                            if pd.isna(batch_id):

                                                st.error(
                                                    "❌ Batch information is missing."
                                                )

                                            else:

                                                batch_id_int = int(
                                                    batch_id
                                                )

                                                batch_result = conn.execute(
                                                    """
                                                    SELECT
                                                        quantity,
                                                        batch_number
                                                    FROM inventory_batches
                                                    WHERE id = ?
                                                    """,
                                                    (batch_id_int,)
                                                ).fetchone()

                                                if not batch_result:

                                                    st.error(
                                                        "❌ Inventory batch not found."
                                                    )

                                                else:

                                                    current_quantity = int(
                                                        batch_result[0] or 0
                                                    )

                                                    original_quantity = int(
                                                        transaction["quantity"]
                                                    )

                                                    batch_number = str(
                                                        batch_result[1] or "Unknown"
                                                    )

                                                    # ==================================
                                                    # FINAL STOCK CHECK
                                                    # ==================================

                                                    if current_quantity < original_quantity:

                                                        st.error(
                                                            f"""
❌ Cannot void this Stock In.

📋 Batch: {batch_number}

📦 Current Batch Stock: {current_quantity}

📥 Original Stock In: {original_quantity}

The stock has already been partially or completely removed.
"""
                                                        )

                                                    else:

                                                        # ==================================
                                                        # REMOVE STOCK FROM BATCH
                                                        # ==================================

                                                        conn.execute(
                                                            """
                                                            UPDATE inventory_batches
                                                            SET quantity = quantity - ?
                                                            WHERE id = ?
                                                            """,
                                                            (
                                                                original_quantity,
                                                                batch_id_int
                                                            )
                                                        )

                                                        # ==================================
                                                        # RECORD VOID TRANSACTION
                                                        # ==================================

                                                        void_notes = (
                                                            f"Voided Stock In Transaction "
                                                            f"#{transaction_id} | "
                                                            f"Batch: {batch_number} | "
                                                            f"Original Quantity: "
                                                            f"{original_quantity}"
                                                        )

                                                        conn.execute(
                                                            """
                                                            INSERT INTO stock_transactions
                                                            (
                                                                medicine_id,
                                                                batch_id,
                                                                transaction_type,
                                                                quantity,
                                                                notes,
                                                                user_id
                                                            )
                                                            VALUES (?, ?, ?, ?, ?, ?)
                                                            """,
                                                            (
                                                                int(
                                                                    med_dict.get(
                                                                        medicine_name
                                                                    )
                                                                ),
                                                                batch_id_int,
                                                                "VOID",
                                                                original_quantity,
                                                                void_notes,
                                                                user["id"]
                                                            )
                                                        )

                                                        # ==================================
                                                        # COMMIT
                                                        # ==================================

                                                        conn.commit()

                                                        # ==================================
                                                        # AUDIT LOG
                                                        # ==================================

                                                        log_audit(
                                                            user["id"],
                                                            user["username"],
                                                            "Void Stock In",
                                                            (
                                                                f"{medicine_name}: "
                                                                f"-{original_quantity} | "
                                                                f"Transaction #{transaction_id} | "
                                                                f"Batch: {batch_number}"
                                                            )
                                                        )

                                                        # ==================================
                                                        # CLEAR CONFIRMATION
                                                        # ==================================

                                                        st.session_state.pop(
                                                            f"confirm_void_{transaction_id}",
                                                            None
                                                        )

                                                        # ==================================
                                                        # SUCCESS POPUP
                                                        # ==================================

                                                        _set_success_notification(
                                                            (
                                                                f"Stock In Voided — "
                                                                f"{medicine_name} "
                                                                f"{original_quantity} "
                                                                f"stock successfully removed "
                                                                f"from inventory."
                                                            ),
                                                            icon="🚫"
                                                        )

                                                        st.rerun()

                                        except Exception as e:

                                            conn.rollback()

                                            st.error(
                                                f"❌ Failed to void Stock In: {e}"
                                            )

                                with cancel_col:

                                    if st.button(
                                        "↩️ Keep Stock In",
                                        key=f"cancel_void_{transaction_id}",
                                        use_container_width=True
                                    ):

                                        st.session_state.pop(
                                            f"confirm_void_{transaction_id}",
                                            None
                                        )

                                        st.rerun()

                            # ==================================================
                            # STOCK OUT
                            # ==================================================

                            elif transaction_type == "OUT":

                                st.markdown(
                                    f"""
                                    **📤 STOCK OUT**

                                    **Quantity:** {int(transaction["quantity"])}

                                    **Recorded By:** {transaction["username"]}

                                    **Date & Time:** {transaction["timestamp"]}

                                    **Notes:** {transaction["notes"] or "None"}
                                    """
                                )

                            # ==================================================
                            # VOID
                            # ==================================================

                            elif transaction_type == "VOID":

                                st.markdown(
                                    f"""
                                    **🚫 STOCK IN VOIDED**

                                    **Quantity Voided:** {int(transaction["quantity"])}

                                    **Voided By:** {transaction["username"]}

                                    **Date & Time:** {transaction["timestamp"]}

                                    **Notes:** {transaction["notes"] or "None"}
                                    """
                                )

                            st.divider()

    # ======================================================
    # CLOSE DATABASE
    # ======================================================

    conn.close()