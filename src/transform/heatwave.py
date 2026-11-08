# src/transform/heatwave.py -- annual number of heatwave days from daily maximum temperature
# (T2M_MAX).
# Definition implemented below: a heatwave day is a day that belongs to a run of at least 3
# consecutive 'hot' days; a hot day is one whose T2M_MAX anomaly (observation minus the
# 1981-2010 mean seasonal cycle) exceeds the 90th percentile of anomalies for that day of
# the year, estimated from a +/-7-day window over 1981-2010. The baseline years, window
# width, percentile and minimum run length are hard-coded.

# pandas: dates, time deltas, resampling.
import pandas as pd
# NumPy: percentile calculation.
import numpy as np


def heatwave(df_data):
    """
    Annual heatwave-day counts using the deseasonalized TX90p method.

    df_data : DataFrame with a daily DatetimeIndex (29 Feb already removed)
              and a column "T2M_MAX".
    Returns : DataFrame indexed by year with column "Total_Heatwave_Days".
    """
    df_data = df_data.copy()  # do not modify the caller's DataFrame

    # ------------------------------------------------------------------
    # STEP 1: Mean seasonal cycle of T2M_MAX over the 1981-2010 baseline
    # ------------------------------------------------------------------
    baseline_data = df_data.loc["1981-01-01":"2010-12-31"]
    # Mean T2M_MAX for every day-of-year (1..366) over the baseline = climatological
    # seasonal cycle.
    # Days are grouped by day-of-year number; because 29 Feb rows were removed but
    # day-of-year numbering was not recomputed, 1 March is day 61 in leap years and day 60
    # otherwise.
    daily_means = baseline_data.groupby(baseline_data.index.dayofyear)["T2M_MAX"].mean()

    # Anomalies for the whole record
    # Add day-of-year, seasonal mean and anomaly (observation - seasonal mean) for the whole
    # 1981-2025 record.
    df_data["Day_of_Year"] = df_data.index.dayofyear
    df_data["Climatological_Mean"] = df_data["Day_of_Year"].map(daily_means)
    df_data["T_Anomaly"] = df_data["T2M_MAX"] - df_data["Climatological_Mean"]

    # Baseline slice that now contains the anomaly column
    baseline_data = df_data.loc["1981-01-01":"2010-12-31"]

    # ------------------------------------------------------------------
    # STEP 2: 90th-percentile threshold on the anomalies (15-day window)
    # ------------------------------------------------------------------
    # Result container: day-of-year -> 90th percentile of the anomaly.
    daily_anomaly_thresholds = {}

    # For each day-of-year, pool the anomalies from a 15-day window (-7..+7 days) around
    # that day in each of the 30 baseline years (up to 30 x 15 = 450 values) and take their
    # 90th percentile.
    for day in range(1, 367):
        window_values = []
        for year in range(1981, 2011):
            for offset in range(-7, 8):  # -7 ... +7 days
                # Calendar date lying `offset` days from day-of-year `day` of this year.
                target_date = pd.to_datetime(f"{year}-01-01") + pd.Timedelta(days=(day - 1 + offset))
                # Skip dates that are not in the baseline (removed leap days, or before 1981
                # / after 2010), so windows at the ends of the baseline contain fewer
                # values.
                if target_date in baseline_data.index:
                    window_values.append(baseline_data.loc[target_date, "T_Anomaly"])

        # 90th percentile of the pooled anomalies (NaN if the window is empty).
        if window_values:
            daily_anomaly_thresholds[day] = np.percentile(window_values, 90)
        else:
            daily_anomaly_thresholds[day] = np.nan

    # Lookup table: day-of-year -> anomaly threshold.
    anomaly_threshold_series = pd.Series(daily_anomaly_thresholds)

    # ------------------------------------------------------------------
    # STEP 3: Hot days and heatwave days (runs of >= 3 consecutive hot days)
    # ------------------------------------------------------------------
    # Look up the threshold that applies to each day (by day-of-year).
    df_data["Threshold_90th_Anomaly"] = df_data["Day_of_Year"].map(anomaly_threshold_series)
    # Hot day: anomaly strictly greater than that day's 90th-percentile threshold.
    df_data["Is_Hot_Day"] = df_data["T_Anomaly"] > df_data["Threshold_90th_Anomaly"]

    # Every non-hot day starts a new group; the hot days after it form one run
    run_id = (~df_data["Is_Hot_Day"]).cumsum()
    # Number of hot days in the run each row belongs to.
    run_length = df_data["Is_Hot_Day"].groupby(run_id).transform("sum")

    # A heatwave day is a hot day that belongs to a run of 3 or more hot days
    df_data["Is_Heatwave_Day"] = df_data["Is_Hot_Day"] & (run_length >= 3)

    # ------------------------------------------------------------------
    # STEP 4: Annual aggregation
    # ------------------------------------------------------------------
    # Count heatwave days per calendar year ('YE' = year-end frequency alias, pandas >=
    # 2.2).
    yearly = df_data["Is_Heatwave_Day"].resample("YE").sum().to_frame()
    # Name the output column.
    yearly.columns = ["Total_Heatwave_Days"]
    # Use the integer year (1981 ... 2025) as the index.
    yearly.index = yearly.index.year
    return yearly