"""
A Collater receives data ingested by an Ingester and collates it into a single file. Collaters can be used as
context managers.
"""

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


import fiona
import shapely.geometry
import numpy as np

CRS = { 'init': 'epsg:4326' } # WGS 84

INFINITY = 2147438647 # maxint for 32 bit int

class Collater (object):
    def __init__ (self, schema, outfile, driver='GeoJSON'):
        "schema is a fiona schema, see http://toblerity.org/fiona/manual.html#writing-vector-data"
        self.schema = schema
        self.outfilename = outfile
        self.driver = driver
        self.out = None

    def __enter__ (self):
        self.open()
        return self

    def __exit__ (self, exception_type, exception_value, traceback):
        self.close()

    def open (self):
        self.out = fiona.open(self.outfilename, 'w', driver=self.driver, crs=CRS, schema=self.schema)

    def close (self):
        if self.out is not None:
            self.out.close()

    def collate (self, data):
        if self.out is None:
            raise Exception('Collater has not been opened (call open() or use a with statement).')

        if not set(self.schema['properties'].keys()).issubset(data.columns):
            raise ValueError('Not all columns in schema are in data frame!')

        projected = data.to_crs(CRS)

        def fiona_records_gen():
            for index, row in projected.iterrows():
                yield self.toFionaRecord(row)

        self.out.writerecords(fiona_records_gen())

    # convert NaNs to Nones, which will be written as nulls. The JSON spec doesn't allow NaNs and Infinities, but fiona
    # is happy to write them anyhow
    # TODO the Infinities mean something - how to carry them through into output?
    def processValue (self, val):
        if type(val) == float:
            if np.isnan(val):
                return None
            if not np.isfinite(val):
                return INFINITY
        return val

    def toFionaRecord (self, row):
        "Convert a row from the data frame to a Fiona record"
        return {
            'properties': {

                key: self.processValue(value)
                for key, value in
                dict(row.loc[list(self.schema['properties'].keys())]).items()
                },
            'geometry': shapely.geometry.mapping(row.geometry)
        }
