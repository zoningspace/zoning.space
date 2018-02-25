#!/usr/bin/python
# Load zoning for all spec'd cities

from sys import argv, exit
import os.path
from pathlib import Path
from argparse import ArgumentParser

from src.zoning.zoneingest import ZoneIngester, schema
from src.ingest import Collater

print('''
 _____                ___                       _
|__  /___  _ __   ___|_ _|_ __   __ _  ___  ___| |_ ___ _ __
  / // _ \| '_ \ / _ \| || '_ \ / _` |/ _ \/ __| __/ _ \ '__|
 / /| (_) | | | |  __/| || | | | (_| |  __/\__ \ ||  __/ |
/____\___/|_| |_|\___|___|_| |_|\__, |\___||___/\__\___|_|
                                |___/
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
