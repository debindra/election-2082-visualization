"""
API routes for trend analysis.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.trend_service import compute_trends
from app.schemas.trend_response import TrendResponse, MultiTrendResponse

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("", response_model=MultiTrendResponse)
async def get_trends(
    years: str = Query(..., description="Comma-separated list of election years (e.g., '2017,2022,2026')"),
    metric: Optional[str] = Query(None, description="Specific metric to analyze"),
):
    """
    Get trend analysis across multiple election years.
    
    Supported metrics:
    - independent_shift: Independent candidate percentage trend
    - party_footprint: Party footprint index trend
    - age_trends: Candidate age trend
    - education_evolution: Education profile evolution
    - party_volatility: Party volatility index
    - candidate_density: Candidate density index
    - symbol_saturation: Symbol saturation index
    - political_churn: Political churn index
    
    If metric is not specified, returns all trends.
    """
    try:
        year_list = [int(y.strip()) for y in years.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid years format. Use comma-separated integers.")
    
    if len(year_list) < 1:
        raise HTTPException(status_code=400, detail="At least 1 year required")
    
    try:
        trends_data = compute_trends(year_list, metric)
        
        # Convert to response format
        trends = {}
        for metric_name, trend_data in trends_data.items():
            trends[metric_name] = TrendResponse(
                metric=trend_data["metric"],
                data_points=[
                    {
                        "year": dp["year"],
                        "value": dp["value"],
                        "metadata": dp.get("metadata"),
                    }
                    for dp in trend_data["data_points"]
                ],
            )
        
        return MultiTrendResponse(trends=trends)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute trends: {str(e)}")
