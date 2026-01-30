#!/usr/bin/env bash
# Fetch Nepal districts GeoJSON (75 districts).
# Source: https://github.com/mesaugat/geoJSON-Nepal (archived)
# See data/geojson/README.md for details.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GEOJSON_DIR="$PROJECT_ROOT/data/geojson"
DISTRICTS_URL="https://raw.githubusercontent.com/mesaugat/geoJSON-Nepal/master/nepal-districts.geojson"

mkdir -p "$GEOJSON_DIR"
echo "Downloading Nepal districts GeoJSON to $GEOJSON_DIR/nepal-districts.geojson ..."
curl -sL "$DISTRICTS_URL" -o "$GEOJSON_DIR/nepal-districts.geojson"
echo "Done. $(python3 -c "import json; d=json.load(open('$GEOJSON_DIR/nepal-districts.geojson')); print(len(d.get('features',[])), 'districts')")"
