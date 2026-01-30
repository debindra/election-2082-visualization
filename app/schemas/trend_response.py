"""
Pydantic schemas for trend analysis responses.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class TrendDataPoint(BaseModel):
    """Single data point in a trend."""
    year: int = Field(..., description="Election year")
    value: float = Field(..., description="Metric value")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TrendResponse(BaseModel):
    """Trend analysis response."""
    metric: str = Field(..., description="Metric name")
    data_points: List[TrendDataPoint] = Field(..., description="Trend data points")
    summary: Optional[Dict[str, Any]] = Field(None, description="Summary statistics")


class MultiTrendResponse(BaseModel):
    """Multiple trend analysis response."""
    trends: Dict[str, TrendResponse] = Field(..., description="Trends by metric name")
