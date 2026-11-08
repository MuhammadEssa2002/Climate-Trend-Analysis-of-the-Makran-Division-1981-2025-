# src/trend/find_trend.py -- applies Mann-Kendall-family trend tests (pymannkendall) to one
# or more columns.

# pymannkendall provides original_test, hamed_rao_modification_test,
# yue_wang_modification_test, ...
# (This `mk` is unrelated to the `mk` alias used for the src package in the notebooks.)
import pymannkendall as mk

# Runs one or more pymannkendall tests on one or more columns and collects the results.
class Find_Trend:
    # data: DataFrame holding the series; keys: a column name or a list of column names.
    def __init__(self, data , keys):
        self._data = data
        self._keys = keys
        self._methods = None
        # Results: column name -> result (single test) or list of results (list of tests).
        self._out_data = {}

    # methods: name of a pymannkendall test (str) or a list of names, e.g.
    # 'yue_wang_modification_test'.
    # Each name is resolved with getattr(pymannkendall, name) and applied to the column.
    # Every result is a namedtuple (trend, h, p, z, Tau, s, var_s, slope, intercept);
    # pymannkendall's default significance level alpha=0.05 is used.
    # Four cases follow: (column list | single column) x (test list | single test). The
    # return value is {column: result} or {column: [results]} accordingly.
    def mann_kendall(self,methods):
        self._methods = methods

        if isinstance(self._keys,list):
            if isinstance(self._methods,list):
                for key in self._keys:
                    method_results = []
                    for method in self._methods:
                        # Look up the test function by name (e.g.
                        # mk.yue_wang_modification_test) and run it on the column.
                        result = getattr(mk,method)
                        method_results.append(result(self._data[key]))

                    self._out_data[key] = method_results


            else:
                for key in self._keys:
                    result = getattr(mk,self._methods)
                    self._out_data[key] = result(self._data[key])

        else:
            if isinstance(self._methods,list):
                method_results = []
                for method in self._methods:
                    result = getattr(mk,method)
                    method_results.append(result(self._data[self._keys]))

                self._out_data[self._keys] = method_results

            else:
                result = getattr(mk,self._methods)
                self._out_data[self._keys] = result(self._data[self._keys])

        # Dictionary of results, keyed by column name.
        return self._out_data



