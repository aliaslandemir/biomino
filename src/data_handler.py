import os
import pandas as pd
from typing import List, Dict, Any

def load_locations_from_csv(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load location data from a CSV file and return a list of dictionaries.
    Required columns: name, lat, lon, species, image_url, info_link
    Optional column: color
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    required_cols = {"name", "lat", "lon", "species", "image_url", "info_link"}

    # Let pandas guess the delimiter; handle BOM with "utf-8-sig"
    df = pd.read_csv(csv_path, encoding="utf-8-sig", engine="python", sep=None)

    # Clean BOM characters if present
    df.columns = [col.replace('\ufeff', '').strip() for col in df.columns]
    print("DEBUG COLUMNS DETECTED:", df.columns.tolist())

    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns in CSV: {missing}")

    # Ensure color column exists
    if "color" not in df.columns:
        df["color"] = "blue"

    # Convert lat/lon to float (replace comma decimals if needed)
    df["lat"] = df["lat"].astype(str).str.replace(",", ".").astype(float)
    df["lon"] = df["lon"].astype(str).str.replace(",", ".").astype(float)

    # Keep only the necessary columns
    keep_cols = ["name", "lat", "lon", "species", "image_url", "info_link", "color"]
    df = df[keep_cols]

    return df.to_dict(orient="records")
