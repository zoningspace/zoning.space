# Hooks

Hooks allow pre- and post-processing of zoning data, either before or after it is parsed by Zoning.Space. They are optional, and will not be needed for most cities. They are useful when data needs to be cleaned or merged prior to processing, or when there are zoning rules that are significantly easier to express in code rather than a specfile. Here are some examples of situations in which hooks might be useful:

 - overlaying multiple files that contain different aspects of the zoning code (for example, height districts, etc.)
 - special zoning codes in particular areas that are not defined in the zoning shapefile---for example, reduced parking requirements around transit

Hooks are written in Python (version 3.6, like the rest of the Zoning.Space stack). To create a hook, create a file `<slug>.py` in `src/zoning/hooks` (where slug is the same as the name of your shapefile and specfile). You can define several functions here:

  - `before (data, datadir)` receives a GeoPandas GeoDataFrame that results from reading the zipped shapefile, and should return a GeoPandas dataframe that has been processed. It is acceptable to operate destructively or in-place, so long as the data is returned. The `datadir` parameter is the path to the `data/zoning` directory, in case any ancillary data from there needs to be loaded.
 - `after (data, datadir)` receives a GeoPandas GeoDataFrame containing the processed data with all [Zoning.Space attributes](datadictionary), as well as the attributes from the original zipped shapefile; should return a GeoDataFrame that has at least the Zoning.Space attributes (and may have other attributes). Again, it is acceptable to destructively or in-place, so long as the data is returned.

The file is executed using Python's `exec` statement. Thus, if any modules or functions are imported, they must be [declared as globals in each function](https://github.com/zoningspace/zoning.space/blob/master/src/zoning/hooks/sanfrancisco.py#L13).
