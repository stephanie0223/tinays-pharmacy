import sqlite3
import hashlib
import pandas as pd
import json
from datetime import datetime

DB_NAME = "pharmacy_system.db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db_connection():

    conn = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================================
# PASSWORD HASH
# ==========================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

def init_db():

    conn = get_db_connection()
    cursor = conn.cursor()

    # ======================================================
    # USERS
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL,

            full_name TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================================
    # MEDICINES
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            generic_name TEXT,

            brand_name TEXT,

            category TEXT,

            dosage_strength TEXT,

            price REAL NOT NULL,

            description TEXT
        )
    """)

    # ======================================================
    # SUPPLIERS
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            contact_person TEXT,

            phone TEXT,

            email TEXT,

            address TEXT
        )
    """)

    # ======================================================
    # INVENTORY BATCHES
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_batches (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            medicine_id INTEGER NOT NULL,

            supplier_id INTEGER,

            batch_number TEXT NOT NULL,

            quantity INTEGER NOT NULL,

            expiration_date DATE NOT NULL,

            received_date TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (medicine_id)
                REFERENCES medicines(id),

            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(id)
        )
    """)

    # ======================================================
    # STOCK TRANSACTIONS
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            medicine_id INTEGER NOT NULL,

            batch_id INTEGER,

            transaction_type TEXT NOT NULL,

            quantity INTEGER NOT NULL,

            notes TEXT,

            user_id INTEGER,

            timestamp TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (medicine_id)
                REFERENCES medicines(id),

            FOREIGN KEY (batch_id)
                REFERENCES inventory_batches(id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    # ======================================================
    # CUSTOMER INQUIRIES
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_inquiries (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_query TEXT NOT NULL,

            bot_response TEXT NOT NULL,

            matched_medicine_id INTEGER,

            timestamp TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (matched_medicine_id)
                REFERENCES medicines(id)
        )
    """)

    # ======================================================
    # AUDIT TRAIL
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            username TEXT,

            action TEXT NOT NULL,

            details TEXT,

            timestamp TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    # ======================================================
    # CUSTOMER ORDERS
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_orders (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            request_number TEXT UNIQUE NOT NULL,

            customer_name TEXT
                DEFAULT 'Walk-in Customer',

            items TEXT NOT NULL,

            total_amount REAL NOT NULL,

            status TEXT
                DEFAULT 'PENDING',

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            processed_by INTEGER,

            processed_at TIMESTAMP,

            FOREIGN KEY (processed_by)
                REFERENCES users(id)
        )
    """)

    # ======================================================
    # DEFAULT ADMIN
    # ======================================================

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        ("admin",)
    )

    if not cursor.fetchone():

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                password,
                role,
                full_name
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "admin",
                hash_password("admin123"),
                "Administrator",
                "Tinay Riceplate"
            )
        )

    # ======================================================
    # DEFAULT PHARMACIST
    # ======================================================

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        ("pharmacist1",)
    )

    if not cursor.fetchone():

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                password,
                role,
                full_name
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "pharmacist1",
                hash_password("pharma123"),
                "Pharmacist",
                "Kristine"
            )
        )

    conn.commit()
    conn.close()


# ==========================================================
# AUDIT LOG
# ==========================================================

def log_audit(
    user_id,
    username,
    action,
    details=""
):

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO audit_trail
        (
            user_id,
            username,
            action,
            details
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            username,
            action,
            details
        )
    )

    conn.commit()
    conn.close()


# ==========================================================
# MEDICINE STOCK SUMMARY
# ==========================================================

def get_medicine_stock_summary():

    conn = get_db_connection()

    query = """
        SELECT

            m.id,

            m.name,

            m.generic_name,

            m.brand_name,

            m.category,

            m.dosage_strength,

            m.price,

            COALESCE(
                SUM(
                    CASE
                        WHEN b.quantity > 0
                        THEN b.quantity
                        ELSE 0
                    END
                ),
                0
            ) AS available_stock

        FROM medicines m

        LEFT JOIN inventory_batches b
            ON m.id = b.medicine_id

        GROUP BY

            m.id,
            m.name,
            m.generic_name,
            m.brand_name,
            m.category,
            m.dosage_strength,
            m.price

        ORDER BY
            m.name ASC
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df


# ==========================================================
# GET SINGLE MEDICINE STOCK
# ==========================================================

def get_medicine_stock(medicine_id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            m.id,

            m.name,

            m.generic_name,

            m.brand_name,

            m.category,

            m.dosage_strength,

            m.price,

            COALESCE(
                SUM(
                    CASE
                        WHEN b.quantity > 0
                        THEN b.quantity
                        ELSE 0
                    END
                ),
                0
            ) AS available_stock

        FROM medicines m

        LEFT JOIN inventory_batches b
            ON m.id = b.medicine_id

        WHERE m.id = ?

        GROUP BY

            m.id,
            m.name,
            m.generic_name,
            m.brand_name,
            m.category,
            m.dosage_strength,
            m.price
        """,
        (medicine_id,)
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return dict(result)

    return None


# ==========================================================
# CREATE CUSTOMER ORDER
# ==========================================================

def create_customer_order(
    request_number,
    cart,
    total_amount,
    customer_name="Walk-in Customer"
):

    conn = get_db_connection()

    items_json = json.dumps(
        cart,
        default=str
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO customer_orders
        (
            request_number,
            customer_name,
            items,
            total_amount,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            request_number,
            customer_name,
            items_json,
            float(total_amount),
            "PENDING"
        )
    )

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return order_id


# ==========================================================
# GET PENDING CUSTOMER ORDERS
# ==========================================================

def get_pending_orders():

    conn = get_db_connection()

    orders = conn.execute(
        """
        SELECT
            id,
            request_number,
            customer_name,
            items,
            total_amount,
            status,
            created_at,
            processed_by,
            processed_at
        FROM customer_orders
        WHERE status = 'PENDING'
        ORDER BY created_at ASC
        """
    ).fetchall()

    conn.close()

    return orders


# ==========================================================
# GET ALL CUSTOMER ORDERS
# ==========================================================

def get_customer_orders():

    conn = get_db_connection()

    orders = conn.execute(
        """
        SELECT
            id,
            request_number,
            customer_name,
            items,
            total_amount,
            status,
            created_at,
            processed_by,
            processed_at
        FROM customer_orders
        ORDER BY created_at DESC
        """
    ).fetchall()

    conn.close()

    return orders


# ==========================================================
# GET PENDING ORDER COUNT
# ==========================================================

def get_pending_order_count():

    conn = get_db_connection()

    result = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM customer_orders
        WHERE status = 'PENDING'
        """
    ).fetchone()

    conn.close()

    return result["count"]


# ==========================================================
# UPDATE CUSTOMER ORDER STATUS
# ==========================================================

def update_order_status(
    order_id,
    status,
    user_id=None
):

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE customer_orders

        SET
            status = ?,
            processed_by = ?,
            processed_at = CURRENT_TIMESTAMP

        WHERE id = ?
        """,
        (
            status,
            user_id,
            order_id
        )
    )

    conn.commit()
    conn.close()


# ==========================================================
# GET ONE CUSTOMER ORDER
# ==========================================================

def get_customer_order(order_id):

    conn = get_db_connection()

    order = conn.execute(
        """
        SELECT
            id,
            request_number,
            customer_name,
            items,
            total_amount,
            status,
            created_at,
            processed_by,
            processed_at
        FROM customer_orders
        WHERE id = ?
        """,
        (order_id,)
    ).fetchone()

    conn.close()

    if order:
        return dict(order)

    return None