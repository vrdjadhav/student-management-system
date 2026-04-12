"""
Excel Handler Utility
---------------------
Reads and parses attendance data from Excel files.
Expects columns: Roll_No, Date, Status.
"""

import pandas as pd
from datetime import datetime
import os


def parse_attendance_excel(filepath):
    """
    Parse an Excel file containing attendance records.

    Expected columns:
        - Roll_No : Student roll number (string)
        - Date    : Attendance date (any format parseable by pandas)
        - Status  : 'Present', 'Absent', or 'Late'

    Args:
        filepath (str): Path to the Excel file.

    Returns:
        list: List of dictionaries, each with keys 'Roll_No', 'Date', 'Status'.

    Raises:
        ValueError: If required columns are missing.
        Exception: For file read errors or invalid data.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        # Read Excel file, treating all columns as strings initially
        df = pd.read_excel(filepath, dtype=str)
    except Exception as e:
        raise Exception(f"Failed to read Excel file: {e}")

    # Validate required columns
    required_columns = {'Roll_No', 'Date', 'Status'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    # Clean data: drop rows with any NaN in required columns
    df = df.dropna(subset=['Roll_No', 'Date', 'Status'])

    records = []
    for _, row in df.iterrows():
        roll_no = str(row['Roll_No']).strip()
        if not roll_no:
            continue

        # Parse date
        try:
            date_val = pd.to_datetime(row['Date']).date()
            date_str = date_val.strftime('%Y-%m-%d')
        except Exception:
            # If date parsing fails, try to interpret as string
            date_str = str(row['Date']).strip()
            # Optionally, we could attempt to parse with a known format here
            # For simplicity, we accept any string; the database will store it as is.

        status = str(row['Status']).strip().capitalize()
        if status not in ('Present', 'Absent', 'Late'):
            # Default to 'Absent' if unknown status
            status = 'Absent'

        records.append({
            'Roll_No': roll_no,
            'Date': date_str,
            'Status': status
        })

    return records


def export_attendance_to_excel(records, filepath):
    """
    Export attendance records to an Excel file.

    Args:
        records (list): List of dictionaries with keys 'Roll_No', 'Date', 'Status'.
        filepath (str): Output file path.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        df = pd.DataFrame(records)
        df.to_excel(filepath, index=False)
        return True
    except Exception as e:
        print(f"Export failed: {e}")
        return False