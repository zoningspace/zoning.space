# Processing Zoning Data with Zoning.Space

In order to produce usable GIS output from Zoning.Space, it is necessary to run a process to convert zoning data from city shapefiles and Zoning.Space specfiles into a standard, GIS-friendly format.

1. If you haven't already, [install Zoning.Space](installation).
1. Activate the appropriate `conda` environment, by running the command `source activate zoning.space` (or just `activate zoning.space` on Windows).
1. Download the source data from S3 by running `aws s3 sync s3://zoning-data/zoning data/zoning`. The `zoning-data` bucket is an S3 requester pays bucket. Therefore, you'll need to make an AWS account if you don't already have one, but you need no special permissions. Your AWS account will be charged for the bandwidth needed to download the data, on the order of a few cents. Zoning.Space is run entirely by volunteers, and unfortunately don't have the budget to cover bandwidth costs for everyone who might want to contribute (if you're interested in sponsoring the project, please [get in touch](mailto:hello@zoning.space)).
1. Process the data by running `python processData.py <outfile>`. If you are only interested in a particular city, you can pass the option `--include <slug>`; you can also pass multiple slugs to this option. Similarly, you can exclude cities using `--exclude <slug>`.

  The processing script defaults to GeoJSON output. To change this, pass `--driver <OGR Driver Name>` to write to a different format (e.g. `ESRI Shapefile`).

  The `outfile` should be specified before any options.
1. GIS data will be output to the outfile you specify. Processing may take quite a bit of time depending on the cities included.
1. Since most GIS output formats don't support `Infinity`, it has been represented as `2147438647`.
