"""
Ingest zoning data based on a CSV description of the zoning codes
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

import csv
from collections import OrderedDict, defaultdict
import pandas as pd
import numpy as np
import functools
from ..ingest import Ingester

# A foot is exactly 0.3048 meters by international standard.
# Prior to the international standard, there was a measure known as a survey foot, which is slightly larger (less than 0.0001%). Let's
# assume that zoning codes use international feet, not that it matters for the distances we're talking about anyhow.
# We then define all other unit conversions based on this exact conversion, to minimize roundoff error.
FOOT_TO_METER = 0.3048
SQFOOT_TO_SQMETER = FOOT_TO_METER ** 2
SQFOOT_TO_HECTARE = SQFOOT_TO_SQMETER / 10000 # a hectare is 10000 square meters
ACRE_TO_HECTARE = SQFOOT_TO_HECTARE * 660 * 66 # an acre is 660 x 66 feet, the area one man and one horse can plow in a day

# These are the canonical forms of variables. Anything ending in meters can also be expressed in feet, hectares can
# also be expressed in acres or square feet, and minLotSizePerUnit{Hectares|Acres|SqFt} will be converted to maxUnitsPerHectare.
variables = {
    'singleFamily': 'str',
    'multiFamily': 'str',
    'maxHeightMeters': 'float',
    'maxHeightStories': 'float',
    'minLotSizePerUnitHectares': 'float',
    'maxUnitsPerLot': 'float',
    'minUnitsPerLot': 'float',
    'minLotSizeHectares': 'float',
    'maxLotSizeHectares': 'float',
    'minLotWidthMeters': 'float',
    'maxLotWidthMeters': 'float',
    'minLotDepthMeters': 'float',
    'minFloorAreaPerUnitSqMeters': 'float',
    'minParkingPerUnit': 'float',
    'maxParkingPerUnit': 'float',
    'maxUnitsPerHectare': 'float',
    'maxLotCoverage': 'float',
    'maxFar': 'float',
    'setbackFrontMeters': 'float',
    'setbackFrontPercent': 'float',
    'setbackSideMeters': 'float',
    'setbackSidePercent': 'float',
    'setbackRearMeters': 'float',
    'setbackRearPercent': 'float',
    'demoControls': 'int',
    'zone': 'str',
    'note': 'str'
}

schema = {
    'geometry': 'Polygon',
}

# add range attributes to schema
schema['properties'] = dict()
for key, val in variables.items():
    if val == 'float':
        # put lo and hi up front so they aren't lost if saved as a Shapefile with truncated columns
        schema['properties']['lo' + key[0].upper() + key[1:]] = val
        schema['properties']['hi' + key[0].upper() + key[1:]] = val
    else:
        # cannot be represented as a range
        schema['properties'][key] = val

schema['properties']['jurisdiction'] = 'str'

def isBlank (line):
    return len(line) == 0 or all([c == '' for c in line])

def parseAllowableUse (val):
    if val.lower() in {'0', 'f', 'false', 'n', 'no'}:
        return 'no'
    elif val.lower() in {'1', 't', 'true', 'y', 'yes'}:
        return 'yes'
    elif val.lower() in {'c', 'cup', 'cond', 'conditional'}:
        return 'conditional'
    else:
        raise ValueError(f'cannot parse allowable use value {val}')

def parseBoolean (val):
    if val.lower() in {'0', 'f', 'false', 'n', 'no'}:
        return 0
    elif val.lower() in {'1', 't', 'true', 'y', 'yes'}:
        return 1
    else:
        raise ValueError(f'cannot parse boolean value {val}')

def dictsToSeries (*dicts):
    out = dict()
    for dct in dicts:
        out.update(dct)

def processLine(line):
    return [c.strip() if not c.strip().startswith('#') else '' for c in line] # filter single cell comments

class ZoneIngester(Ingester):
    def __init__ (self, collater, definition):
        super().__init__(collater)
        self.readDefinition(definition)

    def readDefinition (self, definition):
        rdr = csv.reader(definition)

        # Read header
        self.jurisdiction = None
        self.year = None

        self.zoneColumns = [] # The columns used to specify a zone
        self.zoneTables = [] # possibly several tables of zoning codes, to be applied one after the other

        for line in rdr:
            line = processLine(line)
            if len(line) > 0 and line[0].startswith('//'):
                continue

            if isBlank(line):
                break # reached end of header

            if line[0] == 'jurisdiction':
                self.jurisdiction = line[1]
            elif line[0] == 'year':
                if line[1] != '':
                    self.year = int(line[1])
            elif line[0] == 'column':
                self.zoneColumns.append(line[1]) # the columns used in this file

        # Read body
        currentColumns = None
        tableZoneColumns = None
        dataOffset = None # the index of the first column containing data
        zoneData = None
        for line in rdr:
            line = processLine(line)
            if len(line) > 0 and line[0].startswith('//'):
                continue

            if isBlank(line):
                # Signifies table boundary, save table and start again
                zoneData.set_index(tableZoneColumns, inplace=True)
                self.zoneTables.append(zoneData)

                currentColumns = dataOffset = tableZoneColumns = zoneData = None
                continue

            if currentColumns is None:
                # new table, this line is header
                currentColumns = line
                tableZoneColumns = []
                for i, column in enumerate(currentColumns):
                    if column in self.zoneColumns:
                        tableZoneColumns.append(column)
                    else:
                        # column offset to start of zoning data
                        dataOffset = i
                        break

                # Create an empty data frame to hold the values from this table
                zoneData = pd.DataFrame(columns=tableZoneColumns + list(variables.keys()))

            else:
                # Read a zone
                # lineValues will eventually be a row of the zone lookup table
                lineValues = {column: zone for column, zone in list(zip(currentColumns, line))[:dataOffset]}
                for rawCol, rawVal in list(zip(currentColumns, line))[dataOffset:]:
                    if rawVal == '':
                        continue

                    # Allow users to specify ranges as, e.g., 13-42
                    if rawCol not in ['note', 'singleFamily', 'multiFamily', 'demoControls']:
                        if '-' in rawVal:
                            # Houston, we have a range
                            vals = rawVal.split('-')
                            if len(vals) != 2:
                                raise ValueError(f'cannot parse range {rawVal} for column {rawCol}')

                            colVals = zip(('lo' + rawCol[0].upper() + rawCol[1:], 'hi' + rawCol[0].upper() + rawCol[1:]), vals)
                        else:
                            colVals = (('lo' + rawCol[0].upper() + rawCol[1:], rawVal), ('hi' + rawCol[0].upper() + rawCol[1:], rawVal))

                    else:
                        colVals = [(rawCol, rawVal)]

                    for col, val in colVals:
                        # do unit conversion
                        # areas first, so SqFeet comes before Feet
                        if rawCol.endswith('Acres'):
                            col = col.replace('Acres', 'Hectares')
                            val = float(val) * ACRE_TO_HECTARE

                        elif rawCol.endswith('PerAcre'):
                            col = col.replace('PerAcre', 'PerHectare')
                            # divide since the units are in the denominator
                            val = float(val) / ACRE_TO_HECTARE

                        elif rawCol.endswith('SqFeet') or rawCol.endswith('SqFt'):
                            col = col.replace('SqFeet', 'Hectares').replace('SqFt', 'Hectares')
                            # some things (notably unit sizes) should not be represented in hectares
                            if col in schema['properties']:
                                val = float(val) * SQFOOT_TO_HECTARE
                            else:
                                col = col.replace('Hectares', 'SqMeters')
                                val = float(val) * SQFOOT_TO_SQMETER

                        elif rawCol.endswith('Feet'):
                            col = col.replace('Feet', 'Meters')
                            val = float(val) * FOOT_TO_METER

                        elif col == 'singleFamily' or col == 'multiFamily':
                            val = parseAllowableUse(val)

                        elif col == 'demoControls':
                            val = parseBoolean(val)

                        elif col == 'note':
                            pass # leave as string

                        else:
                            val = float(val)

                        if col not in schema['properties'].keys():
                            raise ValueError(f'Unrecognized column {col} (was {rawCol})!')

                        lineValues[col] = val
                # Zone for current table, for this designation and column
                zoneData = zoneData.append(lineValues, ignore_index=True, )

        if zoneData is not None:
            # last table did not get appended yet
            zoneData.set_index(tableZoneColumns, inplace=True)
            self.zoneTables.append(zoneData)

    def computeDensityLimits (self, row):
        """
        There are a lot of ways to define density, and cities may use some or all of them.
        Translate them into a common unit, units per hectare, using the most conservative limit.
        """
        row = row.copy() # protective copy, I don't know if there are issues with modifying in place but let's not find out
        for prefix in ('hi', 'lo'):
            # Find the
            maxDensity = np.inf

            if not np.isnan(row[prefix + 'MinLotSizePerUnitHectares']):
                maxDensity = min(maxDensity, 1 / row[prefix + 'MinLotSizePerUnitHectares'])

            if not np.isnan(row[prefix + 'MaxUnitsPerHectare']):
                maxDensity = min(maxDensity, row[prefix + 'MaxUnitsPerHectare'])

            if not np.isnan(row[prefix + 'MinLotSizeHectares']) and not np.isnan(row[prefix + 'MaxUnitsPerLot']):
                maxDensity = min(maxDensity, row[prefix + 'MaxUnitsPerLot'] / row[prefix + 'MinLotSizeHectares'])

            if np.isfinite(maxDensity):
                row[prefix + 'MaxUnitsPerHectare'] = maxDensity

        return row

    def transform (self, data):
        # Map all zones to a particular set of rules
        # First, get all unique zoning codes (combinations of specified columns)
        # Convert Nones to empty strings for ease of joining with CSV
        data = data.copy()
        for col in self.zoneColumns:
            data[col] = data[col].apply(lambda x: x if x is not None and not pd.isnull(x) else '')

        # No need to have the same code multiple times
        zoneData = data[self.zoneColumns].drop_duplicates()

        # make sure it has all the required columns
        for col in schema['properties'].keys():
            zoneData[col] = np.nan

        # Merges results from a zonetable into existing results
        def merge (zoneTable, colset, base):
            if len(colset) > 1:
                index = tuple(base.loc[colset])
            else:
                index = base.loc[colset].values[0]

            if index in zoneTable.index:
                # this table contains a match for this zone
                vals = zoneTable.loc[index]
                # grab only the vals that are specified in this table
                vals = vals[vals.apply(lambda x: x is not None and x != '' and not (type(x) == np.float64 and np.isnan(x)))]
                # and apply them to base zoning
                out = base.copy()
                out.update(vals)
                return out
            else:
                return base # no match, leave unchanged

        # apply each table in turn
        for zoneTable in self.zoneTables:
            colset = list(zoneTable.index.names) # the columns that went into this index
            zoneData = zoneData.apply(functools.partial(merge, zoneTable, colset), axis=1)

        zoneData['zone'] = zoneData[self.zoneColumns].apply(lambda row: '-'.join([str(i) for i in row.values.tolist()]), axis=1)

        # merge fast
        zoneData = zoneData.set_index(self.zoneColumns)

        # there are several ways to specify density, convert them to the lingua franca of units per hectare
        zoneData = zoneData.apply(self.computeDensityLimits, axis=1)

        df = data.merge(zoneData, left_on=self.zoneColumns, right_index=True, validate='m:1', how='left')
        df['jurisdiction'] = self.jurisdiction
        return df
