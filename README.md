# Climate Trend Analysis of the Makran Division (1981-2025)

Code and notebooks for reproducing the temperature, rainfall and heatwave trend analysis of the Makran region of Balochistan, Pakistan, based on daily NASA POWER data. For every location (tehsil or sub-tehsil) the workflow downloads the daily series, aggregates it to annual values, and tests for monotonic trends with the Modified Mann-Kendall test and Sen's slope.

> **Paper:** [TODO: full title, authors, journal, DOI]
> **Archived version:** [TODO: Zenodo DOI, optional but recommended for publication]

## Contents

- [What the analysis does](#what-the-analysis-does)
- [Study locations](#study-locations)
- [Data](#data)
- [Methods](#methods)
- [Repository structure](#repository-structure)
- [Installation](#installation)
- [Reproducing the results](#reproducing-the-results)
- [Using the `src` package](#using-the-src-package)
- [Freezing the downloaded data](#freezing-the-downloaded-data)
- [Reproducibility notes](#reproducibility-notes)
- [Citation, data acknowledgement and license](#citation-data-acknowledgement-and-license)

## What the analysis does

For each study area the notebooks produce four results, in this order:

1. Annual mean air temperature (T2M) for every location, plotted together.
2. Annual mean temperature trend per location (Modified Mann-Kendall test, Sen's slope line).
3. Annual rainfall total (PRECTOTCORR) trend per location.
4. Annual heatwave-day count trend per location.

Two further notebooks repeat the rainfall and heatwave analyses for the whole Makran Division, using one area-averaged series per study area.

## Study locations

All coordinates are in decimal degrees (WGS84) and are taken directly from the notebooks. The administrative level is the label used in the figure legends.

| Study area (notebook) | Location | Level | Latitude | Longitude |
|---|---|---|---|---|
| Kech (`Turbat.ipynb`) | Turbat | Tehsil | 26.004168 | 63.060555 |
| | Dasht | Sub-tehsil | 25.709777 | 62.622079 |
| | Buleda | Sub-tehsil | 26.3985 | 62.9206 |
| | Hoshab | Sub-tehsil | 26.0155 | 63.8818 |
| | Balnigor | Sub-tehsil | 25.832619 | 62.261213 |
| Gwadar (`Gawadar.ipynb`) | Gwadar | Tehsil | 25.12648 | 62.3225 |
| | Jiwani | Tehsil | 25.0504 | 61.7420 |
| | Pasni | Tehsil | 25.2624 | 63.4713 |
| | Ormara | Tehsil | 25.2144 | 64.6333 |
| | Suntar | Sub-tehsil | 25.5022 | 61.9817 |
| Panjgur (`Panjgur.ipynb`) | Panjgur | Tehsil | 26.9683 | 64.1014 |
| | Parome | Tehsil | 26.5670 | 63.3850 |
| | Gowargo | Tehsil | 26.7830 | 64.2670 |
| | Gichk | Sub-tehsil | 26.6670 | 64.5170 |
| Tump (`Tump.ipynb`) | Tump | Tehsil | 26.0969 | 62.3654 |
| | Mand | Sub-tehsil | 26.37 | 61.75 |

## Data

No data files are stored in this repository. Everything is downloaded at run time from the [NASA POWER](https://power.larc.nasa.gov/) point API (`https://power.larc.nasa.gov/api/temporal/daily/point`).

| Setting | Value |
|---|---|
| Source | NASA POWER (Prediction Of Worldwide Energy Resources), meteorological data derived from the MERRA-2 reanalysis |
| Temporal resolution | Daily |
| Period | 1981-01-01 to 2025-12-31 |
| Community | `AG` (agroclimatology) |
| Temperature variables | `T2M`, `T2M_MAX`, `T2M_MIN` (2 m air temperature: mean, maximum, minimum, in degrees C) |
| Precipitation variable | `PRECTOTCORR` (bias-corrected precipitation, mm/day) |
| Missing values | NASA's fill value (-999) is converted to `NaN` |
| Data retrieved on | [TODO: YYYY-MM-DD] |

NASA POWER can be reprocessed and updated over time. To make the published numbers exactly reproducible, see [Freezing the downloaded data](#freezing-the-downloaded-data).

## Methods

**Annual aggregation.** Daily mean temperature (`T2M`) is averaged per calendar year. Daily precipitation (`PRECTOTCORR`) is summed per calendar year to give mm/year. This gives 45 annual values (1981-2025) per location.

**Trend test.** Trends are tested with the Modified Mann-Kendall test with the Yue-Wang correction for serial correlation (`yue_wang_modification_test` from [`pymannkendall`](https://github.com/mmhs013/pyMannKendall)). The slope drawn on each figure is Sen's slope in units per year, and the intercept refers to a 0-based time step (0 = 1981). The significance level is the `pymannkendall` default (alpha = 0.05); the full test result (trend, h, p, z, Tau, s, var_s, slope, intercept) is printed below each figure cell.

**Heatwave days** (`src/transform/heatwave.py`). Computed from daily maximum temperature (`T2M_MAX`) with a deseasonalized TX90p-style procedure:

1. Remove 29 February from the series.
2. Compute the mean seasonal cycle of `T2M_MAX` per day of year over the baseline 1981-2010, and subtract it from the whole record to obtain daily anomalies.
3. For each day of year, take the 90th percentile of the baseline anomalies pooled over a 15-day window (+/- 7 days) across the 30 baseline years.
4. A day is *hot* if its anomaly exceeds the threshold of its day of year. A *heatwave day* is a hot day that is part of a run of at least 3 consecutive hot days.
5. Count heatwave days per calendar year.

The baseline period, window width, percentile and minimum run length are fixed in the code.

[TODO: add the reference for the heatwave definition used in the manuscript.]

**Area-level series** (`combined_heatwave.ipynb`, `combined_rain.ipynb`). The daily series of all locations in a study area are averaged with equal weights (5 locations for Kech and Gwadar, 4 for Panjgur, 2 for Tump), and the analysis above is applied to the averaged series.

## Repository structure

```
.
├── README.md
├── deeplearning.mplstyle        Matplotlib style sheet used for all figures
├── Turbat.ipynb                 Kech study area: temperature, rainfall, heatwave
├── Gawadar.ipynb                Gwadar study area
├── Panjgur.ipynb                Panjgur study area
├── Tump.ipynb                   Tump study area
├── combined_rain.ipynb          Annual rainfall trends, area-averaged, whole division
├── combined_heatwave.ipynb      Heatwave-day trends, area-averaged, whole division
└── src/                         Local analysis package (imported as `import src as mk`)
    ├── core/                    Dataframe (pandas subclass with metadata), MultiDataFrame
    ├── weather_api/             NASA POWER client (nasa_power.py)
    ├── data_load/               Reload data saved with Dataframe.save()
    ├── transform/               Annual/monthly aggregation (_transform.py), heatwave index (heatwave.py)
    ├── trend/                   Mann-Kendall wrapper around pymannkendall (find_trend.py)
    ├── chart/                   Plotting helper with trend-line overlay (_chart.py)
    └── utils/                   Date validation for API requests (_validation.py)
```

## Installation

Python 3.12 or newer is required (the notebooks use f-strings with nested double quotes, and the heatwave code uses the pandas `"YE"` frequency alias, which needs pandas 2.2 or newer). The notebooks were developed on Python 3.14.

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd <your-repository>

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install "pandas>=2.2" numpy requests matplotlib seaborn pymannkendall jupyterlab
```

Exact package versions used for the published results: [TODO: paste the output of `pip freeze`, or add a `requirements.txt`].

An internet connection is required to download the data from NASA POWER.

## Reproducing the results

1. Start Jupyter from the **repository root**, so that `import src` and the relative path `./deeplearning.mplstyle` resolve correctly:

   ```bash
   jupyter lab
   ```

2. Open a notebook and choose *Run > Run All Cells*. The notebooks are independent of each other and can be run in any order.

| Notebook | Study area | Output |
|---|---|---|
| `Turbat.ipynb` | Kech (5 locations) | 4 figures: mean temperature, temperature trend, rainfall trend, heatwave trend |
| `Gawadar.ipynb` | Gwadar (5 locations) | Same 4 figures |
| `Panjgur.ipynb` | Panjgur (4 locations) | Same 4 figures |
| `Tump.ipynb` | Tump (2 locations) | Same 4 figures |
| `combined_rain.ipynb` | All four areas | Annual rainfall trends per area |
| `combined_heatwave.ipynb` | All four areas | Heatwave-day trends per area; also saves `combined_figure_3.pdf` |

Each trend cell prints the complete Mann-Kendall result for every location, including the slope, p-value and trend decision.

The heatwave step is written in plain Python loops and is slow; expect it to dominate the run time.

## Using the `src` package

```python
import src as mk

# 1. Download daily data for one point from NASA POWER
data = mk.MultiDataFrame()
data.set_default_parameters("T2M,T2M_MAX,T2M_MIN")
data.fetch_and_add(name="Turbat", lat=26.004168, lon=63.060555)

# 2. Annual mean temperature (work on a copy to keep the raw daily data)
annual = data.copy()
annual[0] = annual[0].transform(["T2M"]).to_annual(method="mean")

# 3. Modified Mann-Kendall test with Sen's slope
result = annual[0].find_trend("T2M").mann_kendall("yue_wang_modification_test")
print(result["T2M"])

# 4. Annual heatwave days from daily T2M_MAX
daily = data.copy()
daily[0].drop_leap_days(inplace=True)
heatwave_days = mk.DataFrame(mk.heatwave(daily[0]))   # column: Total_Heatwave_Days
```

Defaults of `MultiDataFrame` (start date 1981-01-01, end date 2025-12-31, community `AG`, daily resolution) can be changed with the `set_default_*` methods. Every module and function in `src/` is documented with inline comments.

## Freezing the downloaded data

To keep the exact input data used for the paper, save each downloaded series once and reload it instead of calling the API again:

```python
from pathlib import Path

Path("data/raw").mkdir(parents=True, exist_ok=True)
for key in data.keys():
    name = data.meta_data[key]["name"]
    data[key].save(f"data/raw/{name}_daily", fmt="csv")      # writes a .csv and a .meta.json

# later, instead of fetch_and_add(...):
restored = mk.MultiDataFrame()
restored.load_data(name="Turbat", path="data/raw/Turbat_daily")
```

Depositing these files in an archive such as Zenodo and citing the DOI makes the results independent of future NASA POWER updates.

## Reproducibility notes

- The code needs a live connection to NASA POWER; `end_date` cannot be later than the current date.
- A failed download is logged and returns no data instead of raising an error. If a figure comes out empty, check the log output of the `fetch_and_add` cell.
- Figures are shown inline; only `combined_heatwave.ipynb` writes a file (`combined_figure_3.pdf`).
- Run all notebooks from the repository root.

## Data acknowledgement


Data acknowledgement requested by NASA POWER: *These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program.*

Methods used:

- Yue, S. and Wang, C. (2004). The Mann-Kendall test modified by effective sample size to detect trend in serially correlated hydrological series. *Water Resources Management*, 18, 201-218.
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *Journal of the American Statistical Association*, 63, 1379-1389.
- Hussain, M. and Mahmud, I. (2019). pyMannKendall: a python package for non parametric Mann Kendall family of trend tests. *Journal of Open Source Software*, 4(39), 1556.

**Author:** Muhammad Essa, MS Data Science, MAJU University.
