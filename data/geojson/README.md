# Nepal GeoJSON Data

This folder holds GeoJSON files for Nepal’s administrative and election geography, used for map visualization (e.g. [election.onlinekhabar.com](https://election.onlinekhabar.com/) style views).

## Contents

| File | Description | Source |
|------|-------------|--------|
| `nepal-districts.geojson` | All **75 districts** of Nepal with polygon boundaries | [geoJSON-Nepal](https://github.com/mesaugat/geoJSON-Nepal) (archived). Each feature has `properties.DISTRICT` (uppercase English, e.g. `"KATHMANDU"`, `"HUMLA"`). |

## District-level data

- **Source**: [mesaugat/geoJSON-Nepal](https://github.com/mesaugat/geoJSON-Nepal) — `nepal-districts.geojson`
- **Direct URL**: `https://raw.githubusercontent.com/mesaugat/geoJSON-Nepal/master/nepal-districts.geojson`
- **License**: MIT  
- **Note**: Repository was archived in 2020; the file is still available for download.

## Election areas (constituencies)

- **165 constituencies** (प्रतिनिधिसभा निर्वाचन क्षेत्र) are not provided here as a single GeoJSON.
- The [Election Commission of Nepal](https://election.gov.np/en/page/district-wise-constituency-map) publishes district-wise constituency maps (e.g. PDFs), not a consolidated GeoJSON.
- The app uses **district-level** GeoJSON for district view and **synthetic (placeholder) polygons** for province and constituency views when real boundaries are not available.

## Refreshing the data

To re-download the districts GeoJSON:

```bash
# From project root
curl -sL "https://raw.githubusercontent.com/mesaugat/geoJSON-Nepal/master/nepal-districts.geojson" \
  -o data/geojson/nepal-districts.geojson
```

Or run the script from the project root:

```bash
./scripts/fetch_nepal_geojson.sh
```

## Other sources (reference)

- [Acesmndr/nepal-geojson](https://github.com/Acesmndr/nepal-geojson) — lightweight district GeoJSON (standard and high-res).
- [Open Data Nepal](https://opendatanepal.com/dataset/geojson-file-of-all-75-districts-of-nepal) — 75 districts, Ministry of Federal Affairs and General Administration.
- [opentechcommunity/map-of-nepal](https://github.com/opentechcommunity/map-of-nepal) — provinces, districts, municipalities.
