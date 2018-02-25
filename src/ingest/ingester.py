# ingester: Ingest data from a zipped shapefile
#
# Subclasses should implement the function transform (self, dataframe), which should return a dataframe with
# the columns defined by in the collater and the same geometries (extra columns and destructive modification are allowed)
#
# @author mattwigway

# Copyright 2018 Zoning.Space contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


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
