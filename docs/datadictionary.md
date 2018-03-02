# Zoning.Space data dictionary

These are the ~voyages of the starship Enterprise~ variables present in the Zoning.Space dataset. In the input specfiles, note that units may be specified differently (for instance, `maxHeightFeet` is allowable rather than `maxHeightMeters`). In output files, note that all numeric fields will be prefixed with `hi` and `lo` to indicate the low and high ends of the ranges of that limiation within a particular zone (for instance, some zones may have height limits that depend on information we can't digitize easily, such as slope or original purchase date). More often than not, there will be a single value rather than a range, and the `lo` value will equal the `hi` value.

singleFamily: Are single-family uses (including duplexes) permitted in this zone? Can be `yes`, `no`, or `conditional`.

multiFamily: Are multi-family uses (apartments/condos) permitted in this zone? Can be `yes`, `no`, or `conditional`.

maxHeightMeters: The maximum height of residential buildings constructed by-right in this zone.

maxHeightStories: The maximum height of residential buildings constructed by-right in this zone, if the city specifies this in stories rather than meters or feet.

minLotSizePerUnitHectares: The minimum lot area required for each unit. Implies a minimum density. This is per 1000-square-foot, two-bedroom unit (multifamily units where permitted, otherwise single-family units), with four habitable rooms.

maxUnitsPerLot: The maximum number of units that may be built on a lot. Combined with `minLotSizeHectares`, implies a minimum density. Should be set to 1 in areas that allow only single family development and don't allow multiple single family units on one lot.

minUnitsPerLot: The minimum number of units that may be be built on a lot.

minLotSizeHectares: The minimum size of a lot. Combined with `maxUnitsPerLot`, implies a minimum density.

maxLotSizeHectares: The maximum size of a lot.

minLotWidthMeters: The minimum width of a lot.

maxLotWidthMeters: The maximum width of a lot.

minLotDepthMeters: The minimum depth of a lot.

minFloorAreaPerUnitSqMeters: The minimum size of a housing unit.

minParkingPerUnit: The minimum parking for a housing unit. Since some cities define this based on bedrooms, and some based on square footage, this is per 1000-square-foot, two-bedroom unit (multifamily units where permitted, otherwise single-family units), with four habitable rooms. Parking reductions as an incentive for affordable housing, etc. should not be included, but if an area has reduced parking requirements, e.g. due to transit proximity, that should be included when data is available

maxParkingPerUnit: Maximum parking, again for a 1000-square-foot, two-bedroom unit.

maxUnitsPerHectare: The maximum density of housing units, per 1000-square-foot, two-bedroom unit (multifamily units where permitted, otherwise single-family units), with four habitable rooms. This variable can be entered directly; when the data is [processed](processing), it will be replaced with the minimum density implied by `maxUnitsPerHectare`, `minLotSizePerUnitHectares`, or the combination of `minLotSizeHectares` and `maxUnitsPerLot`.

maxLotCoverage: The maximum percentage of the lot that may be covered by residential construction.

maxFar: The maximum floor area ratio of residential construction here.

setbackFrontMeters: The front (street) setback.

setbackFrontPercent: Alternate specification for the front (street) setback, in percentage of lot depth.

setbackSideMeters: The side setback; where separate street-side and interior setbacks are used, the interior setback should be entered here.

setbackSidePercent: Alternate specification for side setback.

setbackRearMeters: The rear setback.

setbackRearPercent: Alternate specification for the rear setback.

demoControls: Whether there are demolition controls (e.g. on affordable housing) in this area. Currently, data is not present in this field for most cities.

zone: The zoning designation for this area (no need to enter this in specfiles). This is all of the fields used in the specifle, concatenated with a `-`.

note: Any notes from the person who digitized the zoning code about this zone.
