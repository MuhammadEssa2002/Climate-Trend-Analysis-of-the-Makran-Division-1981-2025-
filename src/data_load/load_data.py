# src/data_load/load_data.py -- counterpart of Dataframe.save(): reads a saved dataset back
# into a Dataframe and restores its metadata.

# pandas readers for CSV / Parquet.
import pandas as pd

# Reads the .meta.json sidecar written by save().
import json

# Reads the single-file .pkl format.
import pickle

# Path handles the base name and suffixes.
from pathlib import Path

# Return type: the metadata-aware Dataframe subclass.
from src.core import Dataframe


# fmt: 'csv' (default), 'parquet' or 'pickle' -- must match the format used in save().
# index_col / parse_dates are passed to pandas.read_csv so the first column is restored as a
# DatetimeIndex. Additional keyword arguments go to the pandas reader.
def load_data(path, fmt="csv", index_col=0, parse_dates=True, **kwargs):
    """
    Load a DataFrame previously saved with .save(), restoring metadata.
    path: same base path used in save() (without extension)
    """
    # Base name without extension; the actual file name is derived from `fmt`.
    path = Path(path)

    # Pickle: restores the complete object, metadata included.
    if fmt == "pickle":
        pkl_path = path.with_suffix(".pkl")
        with open(pkl_path, "rb") as f:
            obj = pickle.load(f)
        # Sanity check on the unpickled object. (Only unpickle files you created or trust.)
        if not isinstance(obj, Dataframe):
            raise TypeError(f"Pickled object is {type(obj)}, expected {Dataframe}")
        return obj

    # Data file and its JSON metadata sidecar.
    data_path = path.with_suffix(f".{fmt}")
    meta_path = path.with_suffix(".meta.json")

    # Read the table; the first column (the date) becomes the index.
    if fmt == "csv":
        df = pd.read_csv(data_path, index_col=index_col, parse_dates=parse_dates, **kwargs)
    elif fmt == "parquet":
        df = pd.read_parquet(data_path, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    # The sidecar is optional: without it the metadata attributes stay None.
    meta = {}
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
            
    # Rebuild a Dataframe with the restored metadata. Only lat, lon, parameters, start_date
    # and end_date are restored; community and temporal are not stored back.
    return Dataframe(
        data=df,
        lat=meta.get("lat"),
        lon=meta.get("lon"),
        parameters=meta.get("parameters"),
        start_date=meta.get("start_date"),
        end_date=meta.get("end_date"),
    )