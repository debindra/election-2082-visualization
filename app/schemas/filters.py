"""
Pydantic schemas for filter parameters.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class MapFilters(BaseModel):
    """Filters for map data requests."""
    election_year: int = Field(..., ge=2000, le=2100, description="Election year")
    province: Optional[str] = Field(None, description="Filter by province")
    district: Optional[str] = Field(None, description="Filter by district")
    party: Optional[str] = Field(None, description="Filter by party")
    independent: Optional[bool] = Field(None, description="Filter by independent status")
    age_min: Optional[int] = Field(None, ge=18, le=100, description="Minimum age")
    age_max: Optional[int] = Field(None, ge=18, le=100, description="Maximum age")
    gender: Optional[str] = Field(None, description="Filter by gender")
    education_level: Optional[str] = Field(None, description="Filter by education level")


class TrendFilters(BaseModel):
    """Filters for trend analysis requests."""
    years: List[int] = Field(..., min_items=1, description="List of election years to analyze")
    metric: Optional[str] = Field(None, description="Specific metric to analyze")


class InsightFilters(BaseModel):
    """Filters for insight requests."""
    election_year: int = Field(..., ge=2000, le=2100, description="Election year")
    compare_with: Optional[int] = Field(None, ge=2000, le=2100, description="Year to compare with")


class CompareFilters(BaseModel):
    """Filters for candidate comparison requests."""
    candidate_ids: List[str] = Field(..., min_items=1, max_items=10, description="List of candidate IDs to compare")
    election_year: Optional[int] = Field(None, ge=2000, le=2100, description="Specific election year (optional)")
