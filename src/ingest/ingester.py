# ingester: Ingest data from a zipped shapefile
#
# Subclasses should implement the function transform (self, dataframe), which should return a dataframe with
# the columns defined by in the collater and the same geometries (extra columns and destructive modification are allowed)
#
# @author mattwigway

from functools import partial
import geopandas as gp
import numpy as np
from os.path import dirname, join
from .shputils import readZippedShapefile
from src.zoning.hooks import runHook

class Ingester(object):
    def __init__ (self, collater):
        self.collater = collater
        self.data = None

    def ingest (self, slug):
        "Read a shapefile"
        print('    Reading shapefile...')
        shp = readZippedShapefile(join(dirname(__file__), '..', '..', 'data', 'zoning', slug + '.zip'))
        shp = runHook(slug, 'before', shp)

        # Drop features with no geometry (I know, what?)
        # https://github.com/geopandas/geopandas/issues/138
        noGeom = shp.geometry.apply(lambda g: g is None)
        nNoGeom = np.sum(noGeom)
        if (nNoGeom > 0):
            print(f'      WARNING: {nNoGeom} ({nNoGeom / len(shp):.4f}%) features had no geometry, dropping them')
            shp = shp[~noGeom].copy()

        print('    Standardizing columns...')
        # Call subclass method to add standardized columns
        df = self.transform(shp)

        df = runHook(slug, 'after', df)

        print('    Writing to collater...')
        self.collater.collate(df)
