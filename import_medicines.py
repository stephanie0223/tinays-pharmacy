
import pandas as pd
import sqlite3
import re
import os

# Get the folder where this Python file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_FILE = os.path.join(BASE_DIR, "tinays_pharmacy_200_medicines.csv")
DB_FILE = os.path.join(BASE_DIR, "pharmacy_system.db")

# Check if CSV file exists
if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(
        f"CSV file not found: {CSV_FILE}\n"
        "Place the CSV file in the same folder as import_medicines.py."
    )

# Read CSV
df = pd.read_csv(CSV_FILE).fillna("")

# Exclude placeholder rows
df = df[
    ~df["medicine_name"].astype(str).str.contains(
        "Catalog Variant", case=False, na=False
    )
]

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    # Check whether medicines table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'medicines'
    """)

    if not cursor.fetchone():
        raise Exception("The medicines table does not exist.")

    inserted = 0
    skipped = 0

    for _, row in df.iterrows():

        medicine_name = str(row["medicine_name"]).strip()
        generic = str(row["generic_name"]).strip()
        brand = str(row["brand_name"]).strip()

        # Keep the medicine name from the CSV
        name = medicine_name

        # Extract dosage strength
        match = re.search(
            r"\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|%)"
            r"(?:\s*/\s*\d+(?:\.\d+)?\s*(?:ml|g))?",
            medicine_name,
            re.IGNORECASE
        )

        dosage = match.group(0) if match else ""

        category = str(row["category"]).strip()
        description = str(row["description"]).strip()

        # Check for existing medicine
        existing = cursor.execute("""
            SELECT id FROM medicines
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
            AND LOWER(TRIM(COALESCE(generic_name, '')))
                = LOWER(TRIM(?))
            AND LOWER(TRIM(COALESCE(dosage_strength, '')))
                = LOWER(TRIM(?))
        """, (name, generic, dosage)).fetchone()

        if existing:
            skipped += 1
            continue

        # Insert medicine
        cursor.execute("""
            INSERT INTO medicines (
                name,
                generic_name,
                brand_name,
                category,
                dosage_strength,
                price,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            generic,
            brand,
            category,
            dosage,
            float(row["price"] or 0),
            description
        ))

        inserted += 1

    conn.commit()

    print("================================")
    print("MEDICINE IMPORT COMPLETED")
    print("================================")
    print("Successfully imported:", inserted)
    print("Skipped duplicates:", skipped)
    print("Placeholder rows excluded:", 200 - len(df))

except Exception as e:
    conn.rollback()
    print("Import failed:", e)

finally:
    conn.close()
