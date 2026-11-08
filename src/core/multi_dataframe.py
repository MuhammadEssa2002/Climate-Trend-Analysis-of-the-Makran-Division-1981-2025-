# src/core/multi_dataframe.py -- MultiDataFrame: dictionary-like container holding one
# Dataframe per location (e.g. all tehsils of a district), plus a metadata record for each
# entry.

# NASA_power downloads time series from the NASA POWER REST API.
from src.weather_api import NASA_power
# Loader for datasets saved to disk (underscore avoids a clash with the load_data method
# below).
from src.data_load import load_data as _load_data

# Used by MultiDataFrame.copy() for deep copies.
import copy as _copy

# Entries are keyed by integers 0, 1, 2, ... in the order they were added.
# mdf[i] gives the Dataframe of entry i; mdf.meta_data[i] gives its metadata (name, lat,
# lon, ...).
class MultiDataFrame:
    # Start empty and set the default query settings used by fetch_and_add() (change them
    # with the set_default_* methods).
    def __init__(self):
        # key -> Dataframe
        self._multi_data = {}
        # key -> metadata dictionary
        self._meta_data = {}
        # Next key to hand out. The counter only increases (keys are not reused after
        # remove()).
        self._keys = 0
        # Study defaults: 1981-01-01 to 2025-12-31, daily data, mean/max/min 2 m
        # temperature, NASA POWER community 'AG' (agroclimatology).
        self._default_start_date = "1981-01-01"
        self._default_end_date = "2025-12-31"
        self._default_parameters = "T2M,T2M_MAX,T2M_MIN"
        self._default_community = "AG"
        self._default_temporal = "daily"

    # Download one point (lat, lon in decimal degrees) from NASA POWER and store it under
    # the next key.
    # name: free-text label for the location (used later in titles/legends).
    # Any argument left as None falls back to the defaults above. Requires internet access.
    def fetch_and_add(self, lat, lon, community=None, name=None, parameters=None,
                       start_date=None, end_date=None,temporal=None):
        
        # Fall back to the default for every argument that was not supplied.
        community = community or self._default_community
        parameters = parameters or self._default_parameters
        start_date = start_date or self._default_start_date
        end_date = end_date or self._default_end_date
        temporal = temporal or self._default_temporal

        # Create the downloader and request the data from the API.
        nasa_df = NASA_power()
        nasa_df.fetch_data(community = community ,lat=lat, lon=lon, parameters=parameters,
                            start_date=start_date, end_date=end_date, temporal = temporal)

        # Store the result as a plain Dataframe (detached from the downloader class).
        self._multi_data[self._keys] = nasa_df.to_Dataframe()
        # Record the query settings for this entry.
        self._meta_data[self._keys] = {
            "name": name, "community":community , "lat": lat, "lon": lon,
            "parameters": parameters, "start_date": start_date, "end_date": end_date, "temporal":temporal,
        }
        # Advance the key counter.
        self._keys += 1

    # Dict-style read access: mdf[0] -> Dataframe stored under key 0 (KeyError if absent).
    def __getitem__(self, key):
        if key in self._multi_data:
            return self._multi_data[key]
        else:
            raise KeyError(f"Key '{key}' not found.")

    # Dict-style replacement of an EXISTING entry, e.g. mdf[i] =
    # mdf[i].transform(...).to_annual(...).
    # New entries must be added with fetch_and_add / add_data / load_data. The metadata
    # record is left unchanged.
    def __setitem__(self, key, newvalue):
        if key not in self._multi_data:
            raise KeyError(f"Key '{key}' not found - use fetch_and_add to add new entries.")
        self._multi_data[key] = newvalue

    # Integer keys of all stored entries (lets notebooks write `for i in mdf.keys()`).
    def keys(self):
        return self._multi_data.keys()

    # Setters for the default query settings used by fetch_and_add(): community, start date,
    # end date, variables (parameters) and temporal resolution.
    def set_default_community(self,value):
        self._default_community = value

    def set_default_start_date(self,value):
        self._default_start_date = value

    def set_default_end_date(self,value):
        self._default_end_date = value

    def set_default_parameters(self,value):
        self._default_parameters = value

    def set_default_temporal(self,value):
        self._default_temporal = value


    # Internal helper: store an existing Dataframe under the next key and build its metadata
    # from the Dataframe's own attributes. (This record has no 'community' or 'temporal'
    # entry.)
    def _register(self, data, name):
        self._meta_data[self._keys] = {
            "name": name, "lat": data.lat, "lon": data.lon,
            "parameters": data.parameters,
            "start_date": data.start_date, "end_date": data.end_date,
        }
        self._multi_data[self._keys] = data
        self._keys += 1

    # Load a dataset previously saved with Dataframe.save() and add it as a new entry.
    # Extra arguments are passed to src.data_load.load_data (path, fmt, ...).
    def load_data(self,name = None,*args,**kwargs):
        data = _load_data(*args,**kwargs)
        self._register(data, name)

    # Add an in-memory Dataframe (for example a district average) as a new entry.
    def add_data(self,data,name = None):
        self._register(data, name)

    # Delete an entry and its metadata. The remaining keys are NOT renumbered.
    def remove(self, key):
        if key not in self._multi_data:
            raise KeyError(f"Key '{key}' not found.")
        del self._multi_data[key]
        del self._meta_data[key]

    # Read-only access to the metadata and data dictionaries.
    @property
    def meta_data(self):
        return self._meta_data

    @property
    def data(self):
        return self._multi_data

    # Independent copy of the container. The notebooks copy before transforming so the
    # downloaded raw daily data stays untouched.
    # deep=True also duplicates every DataFrame and metadata record; deep=False copies only
    # the dictionaries (the DataFrames are shared).
    def copy(self, deep=True):
        
        new_obj = MultiDataFrame()

        new_obj._default_start_date = self._default_start_date
        new_obj._default_end_date = self._default_end_date
        new_obj._default_parameters = self._default_parameters
        new_obj._default_community = self._default_community
        new_obj._default_temporal = self._default_temporal
        # Keep the key counter so new entries never reuse an existing key.
        new_obj._keys = self._keys

        # Deep copy: duplicate every DataFrame and metadata record.
        if deep:
            new_obj._multi_data = _copy.deepcopy(self._multi_data)
            new_obj._meta_data = _copy.deepcopy(self._meta_data)
        else:
            new_obj._multi_data = dict(self._multi_data)
            new_obj._meta_data = {k: dict(v) for k, v in self._meta_data.items()}

        return new_obj