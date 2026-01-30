"""
API routes for map data.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Literal

from app.services.map_service import generate_map_geojson

router = APIRouter(prefix="/map", tags=["map"])


@router.get("")
async def get_map_data(
    election_year: int = Query(..., ge=2000, le=2100, description="Election year"),
    level: str = Query("province", description="Geography level: province, district, or constituency"),
    province: Optional[str] = Query(None, description="Filter by province (required for district/constituency level)"),
    district: Optional[str] = Query(None, description="Filter by district (required for constituency level)"),
    party: Optional[str] = Query(None, description="Filter by party"),
    independent: Optional[bool] = Query(None, description="Filter by independent status"),
    age_min: Optional[int] = Query(None, ge=18, le=100, description="Minimum age"),
    age_max: Optional[int] = Query(None, ge=18, le=100, description="Maximum age"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    education_level: Optional[str] = Query(None, description="Filter by education level"),
):
    """
    Get GeoJSON map data with candidate information.
    
    Drill-down hierarchy:
    - level=province: Shows all 7 provinces of Nepal
    - level=district: Shows districts (requires province filter)
    - level=constituency: Shows constituencies/election areas (requires province and district filters)
    
    Returns GeoJSON FeatureCollection with candidate IDs and aggregated metrics
    for visualization on a map.
    """
    # Validate level
    if level not in ["province", "district", "constituency"]:
        raise HTTPException(status_code=400, detail="level must be 'province', 'district', or 'constituency'")
    
    try:
        geojson = generate_map_geojson(
            election_year=election_year,
            level=level,
            province=province,
            district=district,
            party=party,
            independent=independent,
            age_min=age_min,
            age_max=age_max,
            gender=gender,
            education_level=education_level,
        )
        return geojson
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate map data: {str(e)}")
