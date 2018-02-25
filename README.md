# Zoning.Space
Zoning.Space is an open, crowdsourced, machine-readable database of municipal residential zoning regulations. Municipal zoning is a major determinant of urban land use, environmental sustainability, and housing affordability. Data on zoning, however, has been up to this point rather lacking. Most cities have a zoning code that restricts the types of uses, density of residential dwellings, etc. that can be implemented in a given area. These codes, however, are highly variable between cities, making comparative studies very difficult.

Zoning.Space aims to address this gap by providing machine-readable data on zoning regulations across a variety of cities. This data is valuable to policymakers and researchers analyzing trends across many cities.

This repository contains tools and data to process a myriad of zoning codes into a unified dataset containing such variables as height limits :office:, setbacks, density limits, and parking requirements :car:.

## Dependencies

Conda dependencies are listed in `environment.yml`. [Install](https://conda.io/docs/user-guide/install/) Conda, then activate an environment:

```
conda env create --name zoning.space --file environment.yml
source activate zoning.space
```

When dependencies change, update your environment:

```
conda env update --name zoning.space --file environment.yml
```

## Processing the data

The input data, which comes from various cities' open government portals, lives in `data/zoning`. It is too large to check into git, so it lives in the S3 bucket `s3://zoning-data`. In order to initialize your data directory, download all the files in this bucket into your `data` directory. Ask Hunter for a key.

```
aws configure --profile zoning
aws --profile zoning s3 sync s3://zoning-data/zoning data/zoning
```

Once the data is downloaded, you can run `python loadZoning.py outfile`. By default it will write GeoJSON, but other formats are available; see `python loadZoning.py --help`. After processing for a while, the zoning data for the cities included in the repository will be written, in standardized form, to the outfile. Yeehaw :grin:. Some variations:

```
python loadZoning.py output/california.geo.json
python loadZoning.py output/sac-sd-sf.geo.json --include sacramento sandiego sanfrancisco
python loadZoning.py output/no-sac.geo.json --exclude sacramento
```

## Saving results

After creating new output, you can upload the results for others to use:

```
aws --profile zoning s3 sync output s3://zoning-data/output
```

## Adding a new city

In order to add a new city, you will need to find the zoning data for the city in a geospatial format. Generally, this will be a Shapefile with a column containing the zoning code for each area of the city. In order to make this machine readable, we need to convert that zoning code into a number of variables. This is done using a specfile, which lists out all of the zoning codes encountered in the Shapefile and translates them into machine-readable zoning codes.

This specfile has to be created by hand based on the municipal zoning code of the city in question. However, we have tools to make this easier and faster, ~~it's really not that bad~~ it is that bad, but it could be worse. The specfile lists out all the codes and their attributes. For example, [here's one for Sacramento](https://github.com/zoningspace/zoning.space/blob/master/src/zoning/specs/sacramento.csv).

The specfile consists of several sections. The first section is a simple header that lists the jurisdiction the data is for, the URL where the data came from originally, the year of the data (so as time goes by we can tell how out of date our data is), and the column(s) in the Shapefile which contain the zoning code.

Below the header (and separated by a blank line) are a number of tables mapping the column(s) which specify the zoning to the values that we need for the machine-readable dataset. In the simplest case, there will be only one table with one matching column, but frequently things may be more complex than this. For instance, in Sacramento, a unique zoning area is designated by the BASE_ZONE, OVERLAY, and SPDNAME columns. So the first three columns of the table specify the values of those columns in the zoning shapefile. Any of the columns listed in the header can be used to match particular rules in the table. The first row of the table contains the column name(s) that should be matched in the underlying file, and the names of the zoning attributes (e.g. max height). For example, the first row of the table in the Sacramento specfile has a BASENAME of `A`, and OVERLAY and SPDNAME of `''`. This will match areas zoned `A` with no BASENAME or SPDNAME. A few rows down there is an row with BASENAME `ARP-F`, OVERLAY `SPD` and SPDNAME `River District`.

There can be multiple tables, which will be applied in order, with any attributes that are specified in multiple tables overwritten by the last table that contains them. Most cities will only need one table, but some cities have overlay zones that are not dependent on the base zones. For example, San Francisco has height districts that are separate from the zones, so there is a table that applies the height limits first, and then zoning information is applied on top of it; this way separate rules are not needed for, say, R-4 in a 40 foot zone, R-4 in a 50 foot zone, etc. How exactly this is structured will depend on the city.

To make creating specfiles simpler, there is a tool that can be used to pregenerate a template for the specfile. To use it, first download save the data into the `data/zoning` directory, as a zipped shapefile, with a "slug" (abbreviated name). For instance, San Diego might become `sandiego.zip`. Then run `python prepopulateSpecfile.py slug` to generate the specfile. This will ask you which columns from the input file you want to use for each table in your specfile. You enter the column names you want to match on, separated by commas. Once you have entered the columns for one table, it will prompt you for the next; when you have specified all the tables you desire, enter `done` at the prompt, and the specfile will be generated in `src/zoning/specs/<slug>.csv`. It will contain all the attributes for every unique combination of the columns in each table, ready to be filled out.

There are several useful options to the prepopulate script. `--drop-small-zones <sqkm>` will drop zones smaller than `<sqkm>` square kilometers. We recommend using `--drop-small-zones 0.25` to maximize productivity without losing too much data.

It is possible to enter the information in many units, to avoid having to convert units before generating the specfile. For instance, to enter the maximum height in feet rather than meters, simply change the column name from `maxHeightFeet` to `maxHeightMeters`. If the zoning code is entirely in imperial (American) units, simply call the prepopulate script with `--imperial` to generate the column names with imperial units (it's also fine to just edit them in the specfile directly if you so desire).

A few pointers for specfiles:

- If a particular zone does not allow residential, simply enter a 0 in the singleFamily and multiFamily columns; there is no need to fill in the rest of the columns, as this project is currently collecting data only on residential zoning. If a zone allows residential development with a conditional use permit, enter a C for that use type, and fill out the remainder of the column.
- If there is no minimum or maximum for a particular variable, please enter a 0 or `inf` (infinity) as appropriate to distinguish the absence of a restriction from missing data.
- If there is a range for a particular value (for instance, many special districts have height limits that vary block by block or even lot by lot), enter a range for the value by using the format, e.g., `10-20`.
- Parking is per two-bedroom unit (multifamily units where permitted, otherwise single-family units). Parking reductions as an incentive for affordable housing, etc. should not be included, but if an area has reduced parking requirements, e.g. due to transit proximity, that should be included when data is available
- Height limits should be the highest height permitted on the property by-right, without additional restrictions (such as mixed use or affordable housing). If for example there is a height limit at the property line and a separate height limit away from the property line, the higher of the two should be entered.
- If there is only a height limit specified at the setback or lot line, and a function defining max height relative to the lot line behind that, the maximum height shall be entered as the maximum height at the center of a property with the minimum lot depth, or if there is no minimum lot depth, 50 feet behind the setback line.
- Duplexes are considered single family homes for the purposes of this project. Units with three or more dwellings are multifamily.

  For instance, the San Diego Cass Street Planned District has the [following restriction](http://docs.sandiego.gov/municode/MuniCodeChapter15/Ch15Art04Division03.pdf):

  > Street facades shall be a maximum of 20 feet in height at the 10-foot set back line. All parts of the building above the established street facade shall be setback behind an imaginary plane beginning at the top of the established building street facade and sloping back toward the interior of the lot at a 45 degree angle from horizontal.

  The minimum lot depth is 100 feet. The maximum allowed height at 100 / 2 = 50 feet from the front of the lot is (50 - 10) + 20 = 60. This is 40 feet from the ten foot setback, where the height can be 20 feet.

  If the height limit is not specified at the zone level but rather on a lot-by-lot or block-by-block basis (common in planned districts), a range should be entered.

- FARs are coded likewise.
- Setbacks do not include cases that require additional restrictions, only apply for corner lots, etc. Where a setback is only required for a portion of a lot, the average setback is calculated. For instance, if a 5 foot setback is required for 50% of the frontage, the average setback is 2.5 feet. If there are different setbacks depending on building height, and there is a maximum, enter a range. If there is a formula, enter

## Advanced usage: hooks

Sometimes, there is a need for custom pre or post processing for a particular city. For example, the height regulations and the zoning data are in separate files for San Francisco, which must be combined before use. If you need to do any kind of pre or postprocessing, you can define Python hooks for the city you're working with. To do this, create a file `<slug>.py` in `src/zoning/hooks` (where slug is the same as the name of your shapefile and specfile). You can define several functions here:

  - `before (data, datadir)` receives a GeoPandas dataframe that results from reading the zipped shapefile, and should return a GeoPandas dataframe that has been processed. It is acceptable to operate destructively or in-place, so long as the data is returned. The `datadir` parameter is the path to the `data/zoning` directory, in case any ancillary data from there needs to be loaded.

The file is executed using Python's `exec` statement. Thus, if any modules or functions are imported, they must be [declared as globals in each function](https://github.com/zoningspace/zoning.space/blob/master/src/zoning/hooks/sanfrancisco.py#L13).

## Data quality

This is a detailed but still generalized dataset; in no way can every esoteric zoning code in these cities be represented easily in a common database. Thus, it should be used for informative purposes and large-scale analysis, but not to make parcel-level decisions or guide development at a parcel level.
