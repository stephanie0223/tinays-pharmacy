
import pandas as pd
import sqlite3
import re

CSV_FILE = "tinays_pharmacy_200_medicines.csv"
DB_FILE = "pharmacy_system.db"

# Read CSV
df = pd.read_csv(CSV_FILE).fillna("")

# Exclude placeholder rows from the prepared sample file
df = df[
    ~df["medicine_name"].str.contains(
        "Catalog Variant", case=False, na=False
    )
]

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check whether the medicines table exists
cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type = 'table' AND name = 'medicines'
""")

if not cursor.fetchone():
    raise Exception("The medicines table does not exist.")

inserted = 0
skipped = 0

try:
    for _, row in df.iterrows():

        medicine_name = str(row["medicine_name"]).strip()
        generic = str(row["generic_name"]).strip()
        brand = str(row["brand_name"]).strip()

        # Use brand name when available
        name = (
            brand if brand and brand.lower() != "generic"
            else medicine_name
        )

        # Extract strength from medicine name
        match = re.search(
            r"\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|%)"
            r"(?:\s*/\s*\d+(?:\.\d+)?\s*(?:ml|g))?",
            medicine_name,
            re.IGNORECASE
        )

        dosage = match.group(0) if match else ""

        category = str(row["category"]).strip()
        description = str(row["description"]).strip()

        # Check existing medicine
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
    print("Placeholder rows excluded: 36")

except Exception as e:
    conn.rollback()
    print("Import failed:", e)

finally:
    conn.close()
