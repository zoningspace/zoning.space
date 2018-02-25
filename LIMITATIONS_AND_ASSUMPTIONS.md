# General assumptions and limitations

- Parking and density requirements are per 1000-square-foot, two-bedroom unit (multifamily units where permitted, otherwise single-family units), with four habitable rooms. Parking reductions as an incentive for affordable housing, etc. should not be included, but if an area has reduced parking requirements, e.g. due to transit proximity, that should be included when data is available
- Height limits should be the highest height permitted on the property by-right, without additional restrictions (such as mixed use or affordable housing). If for example there is a height limit at the property line and a separate height limit away from the property line, the higher of the two should be entered.
- If there is only a height limit specified at the setback or lot line, and a function defining max height relative to the lot line behind that, the maximum height shall be entered as the maximum height at the center of a property with the minimum lot depth, or if there is no minimum lot depth, 50 feet behind the setback line.
- Duplexes are considered single family homes for the purposes of this project.

  For instance, the San Diego Cass Street Planned District has the [following restriction](http://docs.sandiego.gov/municode/MuniCodeChapter15/Ch15Art04Division03.pdf):

  > Street facades shall be a maximum of 20 feet in height at the 10-foot set back line. All parts of the building above the established street facade shall be setback behind an imaginary plane beginning at the top of the established building street facade and sloping back toward the interior of the lot at a 45 degree angle from horizontal.

  The minimum lot depth is 100 feet. The maximum allowed height at 100 / 2 = 50 feet from the front of the lot is (50 - 10) + 20 = 60. This is 40 feet from the ten foot setback, where the height can be 20 feet.

  If the height limit is not specified at the zone level but rather on a lot-by-lot or block-by-block basis (common in planned districts), the lowest height limit should be used.

- FARs are coded likewise.
- Setbacks do not include cases that require additional restrictions, only apply for corner lots, etc. Where a setback is only required for a portion of a lot, the average setback is calculated. For instance, if a 5 foot setback is required for 50% of the frontage, the average setback is 2.5 feet. If there are different setbacks depending on building height, the smallest is used.
- When there are interior and street side setbacks specified, the interior setback should be recorded.
- Existing state-level land use controls are not included (for instance in port areas), except to the extent that they are reflected in local law as well.

### San Diego

- No overlays, not specified in zoning file. Some planned districts include their own codes, which are included. Those that modify existing codes are not included.
- Maximum FARs in Centre City Planned District do not follow zone designations and this it is not possible to include them.
- The Mid-City Communities Zone has been repealed but is still present in the source data. The area is small.
- Transit overlay and Parking Impact Overlay zones are not included due to lack of data. They make the parking requirements .25 spaces per unit higher or lower.
- The Mission Valley Community Plan zones in the file bear no resemblance to those in the municipal code.

## Sacramento

- Some overlay zones are not documented and therefore not overlaid (e.g. R)
- Floor area ratios are referenced as being defined in the general plan, but I can't find where

## San Francisco :bridge_at_night:
- TRANSIT CENTER C-3-O(SD) COMMERCIAL SPECIAL USE DISTRICT restricts the amount of residential allowed in mixed-use buildings, this is not represented in the model
- Special use districts smaller than 0.25 square kilometers are not represented, and the areas within them are shown as if there were no special use district
- Neighborhood Commercial districts (except for Excelsior, Japantown, and all Neighborhood Commercial Transit districts) have a density limit specified but also the note that if the nearest R zone has a higher density zoning, that it should prevail. This is not represented in the output.

# San Jose
- Planned Developments have density reported by the city, and use codes that we guessed at - we can generally determine if a project permits residential or not, but can't really determine if it's multifamily or only single family. It should be noted that PDs are kind of like nonconforming uses; they can't easily be built again when they wear out. For some analyses it may make sense to drop them.
- Height limits from specific plans and urban villages are not included due to data availability concerns.

# Oakland
- We do not have data on the height/bulk/intensity districts, so some zones have wide ranges of what may be permitted in different height/bulk/intensity districts
  - CN zones in the 35* height district take on the density of nearest RH, RD or RM zone. This is not reflected in the data (not even in the ranges).
