import pandas as pd
import os

def load_locations_from_csv(csv_path):
    """
    Loads biomineral data from a CSV file.
    The CSV is expected to have at least these columns:
        - name, lat, lon, species, image_url, info_link
    Additional columns may be used for marker colors, categories, etc.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    df = pd.read_csv(csv_path)
    
    # Simple validation check
    required_cols = {"name", "lat", "lon", "species", "image_url", "info_link"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in CSV: {missing_cols}")

    # Convert to dictionary list for easy iteration
    data_records = df.to_dict(orient='records')
    return data_records
