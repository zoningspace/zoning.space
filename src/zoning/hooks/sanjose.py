from src.zoning.zoneingest import ACRE_TO_HECTARE, FOOT_TO_METER
from src.ingest.shputils import readZippedShapefile, fastOverlay
from os.path import join
import numpy as np
import pandas as pd
import geopandas as gp
from tqdm import tqdm

tqdm.pandas()

# copy over the specified Planned Development density
def after (data, datadir):
    global ACRE_TO_HECTARE, readZippedShapefile, fastOverlay, np, FOOT_TO_METER, join, pd, gp
    data = data.to_crs(epsg=26943)

    pds = data[data.ZONINGABBR.apply(lambda a: '(PD)' in a)].index
    data.loc[pds, 'loMaxUnitsPerHectare'] = data.loc[pds, 'hiMaxUnitsPerHectare'] =\
        data.loc[pds, 'PDDENSITY'].astype(float) / ACRE_TO_HECTARE

    # Create a column for specific height restrictions. This will be merged with the main height restrictions later.
    # The reason we do this is that, in section 20.85.020(D), it says that in transit areas, the most permissive
    # _specific_ restriction applies, unless it is in the airport influence area in which case the least permissive
    # applies. Thus we have to keep the specific height restrictions separate.
    data['loSpecificHeightMeters'] = np.nan
    data['hiSpecificHeightMeters'] = np.nan

    print('handling specific height restrictions')
    specificHeightDistricts = readZippedShapefile(join(datadir, 'sanjose_specific_height_restrictions.zip')).to_crs(epsg=26943)
    airportInfluenceAreas = readZippedShapefile(join(datadir, 'sanjose_airport_influence_areas.zip')).to_crs(epsg=26943)
    airportInfluenceAreas['airportInfluenceArea'] = True

    # overlay
    data = fastOverlay(data, airportInfluenceAreas)
    data = fastOverlay(data, specificHeightDistricts)

    # Handle downtown zones, section 20.85.020(A)
    # These are controlled by FAA regulations, which are here and complicated to parse: https://www.ecfr.gov/cgi-bin/text-idx?SID=c957224f6e2b4fb1f2fc236f5da09558&node=pt14.2.77&rgn=div5#se14.2.77_117
    # But the heights at any reasonable distance from the airport are high enough it doesn't matter for this analysis, so
    # just set the minimum height limit to 90 feet
    downtown = data[data.ZONINGABBR.isin(['DC', 'DC-NT1'])].index
    data.loc[downtown, 'loSpecificHeightMeters'] = 90 * FOOT_TO_METER
    # anything over 499 feet is a hazard per FAA rules regardless of where it is relative to an airport
    data.loc[downtown, 'hiSpecificHeightMeters'] = 499 * FOOT_TO_METER

    def applySpecificHeightDistrict (section, height, maxHeight=None):
        if maxHeight is None:
            maxHeight = height
        if np.sum(data.sec == section) == 0:
            print(f'WARN did not find any zoning in special height restriction section {district}')

        # single family areas are not affected by specific height districts
        # TODO should multiFamily = conditional be included?
        affected = data[(data.sec == section) & (data.multiFamily == 'yes')].index
        data.loc[affected, 'loSpecificHeightMeters'] = height * FOOT_TO_METER
        data.loc[affected, 'hiSpecificHeightMeters'] = maxHeight * FOOT_TO_METER

    # This is the least specific and should be overridden by the remaining height restrictions
    applySpecificHeightDistrict('C.1.e', 120)

    # Downtown frame, section 20.85.020 sec B
    applySpecificHeightDistrict('B', 120)

    # North San José
    # These two are controlled by FAA regulations, which are here and complicated to parse: https://www.ecfr.gov/cgi-bin/text-idx?SID=c957224f6e2b4fb1f2fc236f5da09558&node=pt14.2.77&rgn=div5#se14.2.77_117
    # But the heights at any reasonable distance from the airport are high enough it doesn't matter for this analysis, so
    # just set the minimum height limit to 90 feet
    applySpecificHeightDistrict('C.1.a', 90, 250)
    applySpecificHeightDistrict('C.1.b', 90, 310)

    applySpecificHeightDistrict('C.1.c', 210)
    applySpecificHeightDistrict('C.1.d', 35)
    applySpecificHeightDistrict('C.3', 120)
    applySpecificHeightDistrict('C.4', 120)

    print('applying transit area height limits')
    stops = readZippedShapefile(join(datadir, 'sanjose_rail_stops.zip')).to_crs(epsg=26943)
    stops['geometry'] = stops.buffer(2000 * FOOT_TO_METER) # 2000 feet around rail stops

    # make disjoint, so we can use fastOverlay later
    print('cleaning transit areas')
    stopsDisjoint = gp.overlay(stops.loc[:,['geometry']], stops.loc[:,['geometry']], how='union')
    # highest height of any nearby stop
    stopsDisjoint['height'] = stopsDisjoint.geometry.progress_apply(lambda g: np.max(stops.height[~stops.disjoint(g)]))
    stopsDisjoint = stopsDisjoint.dissolve('height')
    # restore col after dissolve
    stopsDisjoint['height'] = pd.Series(stopsDisjoint.index.values, index=stopsDisjoint.index.values)

    # Don't use fastOverlay, the stop areas may overlap
    data = fastOverlay(data, stopsDisjoint)
    data['airportInfluenceArea'] = data['airportInfluenceArea'] == True # replace nan's with falses
    data = data[~pd.isnull(data.zone)].copy() # drop stuff outside of San Jose but near rail stations

    # outside airport influence areas, transit overrides all other height limits.
    # Within them, other height limits override. No one wants a 787 in their living room.
    # data.height is from the stops file
    # fmax and fmin ignore nans
    affectedMax = data[~data.airportInfluenceArea & ~pd.isnull(data.height) & (data.multiFamily == 'yes')].index
    data.loc[affectedMax, 'loSpecificHeightMeters'] =\
        np.fmax(data.loc[affectedMax, 'loSpecificHeightMeters'], data.loc[affectedMax, 'height'] * FOOT_TO_METER)
    data.loc[affectedMax, 'hiSpecificHeightMeters'] =\
        np.fmax(data.loc[affectedMax, 'hiSpecificHeightMeters'], data.loc[affectedMax, 'height'] * FOOT_TO_METER)

    affectedMin = data[data.airportInfluenceArea & ~pd.isnull(data.height) & (data.multiFamily == 'yes')].index
    data.loc[affectedMin, 'loSpecificHeightMeters'] =\
        np.fmin(data.loc[affectedMin, 'loSpecificHeightMeters'], data.loc[affectedMin, 'height'] * FOOT_TO_METER)
    data.loc[affectedMin, 'hiSpecificHeightMeters'] =\
        np.fmin(data.loc[affectedMin, 'hiSpecificHeightMeters'], data.loc[affectedMin, 'height'] * FOOT_TO_METER)

    # Where there is a specific height requirement, override the base height requirement. No need to filter for multiFamily
    # residential here, that has been done above.
    data['loMaxHeightMeters'] = data['loSpecificHeightMeters'].combine_first(data['loMaxHeightMeters'])
    data['hiMaxHeightMeters'] = data['hiSpecificHeightMeters'].combine_first(data['hiMaxHeightMeters'])

    data.crs = {'init': 'epsg:26943'}

    return data
