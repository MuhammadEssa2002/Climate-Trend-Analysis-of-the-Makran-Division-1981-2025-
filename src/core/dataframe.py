# src/core/dataframe.py -- Dataframe: a pandas DataFrame subclass that carries the query
# metadata (community, latitude/longitude, variables, period, temporal resolution) together
# with the data, and offers convenience methods for trend tests, aggregation, plotting and
# saving.


# Dataframe subclasses pandas.DataFrame.
import pandas as pd

# Mann-Kendall trend tests (thin wrapper around pymannkendall).
from src.trend import Find_Trend

# Temporal aggregation helper (daily -> annual / monthly, plus climatologies).
from src.transform import Transform

# Plotting helper with optional trend-line overlay.
from src.chart import Chart

# json: the metadata sidecar file (<name>.meta.json) written by save().
import json

# pickle: alternative persistence format that stores data and metadata in a single file.
import pickle

# Path handles file names and suffixes.
from pathlib import Path

# Type hints for optional arguments.
from typing import Optional

# Matplotlib imports (Axes is only used as a type hint in chart()).
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

# pandas DataFrame with extra attributes describing where the data came from.
# Typically obtained from NASA_power.to_Dataframe() or from the district-averaging code in
# the notebooks.
class Dataframe(pd.DataFrame):

    
    # Names of the custom attributes that pandas should carry over to derived objects
    # (slices, copies, ...).
    _metadata = ["_community", "_lat", "_lon", "_parameters", "_start_date", "_end_date","_temporal"]

    # data: anything pandas.DataFrame accepts.
    # community: NASA POWER user community (the notebooks use 'AG').
    # lat, lon: location in decimal degrees.
    # parameters: comma-separated NASA POWER variable codes, e.g. 'T2M,T2M_MAX,T2M_MIN'.
    # start_date, end_date: requested period ('YYYY-MM-DD'); temporal: 'daily', 'monthly' or
    # 'hourly'.
    def __init__(self, data=None, community=None, lat=None, lon=None, parameters=None,
                 start_date=None, end_date=None, temporal=None, *args, **kwargs):
        # Initialise the underlying pandas DataFrame first.
        super().__init__(data, *args, **kwargs)
        # Store the metadata as private attributes (exposed read-only through the properties
        # at the bottom).
        self._community = community
        self._lat = lat
        self._lon = lon
        self._parameters = parameters
        self._start_date = start_date
        self._end_date = end_date
        self._temporal = temporal

    # pandas hook: operations that build a new frame (slicing, arithmetic, copy, ...) return
    # this subclass instead of a plain pandas.DataFrame, so the methods below stay
    # available.
    @property
    def _constructor(self):
        return Dataframe

    # Mann-Kendall trend analysis for one column name or a list of column names.
    # Returns a Find_Trend object; call .mann_kendall(method) on it to run the test(s).
    def find_trend(self, keys:str):
        return Find_Trend(data=self, keys=keys)

    # Remove every 29 February row so that all years have 365 days (required before
    # computing heatwave days).
    # inplace=True modifies this object and returns None; otherwise a filtered copy is
    # returned.
    def drop_leap_days(self, inplace:bool=False):
        # Boolean mask: True for all rows that are NOT 29 February.
        mask = ~((self.index.month == 2) & (self.index.day == 29))
        # Keep only the non-leap-day rows.
        result = self.loc[mask]
        # Replace this object's data with the filtered rows (uses pandas' private
        # _update_inplace).
        if inplace:
            self._update_inplace(result)
            return None
        else:
            return result
        
    # Return a Transform helper for the given column(s) -> .to_annual(...) /
    # .to_monthly(...).
    # Note: this method name shadows pandas.DataFrame.transform for this subclass.
    def transform(self,keys:str):
        return Transform(self,keys)

    # Plot one column.
    # key: column to plot; ct: chart type ('line', 'bar', ...); ax: optional Matplotlib
    # Axes; st: draw the data series now (True) or only create the helper (False).
    # Extra arguments go to Matplotlib. Returns a Chart object; call .mann_kendall(...) on
    # it to add a trend line.
    def chart(self,key:str,ct:str="line",ax:Optional[Axes]=None,st:bool=True,*args,**kwargs):
        return Chart(chart_type = ct,
                    data = self,
                    key = key,
                    ax = ax,
                    show_chart = st,
                    *args,
                    **kwargs)

    def save(self, path:str, fmt:str="csv", **kwargs):
        """
        Save the DataFrame plus its metadata.
        path: base path WITHOUT extension, e.g. 'data/karachi_temp'
        fmt: 'csv', 'parquet', or 'pickle'
        """
        # `path` is a base name without extension; the suffix is added according to `fmt`.
        path = Path(path)

        # Pickle: one .pkl file with the complete object (data + metadata).
        if fmt == "pickle":
            # Pickle preserves the full object (data + metadata) in one file
            pkl_path = path.with_suffix(".pkl")
            with open(pkl_path, "wb") as f:
                pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
            return pkl_path

        # CSV/Parquet: two files, the data itself and a .meta.json sidecar holding the
        # metadata.
        data_path = path.with_suffix(f".{fmt}")
        meta_path = path.with_suffix(".meta.json")

        # Write the data table in the requested format.
        if fmt == "csv":
            self.to_csv(data_path, **kwargs)
        elif fmt == "parquet":
            self.to_parquet(data_path, **kwargs)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        # Metadata written to the JSON sidecar (dates converted to strings so they are
        # JSON-serialisable).
        meta = {
            "community": self._community,
            "lat": self._lat,
            "lon": self._lon,
            "parameters": self._parameters,
            "start_date": str(self._start_date) if self._start_date is not None else None,
            "end_date": str(self._end_date) if self._end_date is not None else None,
            "temporal": self._temporal,
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        return data_path, meta_path

    # Read-only accessors for the stored query metadata.
    @property
    def community(self):
        return self._community
    
    @property
    def lat(self):
        return self._lat

    @property
    def lon(self):
        return self._lon

    @property
    def parameters(self):
        return self._parameters

    @property
    def start_date(self):
        return self._start_date

    @property
    def end_date(self):
        return self._end_date

    @property
    def temporal(self):
        return self._temporal

