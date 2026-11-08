# src/__init__.py -- package entry point.
# The notebooks do `import src as mk`; the names re-exported here form the public API:
# - mk.DataFrame: metadata-aware pandas DataFrame subclass (src/core/dataframe.py)
# - mk.MultiDataFrame: container of several location DataFrames
#   (src/core/multi_dataframe.py)
# - mk.load: reload a dataset written with DataFrame.save() (src/data_load/load_data.py)
# - mk.heatwave: annual heatwave-day counter (src/transform/heatwave.py)

# The class is defined as `Dataframe` but exported as `DataFrame` (capital F), so notebooks
# can write mk.DataFrame(...).
from .core import Dataframe as DataFrame

# Container that stores one time series per location, keyed 0, 1, 2, ... in the order added.
from .core import MultiDataFrame

# mk.load(path, fmt=...) restores a dataset (and its metadata) saved with DataFrame.save().
from .data_load import load_data as load

# mk.heatwave(df) is the heatwave-day function itself (not the module of the same name).
from .transform import heatwave as heatwave
