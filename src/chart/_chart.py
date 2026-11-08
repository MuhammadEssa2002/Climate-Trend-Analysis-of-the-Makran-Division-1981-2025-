# src/chart/_chart.py -- plotting helper used by Dataframe.chart().
# Draws one column of a time-indexed DataFrame on a Matplotlib Axes (or the current pyplot
# figure) and can overlay a Mann-Kendall/Sen's-slope trend line on the same plot.

# Matplotlib does all the drawing; the plot type is looked up by name at run time (getattr).
import matplotlib.pyplot as plt
# NumPy builds the 0..n-1 index on which the trend line is evaluated.
import numpy as np

# Find_Trend wraps the pymannkendall tests and returns slope/intercept/p-value etc.
from src.trend import Find_Trend

# Thin wrapper around a Matplotlib plotting call for one column of a DataFrame.
# Created by Dataframe.chart(); call .mann_kendall(...) on the returned object to add a
# trend line.
class Chart:
    # chart_type: Matplotlib method name ('line' is accepted as an alias for 'plot'; also
    # 'bar', 'scatter', ...).
    # data: DataFrame whose index is the x-axis (years for annual series).
    # key: name of the column to plot on the y-axis.
    # ax: Axes to draw on; None means the current pyplot figure.
    # show_chart: if False nothing is drawn now (useful when only the trend line is wanted).
    # *args/**kwargs: forwarded unchanged to the Matplotlib call (colour, marker, label,
    # ...).
    def __init__(self,chart_type,data,key,ax,show_chart,*args,**kwargs):
        self._ax = ax
        self._data = data
        self._key = key
        # Matplotlib has no 'line' function; the equivalent is plot().
        if (chart_type == "line"):
            chart_type = "plot"

        # Draw the data series only when requested.
        if show_chart:
            # No Axes supplied -> draw on the current pyplot figure; otherwise draw on the
            # given Axes.
            if (self._ax == None):
                # Resolve plt.plot / plt.bar / ... by name, then plot column `key` against
                # the DataFrame index.
                plotting = getattr(plt,chart_type)
                plotting(self._data.index,self._data[self._key],*args,**kwargs)
            else:
                # Same call, made as a method of the supplied Axes object.
                plotting = getattr(self._ax,chart_type)
                plotting(self._data.index,self._data[self._key],*args,**kwargs)

    # Run a Mann-Kendall-family test on the stored column and draw the fitted Sen's-slope
    # line.
    # method: name of a pymannkendall test, e.g. 'yue_wang_modification_test' (used in the
    # notebooks).
    # chart_type/*args/**kwargs: style of the trend line (e.g. color='red', linestyle='--').
    # Returns the pymannkendall result (trend, h, p, z, Tau, s, var_s, slope, intercept).
    def mann_kendall(self,method,chart_type = "line",*args,**kwargs):
        # Same 'line' -> 'plot' alias as in __init__.
        if (chart_type == "line"):
            chart_type = "plot"

        # Apply the requested test to the column; the result is a dict keyed by column name.
        result = Find_Trend(self._data,self._key).mann_kendall(method)

        # Sen's slope (change per time step; per year for annual series) and its intercept,
        # as returned by the test.
        slope = result[self._key].slope
        intercept = result[self._key].intercept

        # pymannkendall reports the intercept for a 0-based step index (0, 1, ..., n-1), so
        # the line is evaluated on that same index rather than on calendar years.
        x_data = np.linspace(0,len(self._data.index)-1,len(self._data.index))
        # Trend line: y = slope * step + intercept.
        y_data = slope*x_data + intercept

        # Draw the trend line on the same Axes (or current figure) as the data.
        if (self._ax == None):
            plotting = getattr(plt,chart_type)
            plotting(self._data.index,y_data,*args,**kwargs)
        else:
            plotting = getattr(self._ax,chart_type)
            plotting(self._data.index,y_data,*args,**kwargs)

        # Return the full test result so the caller can print it or annotate the plot with
        # slope/intercept.
        return result[self._key]




        