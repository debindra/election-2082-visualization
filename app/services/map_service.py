"""
Service for generating map data (GeoJSON) with candidate information.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import logging


def _sanitize_for_json(obj: Any) -> Any:
    """Replace NaN/inf with None so the result is JSON-serializable."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, float) and (pd.isna(obj) or abs(obj) == float("inf")):
        return None
    return obj

from app.core.config import DATA_DIR
from app.data.loader import loader
from app.data.schema_notes import DISTRICT_TO_PROVINCE
from app.utils.indices import aggregate_metrics_by_geography

logger = logging.getLogger(__name__)

# Path to Nepal 75-district GeoJSON (from geoJSON-Nepal; see data/geojson/README.md)
GEOJSON_DISTRICTS_PATH = DATA_DIR / "geojson" / "nepal-districts.geojson"

# Cached: GeoJSON DISTRICT key (uppercase) -> geometry dict
_district_geometries_cache: Optional[Dict[str, Dict]] = None

# One-time: Nepali district name -> GeoJSON DISTRICT key (from DISTRICT_TO_PROVINCE order: nepali, english pairs)
_nepali_to_geo_key_cache: Optional[Dict[str, str]] = None


def _nepali_to_geo_key() -> Dict[str, str]:
    """Build map from Nepali district name to GeoJSON DISTRICT (uppercase). Schema lists (nepali, english) pairs consecutively."""
    global _nepali_to_geo_key_cache
    if _nepali_to_geo_key_cache is not None:
        return _nepali_to_geo_key_cache
    out: Dict[str, str] = {}
    items = list(DISTRICT_TO_PROVINCE.items())
    for i in range(0, len(items) - 1, 2):
        k1, k2 = items[i][0], items[i + 1][0]
        if not k1.isascii() and k2.isascii():
            out[k1] = k2.upper()
    _nepali_to_geo_key_cache = out
    return out


def _first_en(df: pd.DataFrame, col: str) -> Optional[str]:
    """First non-null value from column, or None if column missing or all null."""
    if col not in df.columns:
        return None
    val = df[col].dropna()
    if len(val) == 0:
        return None
    v = str(val.iloc[0]).strip()
    return v if v else None


def _party_distribution_en(df: pd.DataFrame, party_distribution: Dict) -> Optional[Dict]:
    """Build party -> count using English names when available (for card display)."""
    if not party_distribution or "party_en" not in df.columns or "party" not in df.columns:
        return None
    en_dist = {}
    for party, count in party_distribution.items():
        rows = df[df["party"].astype(str).str.strip() == str(party).strip()]
        en_name = str(rows["party_en"].iloc[0]).strip() if len(rows) > 0 and pd.notna(rows["party_en"].iloc[0]) else party
        en_dist[en_name] = en_dist.get(en_name, 0) + int(count or 0)
    return en_dist if en_dist else None


def _match_col_or_en(
    df: pd.DataFrame,
    main_col: str,
    en_col: str,
    value: str,
    extra_cols: Optional[List[str]] = None,
) -> pd.Series:
    """Boolean series: row matches value in main_col, en_col, or any extra_cols (when present)."""
    m = df[main_col].astype(str).str.contains(value, case=False, na=False)
    if en_col in df.columns:
        m = m | df[en_col].fillna("").astype(str).str.contains(value, case=False)
    for col in extra_cols or []:
        if col in df.columns:
            m = m | df[col].fillna("").astype(str).str.contains(value, case=False)
    return m


# Nepal's 7 provinces with approximate center coordinates
NEPAL_PROVINCES = {
    "Province 1": {"center": [87.5, 27.0], "bounds": [[86.5, 26.3], [88.2, 27.9]]},
    "Madhesh": {"center": [85.9, 26.7], "bounds": [[84.8, 26.3], [87.0, 27.1]]},
    "Bagmati": {"center": [85.5, 27.8], "bounds": [[84.5, 27.2], [86.5, 28.4]]},
    "Gandaki": {"center": [84.0, 28.3], "bounds": [[83.0, 27.8], [85.0, 29.0]]},
    "Lumbini": {"center": [83.0, 27.8], "bounds": [[82.0, 27.2], [84.0, 28.4]]},
    "Karnali": {"center": [82.0, 29.0], "bounds": [[81.0, 28.3], [83.0, 30.0]]},
    "Sudurpashchim": {"center": [80.5, 29.2], "bounds": [[80.0, 28.5], [81.5, 30.2]]},
}


def generate_map_geojson(
    election_year: int,
    level: str = "province",
    province: Optional[str] = None,
    district: Optional[str] = None,
    party: Optional[str] = None,
    independent: Optional[bool] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    gender: Optional[str] = None,
    education_level: Optional[str] = None,
) -> Dict:
    """
    Generate GeoJSON for map visualization with candidate data.
    
    Supports drill-down hierarchy:
    - level=province: Shows all 7 provinces
    - level=district: Shows districts within selected province
    - level=constituency: Shows constituencies (election areas) within selected district
    
    Args:
        election_year: Election year
        level: Geography level (province, district, or constituency)
        province: Filter by province (required for district/constituency level)
        district: Filter by district (required for constituency level)
        party: Filter by party
        independent: Filter by independent status
        age_min: Minimum age filter
        age_max: Maximum age filter
        gender: Gender filter
        education_level: Education level filter
        
    Returns:
        GeoJSON FeatureCollection with candidate data for the specified level only
    """
    try:
        df, _ = loader.load_election(election_year)
    except Exception as e:
        logger.error(f"Failed to load election {election_year}: {e}")
        raise
    
    # Apply filters (match main and _en columns when present)
    filtered_df = df.copy()
    
    if province:
        filtered_df = filtered_df[_match_col_or_en(filtered_df, "province", "province_en", province, extra_cols=["province_np"])]
    if district:
        filtered_df = filtered_df[_match_col_or_en(filtered_df, "district", "district_en", district)]
    if party:
        filtered_df = filtered_df[_match_col_or_en(filtered_df, "party", "party_en", party)]
    if independent is not None and "is_independent" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["is_independent"] == independent]
    if age_min is not None and "age" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["age"] >= age_min]
    if age_max is not None and "age" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["age"] <= age_max]
    if gender and "gender" in filtered_df.columns:
        g_val = str(gender).strip().upper()
        filtered_df = filtered_df[filtered_df["gender"].fillna("").astype(str).str.upper() == g_val]
    if education_level and "education_level" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["education_level"].str.contains(education_level, case=False, na=False)]
    
    features = []
    
    # Generate features for the requested level ONLY
    if level == "province" and "province" in filtered_df.columns:
        for prov in filtered_df["province"].unique():
            prov_df = filtered_df[filtered_df["province"] == prov]
            metrics = aggregate_metrics_by_geography(prov_df, "province", include_candidate_ids=True)
            
            if metrics:
                props = dict(metrics[0])
                name_en = _first_en(prov_df, "province_en")
                if name_en:
                    props["name_en"] = name_en
                party_en_dist = _party_distribution_en(prov_df, props.get("party_distribution") or {})
                if party_en_dist:
                    props["party_distribution_en"] = party_en_dist
                props["geography_level"] = "province"
                props["drilldown_to"] = "district"
                feature = {
                    "type": "Feature",
                    "geometry": _get_province_geometry(prov),
                    "properties": props,
                }
                features.append(feature)
    
    elif level == "district" and "district" in filtered_df.columns:
        for dist in filtered_df["district"].unique():
            dist_df = filtered_df[filtered_df["district"] == dist]
            metrics = aggregate_metrics_by_geography(dist_df, "district", include_candidate_ids=True)
            
            if metrics:
                props = dict(metrics[0])
                name_en = _first_en(dist_df, "district_en")
                if name_en:
                    props["name_en"] = name_en
                province_en = _first_en(dist_df, "province_en")
                if province_en:
                    props["province_en"] = province_en
                party_en_dist = _party_distribution_en(dist_df, props.get("party_distribution") or {})
                if party_en_dist:
                    props["party_distribution_en"] = party_en_dist
                props["geography_level"] = "district"
                props["drilldown_to"] = "constituency"
                feature = {
                    "type": "Feature",
                    "geometry": _get_district_geometry(dist, province),
                    "properties": props,
                }
                features.append(feature)
    
    elif level == "constituency" and "constituency" in filtered_df.columns:
        for const in filtered_df["constituency"].unique():
            const_df = filtered_df[filtered_df["constituency"] == const]
            metrics = aggregate_metrics_by_geography(const_df, "constituency", include_candidate_ids=True)
            
            if metrics:
                # Use election_area_display for user-friendly name (e.g., "इलाम - १")
                display_name = const
                if "election_area_display" in const_df.columns:
                    display_values = const_df["election_area_display"].dropna().unique()
                    if len(display_values) > 0:
                        display_name = display_values[0]
                # English display name: district_en + " - " + number from display_name
                display_name_en = None
                district_en_val = _first_en(const_df, "district_en")
                if district_en_val:
                    num_match = re.search(r"[-–—]\s*([०१२३४५६७८९\d]+)\s*$", str(display_name))
                    num_part = num_match.group(1) if num_match else ""
                    display_name_en = f"{district_en_val} - {num_part}" if num_part else district_en_val
                props = dict(metrics[0])
                props["display_name"] = display_name
                if display_name_en:
                    props["display_name_en"] = display_name_en
                if district_en_val:
                    props["district_en"] = district_en_val
                province_en_val = _first_en(const_df, "province_en")
                if province_en_val:
                    props["province_en"] = province_en_val
                party_en_dist = _party_distribution_en(const_df, props.get("party_distribution") or {})
                if party_en_dist:
                    props["party_distribution_en"] = party_en_dist
                props["geography_level"] = "constituency"
                props["drilldown_to"] = None
                feature = {
                    "type": "Feature",
                    "geometry": _get_constituency_geometry(const, district, province),
                    "properties": props,
                }
                features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "level": level,
            "province_filter": province,
            "district_filter": district,
            "total_features": len(features),
        }
    }
    return _sanitize_for_json(geojson)


def _get_province_geometry(name: str) -> Dict:
    """
    Generate geometry for a province.
    Uses approximate boundaries for Nepal's 7 provinces.
    """
    # Try to match province name to known provinces
    province_key = None
    name_lower = name.lower()
    
    for key in NEPAL_PROVINCES:
        if key.lower() in name_lower or name_lower in key.lower():
            province_key = key
            break
    
    if province_key and province_key in NEPAL_PROVINCES:
        bounds = NEPAL_PROVINCES[province_key]["bounds"]
        sw, ne = bounds
        return {
            "type": "Polygon",
            "coordinates": [[
                [sw[0], sw[1]],
                [ne[0], sw[1]],
                [ne[0], ne[1]],
                [sw[0], ne[1]],
                [sw[0], sw[1]],
            ]],
        }
    
    # Fallback: generate based on hash within Nepal bounds
    return _generate_polygon_in_nepal(name, size=1.5)


def _load_district_geojson() -> Dict[str, Dict]:
    """
    Load Nepal districts GeoJSON and return a map: DISTRICT (uppercase) -> geometry.
    Returns empty dict if file is missing or invalid.
    """
    global _district_geometries_cache
    if _district_geometries_cache is not None:
        return _district_geometries_cache
    out: Dict[str, Dict] = {}
    if not GEOJSON_DISTRICTS_PATH.exists():
        logger.debug("District GeoJSON not found at %s; using synthetic geometries", GEOJSON_DISTRICTS_PATH)
        _district_geometries_cache = out
        return out
    try:
        with open(GEOJSON_DISTRICTS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        for feat in data.get("features") or []:
            props = feat.get("properties") or {}
            district_key = props.get("DISTRICT")
            geom = feat.get("geometry")
            if district_key and geom:
                out[str(district_key).strip().upper()] = geom
        _district_geometries_cache = out
        logger.info("Loaded %d district geometries from %s", len(out), GEOJSON_DISTRICTS_PATH)
    except Exception as e:
        logger.warning("Failed to load district GeoJSON: %s", e)
    _district_geometries_cache = out
    return _district_geometries_cache


def _district_name_to_geo_key(name: str) -> Optional[str]:
    """
    Resolve our district name (Nepali or English) to GeoJSON DISTRICT key (uppercase).
    GeoJSON uses properties.DISTRICT like 'KATHMANDU', 'HUMLA'.
    """
    if not name or not str(name).strip():
        return None
    s = str(name).strip()
    geojson_keys = _load_district_geojson()
    # Nepali name (non-ASCII): resolve via prebuilt map first
    if not s.isascii():
        nepali_map = _nepali_to_geo_key()
        if s in nepali_map:
            return nepali_map[s]
    # Direct match: English (e.g. Kathmandu) -> uppercase
    key_upper = s.upper()
    if key_upper in geojson_keys:
        return key_upper
    # Match GeoJSON DISTRICT (case-insensitive)
    for geo_key in geojson_keys:
        if geo_key.upper() == key_upper or geo_key.lower() == s.lower():
            return geo_key
    # Resolve via DISTRICT_TO_PROVINCE: English keys are lowercase (e.g. humla, kathmandu)
    if s.isascii() and s.lower() in DISTRICT_TO_PROVINCE:
        return s.upper()
    return None


def _get_district_geometry(name: str, province: Optional[str] = None) -> Dict:
    """
    Generate geometry for a district. Uses real boundaries from data/geojson/nepal-districts.geojson
    when available; otherwise synthetic polygon within province bounds or Nepal.
    """
    geo_key = _district_name_to_geo_key(name)
    if geo_key:
        geoms = _load_district_geojson()
        if geo_key in geoms:
            return geoms[geo_key]
    # Fallback: province bounds or hash-based polygon
    if province:
        for key in NEPAL_PROVINCES:
            if key.lower() in province.lower() or province.lower() in key.lower():
                bounds = NEPAL_PROVINCES[key]["bounds"]
                return _generate_polygon_in_bounds(name, bounds, size=0.5)
    return _generate_polygon_in_nepal(name, size=0.5)


def _get_constituency_geometry(name: str, district: Optional[str] = None, province: Optional[str] = None) -> Dict:
    """
    Generate geometry for a constituency (election area) - smallest unit.
    """
    # Get province bounds if available
    if province:
        for key in NEPAL_PROVINCES:
            if key.lower() in province.lower() or province.lower() in key.lower():
                bounds = NEPAL_PROVINCES[key]["bounds"]
                return _generate_polygon_in_bounds(name, bounds, size=0.2)
    
    # Fallback
    return _generate_polygon_in_nepal(name, size=0.2)


def _generate_polygon_in_nepal(name: str, size: float = 0.5) -> Dict:
    """
    Generate a polygon within Nepal's bounds based on name hash.
    """
    # Nepal approximate bounds
    min_lon, max_lon = 80.0, 88.2
    min_lat, max_lat = 26.3, 30.4
    
    # Hash-based positioning
    hash_val = abs(hash(name))
    lon_range = max_lon - min_lon - size
    lat_range = max_lat - min_lat - size
    
    base_lon = min_lon + (hash_val % 1000) / 1000.0 * lon_range
    base_lat = min_lat + ((hash_val // 1000) % 1000) / 1000.0 * lat_range
    
    return {
        "type": "Polygon",
        "coordinates": [[
            [base_lon, base_lat],
            [base_lon + size, base_lat],
            [base_lon + size, base_lat + size * 0.6],
            [base_lon, base_lat + size * 0.6],
            [base_lon, base_lat],
        ]],
    }


def _generate_polygon_in_bounds(name: str, bounds: List, size: float = 0.3) -> Dict:
    """
    Generate a polygon within specified bounds.
    """
    sw, ne = bounds
    min_lon, min_lat = sw
    max_lon, max_lat = ne
    
    # Hash-based positioning within bounds
    hash_val = abs(hash(name))
    lon_range = max_lon - min_lon - size
    lat_range = max_lat - min_lat - size
    
    if lon_range <= 0:
        lon_range = 0.1
    if lat_range <= 0:
        lat_range = 0.1
    
    base_lon = min_lon + (hash_val % 1000) / 1000.0 * lon_range
    base_lat = min_lat + ((hash_val // 1000) % 1000) / 1000.0 * lat_range
    
    return {
        "type": "Polygon",
        "coordinates": [[
            [base_lon, base_lat],
            [base_lon + size, base_lat],
            [base_lon + size, base_lat + size * 0.6],
            [base_lon, base_lat + size * 0.6],
            [base_lon, base_lat],
        ]],
    }
