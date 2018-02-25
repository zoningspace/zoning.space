#!/usr/bin/python
# Load zoning for all spec'd cities

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

from sys import argv, exit
import os.path
from pathlib import Path
from argparse import ArgumentParser

from src.zoning.zoneingest import ZoneIngester, schema
from src.ingest import Collater

print('''
 _____           _               ____
|__  /___  _ __ (_)_ __   __ _  / ___| _ __   __ _  ___ ___
  / // _ \| '_ \| | '_ \ / _` | \___ \| '_ \ / _` |/ __/ _ \
 / /| (_) | | | | | | | | (_| |_ ___) | |_) | (_| | (_|  __/
/____\___/|_| |_|_|_| |_|\__, (_)____/| .__/ \__,_|\___\___|
                         |___/        |_|                   
''') # thanks figlet

parser = ArgumentParser(description='Ingest zoning data for fun and profit')
parser.add_argument('outfile', help='Output file')
parser.add_argument('--driver', default='GeoJSON', help='OGR driver for writing output')
parser.add_argument('--include', nargs='+', help='Cit(ies) to parse, default all')
parser.add_argument('--exclude', nargs='+', help='Cit(ies) to omit')
args = parser.parse_args()

# identify spec files
specpath = Path(os.path.join(os.path.dirname(argv[0]), 'src', 'zoning', 'specs'))
specs = list(specpath.glob('*.csv'))

# identify cities
slugs = [os.path.basename(spec).replace('.csv', '') for spec in specs]
if args.include:
    slugs = [slug for slug in slugs if slug in args.include]
if args.exclude:
    slugs = [slug for slug in slugs if slug not in args.exclude]

print('Reading the following specs:')
for slug in slugs:
    print(f' - {slug}')

# Make sure they have a matching shapefile
shppath = os.path.join(os.path.dirname(argv[0]), 'data', 'zoning')

missingStems = []
for slug in slugs:
    if not os.path.exists(os.path.join(shppath, slug + '.zip')):
        missingStems.append(slug)

if len(missingStems) > 0:
    print(f'Stems f{", ".join(missingStems)} are missing zipped shapefiles.')
    exit(1)

print('Initializing output...')
with Collater(schema=schema, outfile=args.outfile, driver=args.driver) as collater:
    print(f'collater: {collater}')
    print('Reading slugs...')
    for slug in slugs:
        print(f'  Reading {slug}...')
        with open(os.path.join(specpath, slug + '.csv')) as spec:
            ingester = ZoneIngester(collater, spec)
            ingester.ingest(slug)
