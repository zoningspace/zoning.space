# Hooks to postprocess Sacramento data

from os.path import join
import partridge as ptg
from shapely.geometry import Point
import geopandas as gp
import pandas as pd
import numpy as np

from src.zoning.zoneingest import FOOT_TO_METER, ACRE_TO_HECTARE
from src.ingest.shputils import readZippedShapefile, fastOverlay

def after (data, datadir):
    global join, readZippedShapefile, fastOverlay, ptg, Point, gp, pd, FOOT_TO_METER, ACRE_TO_HECTARE, np

    print('reprojecting data')
    data = data.to_crs(epsg=26942)

    print('adding parking requirements \U0001f697')
    # Parking Districts required a CA Public Records Act request:
    # https://sacramentoca.mycusthelp.com/WEBAPP/_rs/(S(2rztm4xsj04qo445twgqihlj))/RequestArchiveDetails.aspx?rid=8033&view=1
    parkingDistricts = readZippedShapefile(join(datadir, 'sacramento_parking.zip')).to_crs(epsg=26942)\
        .rename(columns={'SECTION': 'parkingDist'})

    data = fastOverlay(data, parkingDistricts)
    data['parkingDist'] = data.parkingDist.astype('category')

    # http://www.qcode.us/codes/sacramento/view.php?topic=17-vi-17_608-17_608_030&frames=on

    # Most places have no max parking requirement, overwritten in the CBD below
    data['loMaxParkingPerUnit'] = np.inf
    data['hiMaxParkingPerUnit'] = np.inf

    data.loc[data.parkingDist == 'Central Business District', 'loMinParkingPerUnit'] = 0
    data.loc[data.parkingDist == 'Central Business District', 'hiMinParkingPerUnit'] = 0
    data.loc[(data.parkingDist == 'Central Business District') & (data.multiFamily == 'yes'), 'loMaxParkingPerUnit'] = 1
    data.loc[(data.parkingDist == 'Central Business District') & (data.multiFamily == 'yes'), 'hiMaxParkingPerUnit'] = 1

    data.loc[(data.parkingDist == 'Urban') & (data.multiFamily == 'yes'), 'loMinParkingPerUnit'] = 0.5
    data.loc[(data.parkingDist == 'Urban') & (data.multiFamily == 'yes'), 'hiMinParkingPerUnit'] = 0.5

    # != yes: no or conditional
    # NB not encoding exception for lots under 3200 sq feet
    data.loc[(data.parkingDist == 'Urban') & (data.multiFamily != 'yes'), 'loMinParkingPerUnit'] = 1
    data.loc[(data.parkingDist == 'Urban') & (data.multiFamily != 'yes'), 'hiMinParkingPerUnit'] = 1

    data.loc[data.parkingDist == 'Traditional', 'loMinParkingPerUnit'] = 1
    data.loc[data.parkingDist == 'Traditional', 'hiMinParkingPerUnit'] = 1

    data.loc[(data.parkingDist == 'Suburban') & (data.multiFamily == 'yes'), 'loMinParkingPerUnit'] = 1.5
    data.loc[(data.parkingDist == 'Suburban') & (data.multiFamily == 'yes'), 'hiMinParkingPerUnit'] = 1.5
    data.loc[(data.parkingDist == 'Suburban') & (data.multiFamily != 'yes'), 'loMinParkingPerUnit'] = 1
    data.loc[(data.parkingDist == 'Suburban') & (data.multiFamily != 'yes'), 'hiMinParkingPerUnit'] = 1

    # M-1, M-1(S) and M-2 zones conditionally permit multifamily housing iff it is in the central city or within 1/4 mile
    # of a light rail stop
    print('loading central city')
     # this file was created by hand based on the description in the code
    centralCity = readZippedShapefile(join(datadir, 'sacramento_central_city.zip')).to_crs(epsg=26942)

    print('loading light rail stations from GTFS')
    feed = ptg.feed(join(datadir, 'sacramento_gtfs_20180213.zip'))

    lightRailRoutes = feed.routes.route_id[feed.routes.route_type == 0]
    lightRailTrips = feed.trips.trip_id[feed.trips.route_id.isin(lightRailRoutes)]
    feed.stop_times.set_index(['trip_id', 'stop_sequence'], inplace=True)
    lightRailStopIds = feed.stop_times.loc[lightRailTrips, 'stop_id'].unique()
    feed.stops.set_index('stop_id', inplace=True)
    lightRailStops = feed.stops.loc[lightRailStopIds].copy()

    print(f'found {len(lightRailStops)} light rail stops')

    # convert to geodataframe
    lightRailStops['geometry'] = lightRailStops.apply(lambda stop: Point(stop.stop_lon, stop.stop_lat), 1)
    # GTFS is defined to be WGS 84
    lightRailStops = gp.GeoDataFrame(lightRailStops, geometry='geometry', crs={'init': 'epsg:4326'})
    lightRailStops = lightRailStops.to_crs(epsg=26942)

    # save memory
    del feed

    print('buffering light rail stops')
    lightRailStops['geometry'] = lightRailStops.buffer(5280 / 4 * FOOT_TO_METER, resolution=32)

    # For M and RMX-SPD-R St zones, we cut these zones out of the whole file, overlay them with the affected area, and
    # then merge them back in.
    print('adding multifamily as conditional use to industrial zones near light rail')
    industrialZoneLocs = data.zone.apply(lambda zone: zone.startswith('M-1') or zone.startswith('M-1(S)' or zone.startswith('M-2')))
    industrialZones = data[industrialZoneLocs]
    affectedAreas = lightRailStops.loc[:,['geometry']].copy()
    affectedAreas['lightRail'] = True # add a flag column so we know which resulting geometries overlapped
    # and add the central city
    # Do an overlay so that we split large industrial zones at the boundaries of the affected area
    splitIndustrialAreas = gp.overlay(industrialZones, affectedAreas, how='identity')
    centralCity['centralCity'] = True
    splitIndustrialAreas = gp.overlay(splitIndustrialAreas, centralCity, how='identity')

    splitIndustrialAreas['lightRail'] = splitIndustrialAreas.lightRail.fillna(False)
    splitIndustrialAreas['centralCity'] = splitIndustrialAreas.centralCity.fillna(False)

    # and set the multiFamily flag. Conditional at light rail, yes in central city
    # http://qcode.us/codes/sacramento/view.php?topic=17-ii-17_220-i-17_220_110&frames=on
    splitIndustrialAreas['multiFamily'] = splitIndustrialAreas\
        .apply(lambda x: 'yes' if x.centralCity else 'conditional' if x.lightRail else 'no', 'columns')

    print('setting density limits in RMX-SPD-R Street Corridor')
    rmxSpdRstLocs = data.zone == 'RMX-SPD-R Street Corridor'
    rmxSpdRst = data[rmxSpdRstLocs]

    affectedAreas = lightRailStops.loc[:,['geometry']].copy()
    affectedAreas['affected'] = 42 # add a flag column so we know which resulting geometries overlapped
    splitRmxSpd = gp.overlay(rmxSpdRst, affectedAreas, how='identity')
    splitRmxSpd['loMaxUnitsPerHectare'] = splitRmxSpd['hiMaxUnitsPerHectare'] =\
        splitRmxSpd.affected.apply(lambda x: 100 / ACRE_TO_HECTARE if x == 42 else 60 / ACRE_TO_HECTARE)

    # put it all back together into a single dataframe
    recombined = gp.GeoDataFrame(
        pd.concat([
            data[~(rmxSpdRstLocs | industrialZoneLocs)],
            splitRmxSpd,
            splitIndustrialAreas
        ]),
        geometry='geometry' ,
        crs={'init': 'epsg:26942'}
        )

    # drop the 'affected' column we were using as a flag
    del recombined['affected']

    return recombined
