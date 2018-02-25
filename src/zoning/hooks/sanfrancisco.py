# A hooks file can define the following hooks:
# before (data, datadir): transform the data before it is processed by any of the code in the stack
# Receives the data from the shapefile raw, with no conversions or filtering whatsoever. Returns transformed data.
# It is acceptable to operate in place as long as the data is returned.
# Data dir is the path to the data/zoning directory, in case auxiliary data needs to be loaded.

from os.path import join, exists
import geopandas as gp
import numpy as np
from src.zoning.zoneingest import FOOT_TO_METER
from src.ingest.shputils import readZippedShapefile, fastOverlay
from tqdm import tqdm
from functools import partial

# Unify several datasets to produce a canonical SF Zoning dataset
def before (data, datadir):
    global readZippedShapefile, join, gp, exists, fastOverlay # https://stackoverflow.com/questions/12505047/in-python-why-doesnt-an-import-in-an-exec-in-a-function-work
    # from https://data.sfgov.org/Housing-and-Buildings/Height-and-Bulk-Districts/tt4g-gzy9/data

    # project to state plane CA Zone 3 (meters)
    data = data.to_crs(epsg=26943)
    # read special use districts
    print('processing special use districts')
    specialUseDistricts = readZippedShapefile(join(datadir, 'sanfrancisco-special-use-districts.zip')).dissolve('name').to_crs(epsg=26943)
    specialUseDistricts['name'] = specialUseDistricts.index.values
    # Get rid of the really tiny ones (less than 0.25 square km), and ones that don't apply to residences
    relevantSpecialUseDistricts = specialUseDistricts.loc[['Parkmerced', 'Bernal1', 'Candlestick Pt Activity Node', 'Hunters Pt Shipyard Phase 2',
        'India Basin Industrial Park', 'Industrial Protection Zone', 'North of Market Residential 1', 'Telegraph Hill-NB Residential',
        'Van Ness', 'Waterfront 2', 'Waterfront 3']]

    # Some properties are subject to multiple special use districts. Split the map so that each combination of special
    # use districts has its own nonoverlapping polygon
    # use GeoPandas overlay here, because it properly handles overlapping polygons in the same layer, which we have
    # and is performant enough for such a small dataset
    topologicalSpecialUseDistricts = gp.overlay(relevantSpecialUseDistricts, relevantSpecialUseDistricts, how='union')

    # More than two districts may be overlaid, so name and name_2 cols may not be correct, but topology will be correct
    # Add a new column with the names of all the special use districts affecting a particular topology
    topologicalSpecialUseDistricts['SPECIAL_USE_DISTRICTS'] =\
        topologicalSpecialUseDistricts.geometry.apply(
            # Avoid slivers by only looking at intersections greater than 500 sq feet in area
            lambda geom: ','.join(sorted(relevantSpecialUseDistricts.name[relevantSpecialUseDistricts.intersection(geom).area > 500].values.tolist())))

    heightDistricts = readZippedShapefile(join(datadir, 'sanfrancisco-heightbulk.zip')).to_crs(epsg=26943)

    print('overlaying special use districts')
    data = fastOverlay(data, topologicalSpecialUseDistricts)

    print('overlaying height districts')
    data = fastOverlay(data, heightDistricts)

    data.crs = { 'init': 'epsg:26943' } # somehow this gets lost, not sure how
    data = data.to_crs(epsg=4236)

    # fast enough now we probably don't need this
    try:
        data.to_file(join(datadir, 'sanfrancisco_processed.json'), driver='GeoJSON')
    except:
        print('error creating json file')

    return data

def after (data, datadir):
    global np, FOOT_TO_METER, partial, tqdm
    # Take care of special height limits
    print('Handling special height limits')
    rh1 = data[data.zone.apply(lambda x: x.startswith('RH-1'))].index

    # Also replace NaNs with the max value
    def minOrNan (series, x):
        out = np.minimum(series, x)
        out[np.isnan(out)] = x
        return out

    # Lower height limits in RH-1 zones, sec 261
    data.loc[rh1, 'loMaxHeightMeters'] = minOrNan(data.loc[rh1, 'loMaxHeightMeters'], 35 * FOOT_TO_METER)
    data.loc[rh1, 'hiMaxHeightMeters'] = minOrNan(data.loc[rh1, 'hiMaxHeightMeters'], 35 * FOOT_TO_METER)

    # Except in Bernal Heights, sec 242
    bernal = data[data.zone.apply(lambda x: 'Bernal' in x)].index
    data.loc[bernal, 'loMaxHeightMeters'] = minOrNan(data.loc[bernal, 'loMaxHeightMeters'], 30 * FOOT_TO_METER)
    data.loc[bernal, 'hiMaxHeightMeters'] = minOrNan(data.loc[bernal, 'hiMaxHeightMeters'], 30 * FOOT_TO_METER)

    return data
