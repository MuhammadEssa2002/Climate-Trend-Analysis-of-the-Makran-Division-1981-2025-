# src/utils/_validation.py -- input validation for the NASA POWER requests.

# datetime parses the date string; date.today() is used to reject future end dates.
from datetime import datetime, date


# Used by NASA_power.fetch_data to check a start/end date and convert it to the format the
# API expects.
def validate_date(date_type, date_str, temporal_type):
    """
    Validate and convert a date according to the temporal type.

    Parameters
    ----------
    date_type : str
        Must be either "start_date" or "end_date".

    date_str : str
        Date in "YYYY-MM-DD" format.

    temporal_type : str, default="daily"
        Temporal resolution. Must be "daily", "monthly", or "hourly".

    Returns
    -------
    str
        "YYYYMMDD" for daily and hourly data.
        "YYYY" for monthly data.

    Raises
    ------
    ValueError
        If the date or temporal type is invalid, or if hourly data is requested before 2001.
    """

    # Argument checks: types first, then allowed values.
    if not isinstance(date_type, str):
        raise TypeError("date_type must be a string.")

    if date_type not in ("start_date", "end_date"):
        raise ValueError("date_type must be either 'start_date' or 'end_date'.")

    if not isinstance(date_str, str):
        raise TypeError("date_str must be a string.")

    if not isinstance(temporal_type, str):
        raise TypeError("temporal_type must be a string.")

    if temporal_type not in ("daily", "monthly", "hourly"):
        raise ValueError("temporal_type must be 'daily', 'monthly', or 'hourly'.")

    # Parse 'YYYY-MM-DD'; strptime also rejects impossible dates such as 2025-02-30.
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date. Expected format: 'YYYY-MM-DD'.")

    # The API has no data for the future, so end dates after today are rejected (depends on
    # the date of the run).
    if date_type == "end_date" and parsed_date > date.today():
        raise ValueError("end_date cannot be greater than the current date.")

    # --- NEW CHECK: Prevent hourly requests before 2001 ---
    if temporal_type == "hourly" and parsed_date.year < 2001:
        raise ValueError(
            f"Hourly data is only available from 2001 onwards. "
            f"You requested: {date_str} for '{date_type}'."
        )

    # Return API format
    # API date format: YYYYMMDD for daily and hourly requests, YYYY for monthly requests.
    if temporal_type in ("daily", "hourly"):
        return parsed_date.strftime("%Y%m%d")

    elif temporal_type == "monthly":
        return parsed_date.strftime("%Y")