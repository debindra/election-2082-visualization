"""
API routes for candidate comparison.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import math

from app.services.compare_service import compare_candidates, search_candidates
from app.schemas.candidate import CandidateComparison, CandidateInfo, CandidateSearchResult

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("/candidates", response_model=CandidateComparison)
async def compare_candidates_by_id(
    candidate_ids: str = Query(..., description="Comma-separated list of candidate IDs"),
    election_year: Optional[int] = Query(None, ge=2000, le=2100, description="Specific election year (optional)"),
):
    """
    Compare candidates by their IDs.
    
    Args:
        candidate_ids: Comma-separated list of candidate IDs (e.g., "C001,C002,C003")
        election_year: Optional specific election year. If not provided, searches across all elections.
    
    Returns:
        Candidate comparison data with candidate information and comparison metrics.
    """
    try:
        id_list = [id.strip() for id in candidate_ids.split(",") if id.strip()]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate_ids format. Use comma-separated IDs.")
    
    if len(id_list) < 1:
        raise HTTPException(status_code=400, detail="At least 1 candidate ID required")
    
    try:
        comparison_data = compare_candidates(id_list, election_year)
        
        # Convert to response format
        candidates = {}
        for candidate_id, candidate_dict in comparison_data["candidates"].items():
            # Clean up NaN/non-JSON-friendly values before validation
            cleaned = {
                k: (None if isinstance(v, float) and math.isnan(v) else v)
                for k, v in candidate_dict.items()
            }
            candidates[candidate_id] = CandidateInfo(**cleaned)
        
        return CandidateComparison(
            candidates=candidates,
            comparison_metrics=comparison_data["comparison_metrics"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare candidates: {str(e)}")


@router.get("/candidates/search", response_model=List[CandidateSearchResult])
async def search_candidates_autocomplete(
    q: str = Query(..., min_length=1, description="Search by candidate name or ID"),
    limit: int = Query(5, ge=1, le=10, description="Max results (default 5)"),
    election_year: Optional[int] = Query(None, ge=2000, le=2100, description="Optional election year filter"),
):
    """
    Search candidates by name or ID. Returns top 5 matches for autocomplete.
    """
    try:
        results = search_candidates(query=q, limit=limit, election_year=election_year)
        return [CandidateSearchResult(**r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
