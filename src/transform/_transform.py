# src/transform/_transform.py -- temporal aggregation of daily data to annual or monthly
# values, with optional climatologies.

# pandas groupby/MultiIndex operations.
import pandas as pd

# Aggregation helper bound to a DataFrame and one or more columns.
# Created via Dataframe.transform(keys); use .to_annual() or .to_monthly().
class Transform:
    # data: DataFrame with a DatetimeIndex; keys: column name or list of column names.
    def __init__(self, data, keys):
        self._data = data
        self._keys = keys
        # Accept a single column name as well as a list; always work with a list internally.
        if not isinstance(self._keys, list):
            self._keys = [self._keys]

    # Aggregate to one row per calendar year.
    # method: pandas reduction applied per year, by name -- 'mean' for temperature, 'sum'
    # for precipitation totals.
    # climatology: optional second reduction ('mean', 'median', ...) applied to the annual
    # values.
    # year_group_size: with climatology, reduce within consecutive blocks of N years (e.g.
    # 10 for decades) instead of over the whole record.
    def to_annual(self, method, climatology=None, year_group_size=None):
        # 1. Transform to annual data
        annual_data = getattr(self._data[self._keys].groupby(self._data.index.year), method)()
        
        # 2. Return early if no climatology is requested
        if climatology is None:
            return annual_data
            
        # 3. Handle climatology with year grouping
        if year_group_size is not None:
            # Floor each year to the start of its block (1987 with size 10 -> 1980). Blocks
            # are aligned to multiples of the block size, so the first label can start
            # before the first year of data.
            year_bins = (annual_data.index // year_group_size) * year_group_size
            # Apply the climatology reduction within each block of years.
            climatology_data = getattr(annual_data.groupby(year_bins), climatology)()
            
            # Last year of data; caps the end of the final block label.
            max_year = annual_data.index.max()
            
            # Relabel each block as 'start-end' (e.g. '1981-1990').
            climatology_data.index = [
                f"{y}-{min(y + year_group_size - 1, max_year)}" 
                for y in climatology_data.index
            ]
            climatology_data.index.name = "Year_Range"
            
            return climatology_data
            
        # 4. Handle climatology over the entire period
        else:
            # No year grouping: one climatology value per column over the entire period.
            return getattr(annual_data, climatology)()

    # Aggregate to one row per (Year, Month).
    # Arguments as in to_annual; with climatology the result is one row per calendar month
    # (12 rows), optionally computed separately for each block of `year_group_size` years.
    def to_monthly(self, method, climatology=None, year_group_size=None):
        # 1. Transform to monthly data (one row per Year-Month)
        monthly_data = getattr(
            self._data[self._keys].groupby(
                [self._data.index.year, self._data.index.month]
            ),
            method
        )()
        # Name the two index levels.
        monthly_data.index.names = ["Year", "Month"]

        # 2. Return early if no climatology is requested
        if climatology is None:
            return monthly_data

        # Extract the index levels used for grouping below.
        years = monthly_data.index.get_level_values("Year")
        months = monthly_data.index.get_level_values("Month")

        # 3. Handle climatology with year grouping (per-month climatology within year bins)
        if year_group_size is not None:
            # Floor each year to the start of its block (same logic as in to_annual).
            year_bins = (years // year_group_size) * year_group_size
            # Per-month climatology within each block of years.
            climatology_data = getattr(
                monthly_data.groupby([year_bins, months]), climatology
            )()

            max_year = years.max()

            # Relabel blocks as 'start-end' strings; the month stays as the second index
            # level.
            climatology_data.index = pd.MultiIndex.from_tuples(
                [
                    (f"{y}-{min(y + year_group_size - 1, max_year)}", m)
                    for y, m in climatology_data.index
                ],
                names=["Year_Range", "Month"]
            )

            return climatology_data

        # 4. Handle climatology over the entire period (per calendar month, across all years)
        else:
            # Per-calendar-month climatology across all years (12 rows).
            climatology_data = getattr(monthly_data.groupby(months), climatology)()
            climatology_data.index.name = "Month"
            return climatology_data