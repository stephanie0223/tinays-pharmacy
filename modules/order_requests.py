import json
import html
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from database import get_db_connection


# ==========================================================
# ENSURE ORDER TABLE
# ==========================================================

def ensure_order_tables():

    conn = get_db_connection()

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS order_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT UNIQUE NOT NULL,
                customer_name TEXT DEFAULT 'Customer',
                status TEXT DEFAULT 'Pending',
                total_amount REAL DEFAULT 0,
                items_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TEXT,
                reviewed_by TEXT
            )
            """
        )

        conn.commit()

    finally:

        conn.close()


# ==========================================================
# AUDIT TRAIL
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


def log_order_audit(username, action, details):
    ensure_audit_table()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO audit_trail (username, action, details)
            VALUES (?, ?, ?)
            """,
            (username, action, details)
        )
        conn.commit()
    finally:
        conn.close()


# ==========================================================
# GET ORDERS
# ==========================================================

def get_orders(status=None):

    ensure_order_tables()

    conn = get_db_connection()

    try:

        if status and status != "All":

            return pd.read_sql_query(
                """
                SELECT
                    id,
                    request_number,
                    customer_name,
                    status,
                    total_amount,
                    created_at,
                    reviewed_at,
                    reviewed_by,
                    items_json
                FROM order_requests
                WHERE status = ?
                ORDER BY id DESC
                """,
                conn,
                params=(status,)
            )

        return pd.read_sql_query(
            """
            SELECT
                id,
                request_number,
                customer_name,
                status,
                total_amount,
                created_at,
                reviewed_at,
                reviewed_by,
                items_json
            FROM order_requests
            ORDER BY id DESC
            """,
            conn
        )

    finally:

        conn.close()


# ==========================================================
# UPDATE ORDER STATUS + AUTOMATIC STOCK OUT
# ==========================================================

def update_order_status(order_id, status, reviewer):

    ensure_order_tables()
    ensure_audit_table()

    conn = get_db_connection()

    try:

        # ==================================================
        # GET ORDER
        # ==================================================

        order = conn.execute(
            """
            SELECT
                id,
                request_number,
                items_json,
                status
            FROM order_requests
            WHERE id = ?
            """,
            (order_id,)
        ).fetchone()

        if order is None:

            raise Exception(
                "Order request was not found."
            )

        current_status = str(
            order["status"] or ""
        )

        # ==================================================
        # PREVENT DUPLICATE APPROVAL
        # ==================================================

        if current_status == "Approved":

            raise Exception(
                "This order has already been approved "
                "and the stock has already been deducted."
            )

        # ==================================================
        # APPROVAL
        # STOCK OUT HAPPENS HERE
        # ==================================================

        if status == "Approved":

            # ------------------------------------------------
            # ONLY PENDING ORDERS CAN BE APPROVED
            # ------------------------------------------------

            if current_status != "Pending":

                raise Exception(
                    f"This order cannot be approved because "
                    f"its current status is {current_status}."
                )

            # ------------------------------------------------
            # READ ORDER ITEMS
            # ------------------------------------------------

            try:

                items = json.loads(
                    order["items_json"] or "[]"
                )

            except Exception:

                raise Exception(
                    "The order items could not be read."
                )

            if not isinstance(items, list) or not items:

                raise Exception(
                    "This order has no medicine items."
                )

            # ==================================================
            # COMBINE SAME MEDICINE
            # ==================================================
            # This prevents duplicate medicine entries from
            # accidentally using the same inventory twice.
            # ==================================================

            requested_items = {}

            for item in items:

                medicine_id = item.get(
                    "medicine_id"
                )

                medicine_name = item.get(
                    "name",
                    "Unknown Medicine"
                )

                if not medicine_id:

                    raise Exception(
                        f"Medicine ID is missing for "
                        f"{medicine_name}."
                    )

                try:

                    quantity_needed = int(
                        item.get("quantity", 0) or 0
                    )

                except (ValueError, TypeError):

                    raise Exception(
                        f"Invalid quantity for "
                        f"{medicine_name}."
                    )

                if quantity_needed <= 0:

                    raise Exception(
                        f"Invalid quantity for "
                        f"{medicine_name}."
                    )

                medicine_key = str(
                    medicine_id
                )

                if medicine_key not in requested_items:

                    requested_items[medicine_key] = {
                        "medicine_id": medicine_id,
                        "name": medicine_name,
                        "quantity": quantity_needed
                    }

                else:

                    requested_items[
                        medicine_key
                    ]["quantity"] += quantity_needed

            # ==================================================
            # STOCK PLAN
            # ==================================================
            # We first calculate the complete stock-out plan.
            # Nothing is deducted until ALL medicines pass
            # the stock check.
            # ==================================================

            stock_plan = []

            # ==================================================
            # CHECK EACH MEDICINE
            # ==================================================

            for medicine_data in requested_items.values():

                medicine_id = medicine_data[
                    "medicine_id"
                ]

                medicine_name = medicine_data[
                    "name"
                ]

                quantity_needed = medicine_data[
                    "quantity"
                ]

                # ==================================================
                # GET INVENTORY BATCHES
                # FIFO
                # EARLIEST EXPIRATION FIRST
                # ==================================================

                batches = conn.execute(
                    """
                    SELECT
                        id,
                        quantity,
                        expiration_date
                    FROM inventory_batches
                    WHERE medicine_id = ?
                      AND quantity > 0
                    ORDER BY
                        expiration_date ASC,
                        id ASC
                    """,
                    (medicine_id,)
                ).fetchall()

                # ==================================================
                # CALCULATE AVAILABLE STOCK
                # ==================================================

                total_available = sum(
                    int(batch["quantity"] or 0)
                    for batch in batches
                )

                # ==================================================
                # CHECK STOCK
                # ==================================================

                if total_available < quantity_needed:

                    raise Exception(
                        f"Insufficient stock for "
                        f"{medicine_name}. "
                        f"Available: {total_available}, "
                        f"Requested: {quantity_needed}."
                    )

                # ==================================================
                # CREATE FIFO STOCK PLAN
                # ==================================================

                remaining = quantity_needed

                for batch in batches:

                    if remaining <= 0:
                        break

                    batch_quantity = int(
                        batch["quantity"] or 0
                    )

                    deduct = min(
                        batch_quantity,
                        remaining
                    )

                    if deduct > 0:

                        stock_plan.append(
                            {
                                "batch_id": batch["id"],
                                "medicine_id": medicine_id,
                                "medicine_name": medicine_name,
                                "deduct": deduct
                            }
                        )

                    remaining -= deduct

                # ------------------------------------------------
                # SAFETY CHECK
                # ------------------------------------------------

                if remaining > 0:

                    raise Exception(
                        f"Unable to allocate enough stock "
                        f"for {medicine_name}."
                    )

            # ==================================================
            # EXECUTE STOCK OUT
            # ==================================================
            # At this point ALL medicines have sufficient stock.
            # Therefore we can safely deduct the inventory.
            # ==================================================

            for stock in stock_plan:

                conn.execute(
                    """
                    UPDATE inventory_batches
                    SET quantity = quantity - ?
                    WHERE id = ?
                      AND quantity >= ?
                    """,
                    (
                        stock["deduct"],
                        stock["batch_id"],
                        stock["deduct"]
                    )
                )

                if conn.total_changes <= 0:

                    raise Exception(
                        f"Unable to stock out "
                        f"{stock['medicine_name']}."
                    )

            # ==================================================
            # UPDATE ORDER TO APPROVED
            # ==================================================

            conn.execute(
                """
                UPDATE order_requests
                SET
                    status = ?,
                    reviewed_at = ?,
                    reviewed_by = ?
                WHERE id = ?
                """,
                (
                    "Approved",
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    reviewer,
                    order_id
                )
            )

        else:

            # ==================================================
            # OTHER STATUS
            # ==================================================
            # Example:
            # Cancelled
            #
            # No stock is deducted here.
            # ==================================================

            conn.execute(
                """
                UPDATE order_requests
                SET
                    status = ?,
                    reviewed_at = ?,
                    reviewed_by = ?
                WHERE id = ?
                """,
                (
                    status,
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    reviewer,
                    order_id
                )
            )

        # ==================================================
        # RECORD ORDER ACTION IN AUDIT TRAIL
        # ==================================================

        if status == "Approved":
            audit_action = "Approved Order"
            audit_details = (
                f"Order {order['request_number']} was approved. "
                f"Inventory stock was automatically deducted."
            )
        elif status == "Cancelled":
            audit_action = "Cancelled Order"
            audit_details = (
                f"Order {order['request_number']} was cancelled."
            )
        else:
            audit_action = f"Order Status Changed to {status}"
            audit_details = (
                f"Order {order['request_number']} status was changed "
                f"to {status}."
            )

        # Insert in the same transaction so the audit entry is saved
        # together with the order action.
        conn.execute(
            """
            INSERT INTO audit_trail (username, action, details)
            VALUES (?, ?, ?)
            """,
            (reviewer, audit_action, audit_details)
        )

        # ==================================================
        # COMMIT EVERYTHING
        # ==================================================

        conn.commit()

        return True

    except Exception:

        # ==================================================
        # ROLLBACK EVERYTHING
        # ==================================================

        conn.rollback()

        raise

    finally:

        conn.close()



# ==========================================================
# EDIT PENDING ORDER
# ==========================================================

def update_pending_order(order_id, items, editor):
    ensure_order_tables()
    ensure_audit_table()
    conn = get_db_connection()
    try:
        order = conn.execute(
            "SELECT id, request_number, status FROM order_requests WHERE id = ?",
            (order_id,)
        ).fetchone()

        if order is None:
            raise Exception("Order request was not found.")

        if str(order["status"] or "") != "Pending":
            raise Exception("Only Pending orders can be edited.")

        if not isinstance(items, list) or not items:
            raise Exception("The order must contain at least one medicine.")

        cleaned_items = []
        total_amount = 0.0

        for item in items:
            try:
                quantity = int(item.get("quantity", 0) or 0)
                price = float(item.get("price", 0) or 0)
            except (ValueError, TypeError):
                raise Exception("Invalid medicine quantity or price.")

            if quantity <= 0:
                raise Exception(f"Invalid quantity for {item.get('name', 'Medicine')}.")

            item_copy = dict(item)
            item_copy["quantity"] = quantity
            item_copy["price"] = price
            cleaned_items.append(item_copy)
            total_amount += quantity * price

        conn.execute(
            """
            UPDATE order_requests
            SET items_json = ?, total_amount = ?
            WHERE id = ? AND status = 'Pending'
            """,
            (
                json.dumps(cleaned_items, ensure_ascii=False),
                total_amount,
                order_id
            )
        )
        conn.execute(
            """
            INSERT INTO audit_trail (username, action, details)
            VALUES (?, ?, ?)
            """,
            (
                editor,
                "Edited Order",
                f"Order {order['request_number']} was edited while Pending. "
                f"The medicine quantities and order total were updated."
            )
        )

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@st.dialog("✏️ Edit Pending Order")
def edit_order_dialog(order_id, request_number, items, editor):
    st.write(f"**Order:** {request_number}")
    st.caption("Edit the medicine quantities. This is available only while the order is Pending.")

    edited_items = []

    for index, item in enumerate(items):
        name = item.get("name", "Medicine")
        generic = item.get("generic_name", "N/A")

        try:
            current_qty = int(item.get("quantity", 0) or 0)
        except (ValueError, TypeError):
            current_qty = 1

        try:
            price = float(item.get("price", 0) or 0)
        except (ValueError, TypeError):
            price = 0.0

        st.markdown(f"**{name}**")
        st.caption(f"Generic: {generic} • Price: ₱{price:,.2f}")

        new_qty = st.number_input(
            f"Quantity — {name}",
            min_value=1,
            value=max(1, current_qty),
            step=1,
            key=f"edit_qty_{order_id}_{index}"
        )

        item_copy = dict(item)
        item_copy["quantity"] = int(new_qty)
        item_copy["price"] = price
        edited_items.append(item_copy)

    new_total = sum(
        int(item.get("quantity", 0) or 0) *
        float(item.get("price", 0) or 0)
        for item in edited_items
    )

    st.divider()
    st.markdown(f"### New Total: ₱{new_total:,.2f}")

    save_col, close_col = st.columns(2)

    with save_col:
        if st.button(
            "💾 Save Changes",
            type="primary",
            use_container_width=True,
            key=f"save_edit_{order_id}"
        ):
            try:
                update_pending_order(order_id, edited_items, editor)
                st.success("Order updated successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Unable to update order: {e}")

    with close_col:
        if st.button(
            "Close",
            use_container_width=True,
            key=f"close_edit_{order_id}"
        ):
            st.rerun()


# ==========================================================
# MAIN RENDER
# ==========================================================

def render(user):

    # ------------------------------------------------------
    # CHECK USER
    # ------------------------------------------------------

    if user is None:

        st.error(
            "User information is missing."
        )

        return

    # ------------------------------------------------------
    # GET ROLE
    # ------------------------------------------------------

    role = str(
        user.get("role", "")
    )

    allowed = {
        "Administrator",
        "Pharmacist",
        "Staff",
        "Pharmacist/Staff"
    }

    # ------------------------------------------------------
    # ACCESS CONTROL
    # ------------------------------------------------------

    if role not in allowed:

        st.error(
            "🚫 Access Denied. "
            "This dashboard is for pharmacy staff."
        )

        return

    # ------------------------------------------------------
    # ENSURE TABLE
    # ------------------------------------------------------

    ensure_order_tables()

    # ======================================================
    # HEADER
    # ======================================================

    st.header(
        "📋 Order Request Dashboard"
    )

    st.caption(
        "Customer order requests from the AI Pharmacy Tablet appear here."
    )

    # ======================================================
    # STATISTICS
    # ======================================================

    c1, c2, c3, c4 = st.columns(4)

    all_df = get_orders("All")

    if not all_df.empty:

        pending = int(
            (all_df["status"] == "Pending").sum()
        )

        approved = int(
            (all_df["status"] == "Approved").sum()
        )

        cancelled = int(
            (all_df["status"] == "Cancelled").sum()
        )

    else:

        pending = 0
        approved = 0
        cancelled = 0

    c1.metric(
        "📦 Total Orders",
        len(all_df)
    )

    c2.metric(
        "⏳ Pending",
        pending
    )

    c3.metric(
        "✅ Approved",
        approved
    )

    c4.metric(
        "❌ Cancelled",
        cancelled
    )

    st.divider()

    # ======================================================
    # SEARCH + FILTER
    # ======================================================

    filter_col, search_col = st.columns(
        [1, 2]
    )

    # ------------------------------------------------------
    # STATUS FILTER
    # ------------------------------------------------------

    with filter_col:

        filter_status = st.selectbox(
            "Filter Orders",
            [
                "Pending",
                "Approved",
                "Cancelled",
                "All"
            ],
            index=0,
            key="order_status_filter"
        )

    # ------------------------------------------------------
    # ORDER NUMBER SEARCH
    # ------------------------------------------------------

    with search_col:

        search_order = st.text_input(
            "🔎 Search Order Number",
            placeholder="Example: ORD-20260908-150217",
            key="order_number_search"
        )

    # ======================================================
    # GET ORDERS
    # ======================================================

    orders = get_orders(
        filter_status
    )

    # ======================================================
    # SEARCH ORDERS
    # ======================================================

    if search_order.strip():

        search_term = search_order.strip()

        orders = orders[
            orders["request_number"]
            .astype(str)
            .str.contains(
                search_term,
                case=False,
                na=False,
                regex=False
            )
        ]

    # ======================================================
    # NO ORDERS
    # ======================================================

    if orders.empty:

        if search_order.strip():

            st.info(
                f"📭 No order requests found for "
                f"**{search_order.strip()}**."
            )

        else:

            st.info(
                "📭 No order requests found."
            )

        return

    # ======================================================
    # DISPLAY ORDERS
    # ======================================================

    for _, order in orders.iterrows():

        status = str(
            order["status"]
        )

        icon = {
            "Pending": "⏳",
            "Approved": "✅",
            "Cancelled": "❌"
        }.get(
            status,
            "📦"
        )

        # ==================================================
        # ORDER CARD
        # ==================================================

        with st.container(
            border=True
        ):

            top = st.columns(
                [2.1, 1.2, 1.2, 1.0]
            )

            # ----------------------------------------------
            # ORDER NUMBER
            # ----------------------------------------------

            top[0].markdown(
                f"### {icon} "
                f"{html.escape(str(order['request_number']))}"
            )

            # ----------------------------------------------
            # CUSTOMER
            # ----------------------------------------------

            top[1].write(
                f"**Customer**\n"
                f"{order['customer_name']}"
            )

            # ----------------------------------------------
            # DATE
            # ----------------------------------------------

            top[2].write(
                f"**Date**\n"
                f"{order['created_at']}"
            )

            # ----------------------------------------------
            # STATUS
            # ----------------------------------------------

            top[3].write(
                f"**Status**\n"
                f"{status}"
            )

            # ----------------------------------------------
            # TOTAL
            # ----------------------------------------------

            st.write(
                f"**Total:** "
                f"₱{float(order['total_amount'] or 0):,.2f}"
            )

            # ==================================================
            # ITEMS
            # ==================================================

            try:

                items = json.loads(
                    order["items_json"] or "[]"
                )

            except Exception:

                items = []

            rows = []

            for item in items:

                try:

                    qty = int(
                        item.get("quantity", 0) or 0
                    )

                except (ValueError, TypeError):

                    qty = 0

                try:

                    price = float(
                        item.get("price", 0) or 0
                    )

                except (ValueError, TypeError):

                    price = 0.0

                rows.append(
                    {
                        "Medicine": item.get(
                            "name",
                            "Medicine"
                        ),

                        "Generic": item.get(
                            "generic_name",
                            "N/A"
                        ),

                        "Qty": qty,

                        "Price": (
                            f"₱{price:,.2f}"
                        ),

                        "Subtotal": (
                            f"₱{qty * price:,.2f}"
                        )
                    }
                )

            # ==================================================
            # MEDICINE TABLE
            # ==================================================

            if rows:

                st.dataframe(
                    pd.DataFrame(rows),
                    hide_index=True,
                    use_container_width=True
                )

            else:

                st.info(
                    "No medicine items found."
                )

            # ==================================================
            # ACTION BUTTONS
            # ==================================================

            a, b, c = st.columns(3)

            # ==================================================
            # APPROVE ORDER
            # ==================================================

            with a:

                if status == "Pending":

                    if st.button(
                        "✅ Approve",
                        key=f"approve_{order['id']}",
                        use_container_width=True
                    ):

                        reviewer = (
                            user.get("full_name")
                            or user.get("username")
                            or "Pharmacist/Staff"
                        )

                        try:

                            update_order_status(
                                int(order["id"]),
                                "Approved",
                                reviewer
                            )

                            st.success(
                                f"Order "
                                f"{order['request_number']} "
                                f"approved and stock automatically "
                                f"deducted."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"❌ Unable to approve order: {e}"
                            )

            # ==================================================
            # CANCEL ORDER
            # ==================================================

            with b:

                if status == "Pending":

                    if st.button(
                        "❌ Cancel Order",
                        key=f"cancel_{order['id']}",
                        use_container_width=True
                    ):

                        reviewer = (
                            user.get("full_name")
                            or user.get("username")
                            or "Pharmacist/Staff"
                        )

                        try:

                            update_order_status(
                                int(order["id"]),
                                "Cancelled",
                                reviewer
                            )

                            st.warning(
                                f"Order "
                                f"{order['request_number']} "
                                f"has been cancelled."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"❌ Unable to cancel order: {e}"
                            )

            # ==================================================
            # EDIT ORDER
            # ==================================================

            with c:

                if status == "Pending":

                    if st.button(
                        "✏️ Edit Order",
                        key=f"edit_{order['id']}",
                        use_container_width=True
                    ):
                        try:
                            edit_items = json.loads(
                                order["items_json"] or "[]"
                            )

                            if not isinstance(edit_items, list) or not edit_items:
                                st.error("This order has no medicine items to edit.")
                            else:
                                editor = (
                                    user.get("full_name")
                                    or user.get("username")
                                    or "Pharmacist/Staff"
                                )

                                edit_order_dialog(
                                    int(order["id"]),
                                    str(order["request_number"]),
                                    edit_items,
                                    editor
                                )

                        except Exception as e:
                            st.error(f"❌ Unable to open edit order: {e}")
