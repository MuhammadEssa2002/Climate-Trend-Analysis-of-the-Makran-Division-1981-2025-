# src/weather_api/nasa_power.py -- client for the NASA POWER point API
# (https://power.larc.nasa.gov/api/temporal/<daily|monthly|hourly>/point).
# NASA_power is a Dataframe that fills itself from the API: create it, call fetch_data(...),
# and optionally convert to a plain Dataframe with to_Dataframe().

# utils
from src.utils import validate_date
# Core
from src.core import Dataframe
# HTTP client used to call the NASA POWER REST API.
import requests
import pandas as pd
import numpy as np
# log
import logging
# Module logger; progress messages are emitted at INFO level.
logger = logging.getLogger(__name__)


# A Dataframe subclass with an extra fetch_data() method that downloads the data into
# itself.
class NASA_power(Dataframe):
    # Same arguments as Dataframe plus `log` (bool): print INFO-level progress messages.
    def __init__(self, data=None, community=None, lat=None, lon=None, parameters=None,
                 start_date=None, end_date=None, temporal=None, log=True, *args, **kwargs):
        super().__init__(
            data,
            community=community,
            lat=lat,
            lon=lon,
            parameters=parameters,
            start_date=start_date,
            end_date=end_date,
            temporal=temporal,
            *args,
            **kwargs
        )
        # Despite its name, _logger is just a boolean flag (not a Logger object).
        self._logger = log
        if self._logger:
            # Make logger.info() messages visible (e.g. in a notebook).
            logging.basicConfig(level=logging.INFO)

    # Download one point time series.
    # community: NASA POWER user community (the study uses 'AG').
    # lat, lon: decimal degrees.
    # parameters: comma-separated variable codes -- 'T2M', 'T2M_MAX', 'T2M_MIN' (2 m air
    # temperature: mean, maximum, minimum; deg C) and 'PRECTOTCORR' (bias-corrected
    # precipitation; mm/day).
    # start_date, end_date: 'YYYY-MM-DD'; temporal: 'daily', 'monthly' or 'hourly'.
    # On success this object becomes the downloaded table (index = Date). On a network/HTTP
    # error the exception is logged, None is returned and the object stays empty.
    def fetch_data(self, community, lat, lon, parameters, start_date, end_date, temporal):
        
        # Endpoint for single-point queries at the requested temporal resolution.
        url = f"https://power.larc.nasa.gov/api/temporal/{temporal}/point"

        # Query-string parameters; the dates are converted by validate_date to the API
        # format.
        params = {
            "parameters": parameters,
            "community": community,
            "longitude": lon,
            "latitude": lat,
            "start": validate_date("start_date", start_date, temporal),
            "end": validate_date("end_date", end_date, temporal),
            "format": "JSON"
        }

        if self._logger:
            logger.info(
                "Fetching data | Lat: %.6f | Lon: %.6f | Period: %s → %s",
                lat, lon, start_date, end_date
            )

        # Note: requests.get below is called without a timeout.
        try:
            # Send the request; raise_for_status() turns HTTP errors into exceptions handled
            # in the except block.
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Extract the dictionary containing our parameters
            raw = data.get("properties", {}).get("parameter", {})

            # 1. Convert directly to DataFrame
            df = pd.DataFrame(raw)

            # 2. Convert the index dynamically based on temporal resolution
            if temporal.lower() == 'daily':
                df.index = pd.to_datetime(df.index, format='%Y%m%d')
            elif temporal.lower() == 'monthly':
                # NASA returns 'YYYY13' for annual averages. 
                # errors='coerce' turns these into NaT so pandas doesn't crash.
                df.index = pd.to_datetime(df.index, format='%Y%m', errors='coerce')
                # Drop the annual average rows (NaT)
                df = df[df.index.notnull()]
            elif temporal.lower() == 'hourly':
                df.index = pd.to_datetime(df.index, format='%Y%m%d%H')
            else:
                # Fallback
                df.index = pd.to_datetime(df.index)

            # 3. Name the index for clarity
            df.index.name = 'Date'

            # 4. Replace NASA's missing value indicator (-999.0) with NaN
            df = df.replace(-999.0, np.nan)

            # 5. Load the fetched data into self (self IS the DataFrame)
            # super(Dataframe, self) skips Dataframe.__init__ and calls pandas'
            # DataFrame.__init__ directly, re-initialising this object's data in place (the
            # metadata is set separately just below).
            super(Dataframe, self).__init__(df)

            # 6. Store metadata now that the fetch succeeded
            self._community = community
            self._lat = lat
            self._lon = lon
            self._parameters = parameters
            self._start_date = start_date
            self._end_date = end_date
            self._temporal = temporal

            if self._logger:
                logger.info("Data fetched successfully.")

        # Network/HTTP failure: log it and return None instead of raising, so check the log
        # if a download looks empty.
        except requests.exceptions.RequestException as e:
            logger.exception(f"An error occurred while fetching the data: {e}")
            return None

            
    def to_Dataframe(self):
        """
        Returns the fetched data as a plain Dataframe instance,
        detached from NASA_power's fetching behavior and _constructor.
        """
        mdf = Dataframe(
            community=getattr(self, "_community", None),
            lat=getattr(self, "_lat", None),
            lon=getattr(self, "_lon", None),
            parameters=getattr(self, "_parameters", None),
            start_date=getattr(self, "_start_date", None),
            end_date=getattr(self, "_end_date", None),
            temporal=getattr(self, "_temporal", None),
        )
        # Fill the metadata-carrying Dataframe with a copy of the downloaded table.
        pd.DataFrame.__init__(mdf, self.copy())
        return mdf
    
    # pandas hook: derived objects (slices, copies, ...) are NASA_power instances.
    @property
    def _constructor(self):
        return NASA_power
    