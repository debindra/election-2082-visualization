"""
Pydantic schemas for candidate data.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CandidateInfo(BaseModel):
    """Candidate information."""
    candidate_id: str = Field(..., description="Unique candidate identifier")
    candidate_name: Optional[str] = Field(None, description="Candidate name")
    party: Optional[str] = Field(None, description="Political party")
    is_independent: Optional[bool] = Field(None, description="Independent candidate flag")
    district: Optional[str] = Field(None, description="District name")
    constituency: Optional[str] = Field(None, description="Constituency identifier")
    election_area_display: Optional[str] = Field(
        None,
        description="निर्वाचन क्षेत्र display name (e.g. district - number)",
    )
    province: Optional[str] = Field(None, description="Province name")
    election_year: Optional[int] = Field(None, description="Election year")
    age: Optional[float] = Field(None, description="Candidate age")
    gender: Optional[str] = Field(None, description="Gender")
    education_level: Optional[str] = Field(None, description="Education level")
    birth_district: Optional[str] = Field(None, description="Birth district")
    symbol: Optional[str] = Field(None, description="Election symbol")
    image_url: Optional[str] = Field(None, description="URL of candidate photo/image")
    votes_received: Optional[float] = Field(None, description="Votes received")
    votes_percentage: Optional[float] = Field(None, description="Vote percentage")
    is_winner: Optional[bool] = Field(None, description="Winner flag")
    margin: Optional[float] = Field(None, description="Victory margin")
    candidate_name_en: Optional[str] = Field(None, description="Candidate full name in English")
    district_en: Optional[str] = Field(None, description="District in English")
    birth_place_en: Optional[str] = Field(None, description="Birth place in English")
    party_en: Optional[str] = Field(None, description="Political party in English")
    province_en: Optional[str] = Field(None, description="State/Province in English")
    province_np: Optional[str] = Field(None, description="State name in Nepali")
    vote_share_in_race: Optional[float] = Field(
        None,
        description="Candidate's vote share within their constituency/district race (0-100, if computable)",
    )
    party_strength_in_district: Optional[float] = Field(
        None,
        description="Party's share of total votes in the candidate's district (0-100, if computable)",
    )
    party_incumbent_in_constituency: Optional[bool] = Field(
        None,
        description="Whether this candidate's party held the seat in the previous election (if data available)",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "C001",
                "candidate_name": "John Doe",
                "party": "Nepal Congress",
                "is_independent": False,
                "district": "Kathmandu",
                "constituency": "Kathmandu-1",
                "province": "Bagmati",
                "election_year": 2022,
                "age": 45,
                "gender": "M",
                "education_level": "Masters",
            }
        }


class CandidateSearchResult(BaseModel):
    """Single candidate in search/autocomplete results."""
    candidate_id: str = Field(..., description="Unique candidate identifier")
    candidate_name: Optional[str] = Field(None, description="Candidate name")
    party: Optional[str] = Field(None, description="Political party")
    election_year: Optional[int] = Field(None, description="Election year")
    candidate_name_en: Optional[str] = Field(None, description="Candidate full name in English")
    district_en: Optional[str] = Field(None, description="District in English")
    birth_place_en: Optional[str] = Field(None, description="Birth place in English")
    party_en: Optional[str] = Field(None, description="Political party in English")
    province_en: Optional[str] = Field(None, description="State/Province in English")
    province_np: Optional[str] = Field(None, description="State name in Nepali")


class CandidateComparison(BaseModel):
    """Candidate comparison result."""
    candidates: Dict[str, CandidateInfo] = Field(..., description="Candidate information by ID")
    comparison_metrics: Dict[str, Any] = Field(default_factory=dict, description="Comparison metrics")
