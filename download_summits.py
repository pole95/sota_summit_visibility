import csv
import sqlite3
from datetime import datetime
import requests

# Connect to SQLite database (or create it)
conn = sqlite3.connect("summits.db")
cursor = conn.cursor()

# Create the schema (Associations, Regions, Summits)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS Associations (
    AssociationID INTEGER PRIMARY KEY,
    AssociationCode TEXT UNIQUE,
    AssociationName TEXT
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS Regions (
    RegionID INTEGER PRIMARY KEY,
    RegionCode TEXT,
    RegionName TEXT,
    AssociationID INTEGER,
    UNIQUE(RegionCode, AssociationID),
    FOREIGN KEY (AssociationID) REFERENCES Associations(AssociationID)
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS Summits (
    SummitCode TEXT PRIMARY KEY,
    SummitNumber INTEGER,
    SummitName TEXT,
    Elevation INTEGER,
    Longitude REAL,
    Latitude REAL,
    RegionID INTEGER,
    AssociationID INTEGER,
    FOREIGN KEY (RegionID) REFERENCES Regions(RegionID),
    FOREIGN KEY (AssociationID) REFERENCES Associations(AssociationID)
)
"""
)


def convert_date(date_str):
    if date_str is None:
        return datetime.min
    return datetime.strptime(date_str, "%d/%m/%Y")


r = requests.get("https://www.sotadata.org.uk/summitslist.csv")
content = r.content.decode("utf-8").splitlines()
reader = csv.DictReader(content[1:])

for row in reader:
    # Extract data from SummitCode
    summit_code_parts = row["SummitCode"].split("/")
    association_code = summit_code_parts[0]
    region_summit = summit_code_parts[1].split("-")
    region_code = region_summit[0]
    summit_number = int(region_summit[1])
    is_active = convert_date(row["ValidTo"]) > datetime.now()
    if not is_active:
        continue
    # Insert into Associations table
    cursor.execute(
        """
        INSERT OR IGNORE INTO Associations (AssociationCode, AssociationName)
        VALUES (?, ?)
    """,
        (association_code, row["AssociationName"]),
    )

    # Fetch the AssociationID
    cursor.execute("SELECT AssociationID FROM Associations WHERE AssociationCode = ?", (association_code,))
    association_id = cursor.fetchone()[0]

    # Insert into Regions table
    cursor.execute(
        """
        INSERT OR IGNORE INTO Regions (RegionCode, RegionName, AssociationID)
        VALUES (?, ?, ?)
    """,
        (region_code, row["RegionName"], association_id),
    )

    # Fetch the RegionID
    cursor.execute(
        "SELECT RegionID FROM Regions WHERE RegionCode = ? AND AssociationID = ?", (region_code, association_id)
    )
    region_id = cursor.fetchone()[0]

    # Insert into Summits table
    cursor.execute(
        """
        INSERT OR REPLACE INTO Summits
        (SummitCode, SummitNumber, SummitName, Elevation, Longitude, Latitude, RegionID, AssociationID)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            row["SummitCode"],
            summit_number,
            row["SummitName"],
            int(row["AltM"]),
            float(row["Longitude"]),
            float(row["Latitude"]),
            region_id,
            association_id,
        ),
    )

# Commit changes and close the connection
conn.commit()
conn.close()

print("Summit data successfully inserted into SQLite database.")
