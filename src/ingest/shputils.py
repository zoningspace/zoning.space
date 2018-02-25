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


from zipfile import ZipFile
import geopandas as gp
import shapely.ops
from tempfile import mkdtemp
from shutil import rmtree
from tqdm import trange

def readZippedShapefile (shpzip):
    if type(shpzip) == str:
        with open(shpzip, 'rb') as raw:
            return readZippedShapefile(raw)
    else:
        tmp = mkdtemp()

        zf = ZipFile(shpzip)

        shapePath = None

        for zi in zf.infolist():
            pth = zf.extract(zi, path=tmp) # Extract the item. zf.extract handles sanitizing member names
            if pth.endswith('.shp'):
                if shapePath is not None:
                    raise ArgumentError(f'Multiple shapefiles found in {shpzip}!')
                else:
                    shapePath = pth

        shp = gp.read_file(shapePath)
        rmtree(tmp)
        return shp


# GeoPandas overlay is way too slow to be usable for this, so roll our own that is several orders of magnitude faster
# Note: this will not work if the features in one or the other dataframe are not disjoint
def fastOverlay (df1, df2, minArea=100):
    outrows = []
    for i in trange(len(df1)):
        geom = df1.iloc[i].geometry
        intersectingGeoms = df2.intersects(geom)
        intersections = df2[intersectingGeoms].intersection(geom)
        remainingGeom = geom.difference(shapely.ops.unary_union(intersections.values).buffer(1e-2))

        for index, intersection in intersections[intersections.area > minArea].iteritems(): # drop slivers
            if intersection.type == 'Polygon':
                parts = [intersection]
            elif intersection.type == 'MultiPolygon':
                parts = intersection.geoms
            elif intersection.type == 'GeometryCollection':
                # get rid of point and line intersections when geometries just touch
                parts = [part for part in intersection.geoms if part.type == 'Polygon']

            for part in parts:
                row = df1.iloc[i].copy()
                row = row.combine_first(df2.loc[index])
                row['geometry'] = part
                outrows.append(row)

        if remainingGeom.type == 'Polygon':
            remainingGeoms = [remainingGeom]
        elif remainingGeom.type == 'MultiPolygon':
            remainingGeoms = remainingGeom.geoms
        elif remainingGeom.type == 'GeometryCollection':
            remainingGeoms = [part for part in remainingGeom.geoms if part.type == 'Polygon']

        for part in remainingGeoms:
            if part.area > minArea:
                row = df1.iloc[i].copy()
                row['geometry'] = part
                outrows.append(row)

    # drop=True avoids issues with multiple overlays (https://stackoverflow.com/questions/12203901)
    return gp.GeoDataFrame(outrows, geometry='geometry').reset_index(drop=True)
