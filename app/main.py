"""
FastAPI main application for Nepal House of Representatives Election Data API.

Longitudinal Election Data Visualization & Insight System.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import httpx
from typing import Dict, Any

from app.core.config import API_V1_PREFIX, API_TITLE, API_DESCRIPTION, API_VERSION, ELECTIONS_DIR
from app.core.settings import settings
from app.data.loader import loader, ElectionDataLoader
from app.data.validator import ValidationResult
from app.data.schema_notes import REQUIRED_COLUMNS, OPTIONAL_COLUMNS
from app.api.routes import map, trends, insights, compare
from pydantic import BaseModel
import sys
from pathlib import Path as PathLibPath

# Add RAG directory to path for imports
sys.path.insert(0, str(PathLibPath(__file__).resolve().parent.parent / "rag-qa"))

# Province display order (Nepali official names)
PROVINCE_DISPLAY_ORDER = [
    "कोशी प्रदेश",
    "मधेश प्रदेश",
    "बागमती प्रदेश",
    "गण्डकी प्रदेश",
    "लुम्बिनी प्रदेश",
    "कर्णाली प्रदेश",
    "सुदूरपश्चिम प्रदेश",
]

# Map common province name variants (English/Nepali) to this order
PROVINCE_ORDER_RANK = {
    # Province 1 / Koshi
    "कोशी प्रदेश": 0,
    "Province 1": 0,
    "Koshi": 0,
    "Koshi Province": 0,
    # Province 2 / Madhesh
    "मधेश प्रदेश": 1,
    "Province 2": 1,
    "Madhesh": 1,
    "Madhesh Province": 1,
    # Province 3 / Bagmati
    "बागमती प्रदेश": 2,
    "Province 3": 2,
    "Bagmati": 2,
    "Bagmati Province": 2,
    # Province 4 / Gandaki
    "गण्डकी प्रदेश": 3,
    "Province 4": 3,
    "Gandaki": 3,
    "Gandaki Province": 3,
    # Province 5 / Lumbini
    "लुम्बिनी प्रदेश": 4,
    "Province 5": 4,
    "Lumbini": 4,
    "Lumbini Province": 4,
    # Province 6 / Karnali
    "कर्णाली प्रदेश": 5,
    "Province 6": 5,
    "Karnali": 5,
    "Karnali Province": 5,
    # Province 7 / Sudurpashchim (Sudurpachim)
    "सुदूरपश्चिम प्रदेश": 6,
    "Province 7": 6,
    "Sudurpashchim": 6,
    "Sudurpashchim Province": 6,
    "Sudurpachim": 6,
    "Sudurpachim Province": 6,
}
# DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def _match_col_or_en(
    df: pd.DataFrame,
    main_col: str,
    en_col: str,
    value: str,
    extra_cols: Optional[List[str]] = None,
) -> pd.Series:
    """Boolean series: row matches value in main_col, en_col, or any extra_cols (when present).
    Uses regex=False to prevent ReDoS from user-controlled input."""
    m = df[main_col].astype(str).str.contains(value, case=False, na=False, regex=False)
    if en_col in df.columns:
        m = m | df[en_col].fillna("").astype(str).str.contains(value, case=False, na=False, regex=False)
    for col in extra_cols or []:
        if col in df.columns:
            m = m | df[col].fillna("").astype(str).str.contains(value, case=False, na=False, regex=False)
    return m


def province_sort_key(name: Optional[str]) -> int:
    """
    Sort provinces according to PROVINCE_DISPLAY_ORDER, handling name variants.
    Unknown names are placed at the end.
    """
    if not name:
        return len(PROVINCE_DISPLAY_ORDER) + 1
    
    if name in PROVINCE_ORDER_RANK:
        return PROVINCE_ORDER_RANK[name]
    
    name_lower = name.lower()
    for key, rank in PROVINCE_ORDER_RANK.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return rank
    
    return len(PROVINCE_DISPLAY_ORDER) + 1


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=API_DESCRIPTION,
    version=settings.api_version,
)

# Initialize RAG Service for couple searches
rag_service = None
try:
    from unified_rag_service import UnifiedRAGService
    voting_csv = str(ELECTIONS_DIR / "voting_centers.csv")
    candidate_csvs = {"2082": str(ELECTIONS_DIR / "election_candidates-2082.csv")}
    
    if PathLibPath(voting_csv).exists() and PathLibPath(candidate_csvs["2082"]).exists():
        rag_service = UnifiedRAGService(
            voting_csv_path=voting_csv,
            candidate_csv_paths=candidate_csvs
        )
        rag_service.initialize()
        logger.info("RAG service initialized successfully for couple searches")
    else:
        logger.warning("RAG service data files not found, couple search unavailable")
except Exception as e:
    logger.warning(f"Failed to initialize RAG service: {e}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Allow MapLibre CSS (unpkg), Google Fonts, data/blob images, and API (self + dev backend)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' https://unpkg.com https://fonts.googleapis.com; "
        "style-src-elem 'self' https://unpkg.com https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "script-src 'self' https://plausible.io; "
        "script-src-elem 'self' https://plausible.io; "
        "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 "
        "http://165.22.215.152 http://165.22.215.152:8000 https://165.22.215.152 https://165.22.215.152:8000 "
        "https://nepalelection.subsy.tech https://nepalelection.subsy.tech:8000 "
        "http://nepalelection.subsy.tech http://nepalelection.subsy.tech:8000"
    )
    return response


# Include API routers
app.include_router(map.router, prefix=API_V1_PREFIX)
app.include_router(trends.router, prefix=API_V1_PREFIX)
app.include_router(insights.router, prefix=API_V1_PREFIX)
app.include_router(compare.router, prefix=API_V1_PREFIX)


# RAG Service Proxy Configuration
RAG_SERVICE_URL = "http://rag-qa:8002"
rag_client = httpx.AsyncClient(timeout=30.0)


@app.get("/rag-api/health")
async def rag_health_proxy():
    """
    Proxy to RAG service health check endpoint.
    """
    try:
        response = await rag_client.get(f"{RAG_SERVICE_URL}/health")
        return response.json()
    except Exception as e:
        logger.error(f"Error proxying to RAG health: {e}")
        raise HTTPException(status_code=503, detail="RAG service unavailable")


@app.post("/rag-api/api/v1/chat")
async def rag_chat_proxy(request: Dict[str, Any]):
    """
    Proxy to RAG service chat endpoint.
    
    Allows frontend to access RAG chatbot through the main app on port 8000
    instead of directly connecting to port 8002.
    """
    try:
        response = await rag_client.post(
            f"{RAG_SERVICE_URL}/api/v1/chat",
            json=request,
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error proxying to RAG chat: {e}")
        raise HTTPException(status_code=503, detail="RAG service unavailable")


@app.post("/rag-api/api/v1/analytics")
async def rag_analytics_proxy(request: Dict[str, Any]):
    """
    Proxy to RAG service analytics endpoint.
    
    Allows frontend to access RAG analytics through the main app on port 8000.
    """
    try:
        response = await rag_client.post(
            f"{RAG_SERVICE_URL}/api/v1/analytics",
            json=request,
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error proxying to RAG analytics: {e}")
        raise HTTPException(status_code=503, detail="RAG service unavailable")


@app.post("/rag-api/api/reset_session")
async def rag_reset_session_proxy():
    """
    Proxy to RAG service session reset endpoint.
    """
    try:
        response = await rag_client.post(f"{RAG_SERVICE_URL}/api/reset_session")
        return response.json()
    except Exception as e:
        logger.error(f"Error proxying to RAG session reset: {e}")
        raise HTTPException(status_code=503, detail="RAG service unavailable")


# Pydantic models for API responses
class ElectionSummary(BaseModel):
    """Summary of an election."""
    year: int
    total_candidates: int
    total_constituencies: int
    total_districts: int
    total_provinces: int
    parties: List[str]
    validation: Optional[Dict] = None


class CandidateInfo(BaseModel):
    """Candidate information."""
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    party: Optional[str] = None
    is_independent: Optional[bool] = None
    district: Optional[str] = None
    constituency: Optional[str] = None
    province: Optional[str] = None
    election_year: Optional[int] = None
    age: Optional[float] = None
    gender: Optional[str] = None
    education_level: Optional[str] = None
    votes_received: Optional[float] = None
    votes_percentage: Optional[float] = None
    is_winner: Optional[bool] = None


class ProvinceStats(BaseModel):
    """Province-level statistics."""
    province: str
    total_candidates: int
    total_constituencies: int
    total_districts: int
    parties: List[str]


class DistrictStats(BaseModel):
    """District-level statistics."""
    district: str
    province: str
    total_candidates: int
    total_constituencies: int
    parties: List[str]


class ConstituencyStats(BaseModel):
    """Constituency-level statistics."""
    constituency: str
    district: str
    province: str
    total_candidates: int
    parties: List[str]
    winner: Optional[Dict] = None


# API Routes
# FRONTEND_DIST check: when built (Docker), serve SPA at /; else API message
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

@app.get("/")
async def root():
    """Root: serve SPA when built (Docker), else API info."""
    if FRONTEND_DIST.exists():
        return FileResponse(FRONTEND_DIST / "index.html")
    return {
        "message": "Nepal House of Representatives Election Data API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    available_elections = loader.list_available_elections()
    return {
        "status": "healthy",
        "available_elections": available_elections,
    }


@app.get(f"{API_V1_PREFIX}/elections", response_model=List[int])
async def list_elections():
    """
    List all available election years.
    """
    elections = loader.list_available_elections()
    return elections


@app.get(f"{API_V1_PREFIX}/elections/{{year}}/filter-options")
async def get_filter_options(
    year: int = PathParam(..., description="Election year", ge=2000, le=2100),
    province: Optional[str] = Query(None, description="Filter districts by province"),
    district: Optional[str] = Query(None, description="Filter constituencies by district"),
):
    """
    Get available filter options (provinces, districts, parties, etc.) from CSV data.
    
    Supports hierarchical filtering:
    - If province is specified, only returns districts in that province
    - If district is specified, only returns constituencies in that district
    """
    try:
        df, _ = loader.load_election(year)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Filter by province if specified (match main and _en columns when present)
    filtered_df = df.copy()
    if province:
        filtered_df = filtered_df[_match_col_or_en(filtered_df, "province", "province_en", province, extra_cols=["province_np"])]
    if district:
        filtered_df = filtered_df[_match_col_or_en(filtered_df, "district", "district_en", district)]
    
    # Extract unique values for each filter field
    province_values = []
    if "province" in df.columns:
        province_values = df["province"].dropna().unique().tolist()
        province_values = sorted(province_values, key=province_sort_key)

    options = {
        "provinces": province_values,
        "districts": sorted(filtered_df["district"].dropna().unique().tolist()) if "district" in filtered_df.columns else [],
        "constituencies": sorted(filtered_df["constituency"].dropna().unique().tolist()) if "constituency" in filtered_df.columns else [],
        "parties": sorted(df["party"].dropna().unique().tolist()) if "party" in df.columns else [],
        "genders": sorted(df["gender"].dropna().unique().tolist()) if "gender" in df.columns else [],
        "education_levels": sorted(df["education_level"].dropna().unique().tolist()) if "education_level" in df.columns else [],
        "age_range": {
            "min": int(df["age"].min()) if "age" in df.columns and df["age"].notna().any() else 18,
            "max": int(df["age"].max()) if "age" in df.columns and df["age"].notna().any() else 100,
        },
    }
    
    return options


# English columns supported for search, filters, and display (review)
ENGLISH_COLUMNS_SPEC = [
    {"name": "candidate_name_en", "description": "Candidate Full Name in English", "csv_examples": ["Candidate Full Name in English", "Q", "name in english"]},
    {"name": "district_en", "description": "District in English", "csv_examples": ["District in English"]},
    {"name": "birth_place_en", "description": "Birth Place in English", "csv_examples": ["Birth Place In english"]},
    {"name": "party_en", "description": "Political Party in English", "csv_examples": ["Political Party In English"]},
    {"name": "province_en", "description": "State/Province in English", "csv_examples": ["State in English", "State name in English"]},
    {"name": "province_np", "description": "State name in Nepali", "csv_examples": ["State name in Nepali"]},
]


@app.get(f"{API_V1_PREFIX}/schema")
async def get_schema():
    """
    List all supported data columns for review (required, optional, English).
    Use when preparing CSVs or reviewing which columns the app uses.
    """
    return {
        "required": [{"name": c} for c in REQUIRED_COLUMNS],
        "optional": [{"name": c} for c in OPTIONAL_COLUMNS],
        "english": ENGLISH_COLUMNS_SPEC,
    }


@app.get(f"{API_V1_PREFIX}/elections/{{year}}/columns")
async def get_election_columns(
    year: int = PathParam(..., description="Election year", ge=2000, le=2100),
):
    """
    List all columns present in this election's data and first row sample.
    Includes English columns when present. For review and debugging.
    """
    try:
        df, _ = loader.load_election(year)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cols = list(df.columns)
    first = df.iloc[0] if len(df) > 0 else pd.Series(dtype=object)
    english_names = {s["name"] for s in ENGLISH_COLUMNS_SPEC}

    def _sample(v):
        if pd.isna(v):
            return None
        s = str(v).strip()
        if len(s) > 100:
            return s[:97] + "..."
        return s

    columns = [{"name": c, "sample": _sample(first.get(c)), "english": c in english_names} for c in cols]
    first_row = {c: _sample(first.get(c)) for c in cols}

    return {
        "year": year,
        "columns": columns,
        "first_row": first_row,
        "english_columns_present": [c for c in cols if c in english_names],
    }


@app.get(f"{API_V1_PREFIX}/elections/{{year}}/summary", response_model=ElectionSummary)
async def get_election_summary(
    year: int = PathParam(..., description="Election year", ge=2000, le=2100)
):
    """
    Get summary statistics for a specific election year.
    """
    try:
        df, validation = loader.load_election(year)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Constituencies: count election areas per district, then sum all (165 for full Nepal data)
    if "constituency" in df.columns and "district" in df.columns:
        per_district = df.groupby("district", sort=True)["constituency"].nunique()
        total_constituencies = int(per_district.sum())
    else:
        total_constituencies = int(df["constituency"].nunique()) if "constituency" in df.columns else 0

    summary = {
        "year": year,
        "total_candidates": len(df),
        "total_constituencies": total_constituencies,
        "total_districts": df["district"].nunique() if "district" in df.columns else 0,
        "total_provinces": df["province"].nunique() if "province" in df.columns else 0,
        "parties": sorted(df["party"].unique().tolist()) if "party" in df.columns else [],
        "validation": validation.to_dict() if validation else None,
    }

    return summary


@app.get(f"{API_V1_PREFIX}/elections/{{year}}/candidates", response_model=List[CandidateInfo])
async def get_candidates(
    year: int = PathParam(..., description="Election year", ge=2000, le=2100),
    district: Optional[str] = Query(None, description="Filter by district"),
    constituency: Optional[str] = Query(None, description="Filter by constituency"),
    province: Optional[str] = Query(None, description="Filter by province"),
    party: Optional[str] = Query(None, description="Filter by party"),
    winner_only: bool = Query(False, description="Return only winners"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
):
    """
    Get candidate information for a specific election year.
    Supports filtering by district, constituency, province, party, and winner status.
    """
    try:
        df, _ = loader.load_election(year)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Apply filters (match main columns and English _en columns when present)
    if district:
        df = df[_match_col_or_en(df, "district", "district_en", district)]
    if constituency:
        df = df[df["constituency"].astype(str).str.contains(constituency, case=False, na=False, regex=False)]
    if province:
        df = df[_match_col_or_en(df, "province", "province_en", province, extra_cols=["province_np"])]
    if party:
        df = df[_match_col_or_en(df, "party", "party_en", party)]
    if winner_only and "is_winner" in df.columns:
        df = df[df["is_winner"] == True]
    
    # Limit results
    df = df.head(limit)
    
    # Convert to list of dictionaries
    raw = df.to_dict(orient='records')
    # Replace NaN/inf with None so JSON serialization succeeds
    candidates = [
        {k: (None if isinstance(v, float) and (pd.isna(v) or abs(v) == float('inf')) else v) for k, v in rec.items()}
        for rec in raw
    ]
    return candidates


@app.get(f"{API_V1_PREFIX}/elections/{{year}}/provinces", response_model=List[ProvinceStats])
async def get_province_stats(
    year: int = PathParam(..., description="Election year", ge=2000, le=2100),
):
    """
    Get province-level statistics for a specific election year.
    """
    try:
        df, _ = loader.load_election(year)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if "province" not in df.columns:
        raise HTTPException(status_code=400, detail="Province column not found in data")
    
    # Group by province
    province_stats = []
    for province in df["province"].unique():
        province_df = df[df["province"] == province]
        stats = {
            "province": province,
            "total_candidates": len(province_df),
            "total_constituencies": province_df["constituency"].nunique() if "constituency" in province_df.columns else 0,
            "total_districts": province_df["district"].nunique() if "district" in province_df.columns else 0,
            "parties": sorted(province_df["party"].unique().tolist()) if "party" in province_df.columns else [],
        }
        province_stats.append(stats)
    
    # Sort provinces using custom province order
    return sorted(province_stats, key=lambda x: province_sort_key(x["province"]))


@app.get(f"{API_V1_PREFIX}/elections/{{year}}/districts", response_model=List[DistrictStats])
async def get_district_stats(
    year: int = PathParam(..., description="Election year", ge=2000, le=2100),
    province: Optional[str] = Query(None, description="Filter by province"),
):
    """
    Get district-level statistics for a specific election year.
    """
    try:
        df, _ = loader.load_election(year)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if "district" not in df.columns:
        raise HTTPException(status_code=400, detail="District column not found in data")
    
    # Apply province filter if provided
    if province:
        df = df[df["province"].str.contains(province, case=False, na=False, regex=False)]
    
    # Group by district
    district_stats = []
    for district in df["district"].unique():
        district_df = df[df["district"] == district]
        stats = {
            "district": district,
            "province": district_df["province"].iloc[0] if "province" in district_df.columns else None,
            "total_candidates": len(district_df),
            "total_constituencies": district_df["constituency"].nunique() if "constituency" in district_df.columns else 0,
            "parties": sorted(district_df["party"].unique().tolist()) if "party" in district_df.columns else [],
        }
        district_stats.append(stats)
    
    return sorted(district_stats, key=lambda x: x["district"])


@app.get(f"{API_V1_PREFIX}/elections/{{year}}/constituencies", response_model=List[ConstituencyStats])
async def get_constituency_stats(
    year: int = PathParam(..., description="Election year", ge=2000, le=2100),
    district: Optional[str] = Query(None, description="Filter by district"),
    province: Optional[str] = Query(None, description="Filter by province"),
):
    """
    Get constituency-level statistics for a specific election year.
    """
    try:
        df, _ = loader.load_election(year)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if "constituency" not in df.columns:
        raise HTTPException(status_code=400, detail="Constituency column not found in data")
    
    # Apply filters
    if district:
        df = df[df["district"].str.contains(district, case=False, na=False, regex=False)]
    if province:
        df = df[df["province"].str.contains(province, case=False, na=False, regex=False)]
    
    # Group by constituency
    constituency_stats = []
    for constituency in df["constituency"].unique():
        constituency_df = df[df["constituency"] == constituency]
        
        # Find winner if available
        winner = None
        if "is_winner" in constituency_df.columns:
            winners = constituency_df[constituency_df["is_winner"] == True]
            if len(winners) > 0:
                winner = winners.iloc[0].to_dict()
        
        stats = {
            "constituency": constituency,
            "district": constituency_df["district"].iloc[0] if "district" in constituency_df.columns else None,
            "province": constituency_df["province"].iloc[0] if "province" in constituency_df.columns else None,
            "total_candidates": len(constituency_df),
            "parties": sorted(constituency_df["party"].unique().tolist()) if "party" in constituency_df.columns else [],
            "winner": winner,
        }
        constituency_stats.append(stats)
    
    return sorted(constituency_stats, key=lambda x: x["constituency"])


class VotingCenterStats(BaseModel):
    """Voting center-level statistics."""
    area_no: int
    district: str
    province: str
    palika_type: Optional[str] = None
    palika_name: Optional[str] = None
    ward_no: Optional[int] = None
    polling_center_code: int
    polling_center_name: str
    sub_center: Optional[str] = None
    voter_count: int
    voter_from_serial: int
    voter_to_serial: int
    source_file: Optional[str] = None
    language: Optional[str] = None


class VotingCentersSummary(BaseModel):
    """Summary statistics for voting centers."""
    total_centers: int
    total_voters: int
    voters_from_serial: int
    voters_to_serial: int
    filtered_by: Dict[str, str]


class VotingCentersResponse(BaseModel):
    """Response containing voting centers and summary."""
    voting_centers: List[VotingCenterStats]
    summary: VotingCentersSummary


@app.get(f"{API_V1_PREFIX}/voting-centers", response_model=VotingCentersResponse)
async def get_voting_centers(
    district: Optional[str] = Query(None, description="Filter by district"),
    province: Optional[str] = Query(None, description="Filter by province"),
    election_area: Optional[int] = Query(None, description="Filter by election area number (area_no)"),
    palika_name: Optional[str] = Query(None, description="Filter by palika/municipality name"),
    ward_no: Optional[int] = Query(None, description="Filter by ward number"),
    polling_center_code: Optional[int] = Query(None, description="Filter by polling center code"),
):
    """
    Get voting center data.

    Filters can be applied by province, district, election_area, palika_name, ward_no, or polling_center_code.
    Returns detailed information about each voting center including voter counts and center details,
    plus a summary with total voters and counts.
    """
    import re
    import logging
    logger = logging.getLogger(__name__)
    
    voting_center_file = ELECTIONS_DIR / "voting_centers.csv"

    if not voting_center_file.exists():
        raise HTTPException(status_code=404, detail="Voting center data file not found")

    try:
        df = pd.read_csv(voting_center_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load voting center data: {str(e)}")

    # Log incoming parameters for debugging
    logger.info(f"Voting centers request - province: {province}, district: {district}, election_area: {election_area}, palika_name: {palika_name}")
    logger.info(f"Total rows in CSV: {len(df)}")
    logger.info(f"Election_area type: {type(election_area)}, value: {election_area}")

    # Apply filters cumulatively - all provided filters are applied together
    logger.info(f"Applying filters - province: {province}, district: {district}, election_area: {election_area}, palika_name: {palika_name}")

    # Parse election_area (constituency number) - can be int or string (e.g., "सुनसरी - ४")
    if election_area is not None:
        constituency_num = None

        # If it's already an integer, use it directly
        if isinstance(election_area, int):
            constituency_num = election_area
        else:
            # Try to parse from string name (e.g., "सुनसरी - ४" -> 4)
            devanagari_num = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
            match = re.search(r'[-–—]\s*([०१२३४५६७८९\d]+)\s*$', str(election_area))
            if match:
                num_str = match.group(1)
                # Convert Devanagari to Arabic numerals
                arabic_num = ''.join(devanagari_num.get(c, c) for c in num_str)
                try:
                    constituency_num = int(arabic_num)
                except ValueError:
                    pass

        if constituency_num is not None:
            df = df[df["area_no"] == constituency_num]
            logger.info(f"Filtered by election_area={election_area} -> constituency_num={constituency_num}, rows: {len(df)}")

    # Apply province filter (if provided)
    if province:
        df = df[df["province"].str.contains(province, case=False, na=False, regex=False)]
        logger.info(f"Filtered by province={province}, rows: {len(df)}")

    # Apply district filter (if provided)
    if district:
        df = df[df["district"].str.contains(district, case=False, na=False, regex=False)]
        logger.info(f"Filtered by district={district}, rows: {len(df)}")

    # Apply other filters (if provided)
    if palika_name:
        df = df[df["palika_name"].str.contains(palika_name, case=False, na=False, regex=False)]
        logger.info(f"Filtered by palika_name={palika_name}, rows: {len(df)}")
    if ward_no is not None:
        df = df[df["ward_no"] == ward_no]
        logger.info(f"Filtered by ward_no={ward_no}, rows: {len(df)}")
    if polling_center_code is not None:
        df = df[df["polling_center_code"] == polling_center_code]
        logger.info(f"Filtered by polling_center_code={polling_center_code}, rows: {len(df)}")

    # Convert to list of dictionaries, handling NaN values
    voting_centers = []
    for _, row in df.iterrows():
        record = {
            "area_no": int(row["area_no"]) if pd.notna(row["area_no"]) else None,
            "district": str(row["district"]) if pd.notna(row["district"]) else None,
            "province": str(row["province"]) if pd.notna(row["province"]) else None,
            "palika_type": str(row["palika_type"]) if pd.notna(row["palika_type"]) else None,
            "palika_name": str(row["palika_name"]) if pd.notna(row["palika_name"]) else None,
            "ward_no": int(row["ward_no"]) if pd.notna(row["ward_no"]) else None,
            "polling_center_code": int(row["polling_center_code"]) if pd.notna(row["polling_center_code"]) else None,
            "polling_center_name": str(row["polling_center_name"]) if pd.notna(row["polling_center_name"]) else None,
            "sub_center": str(row["sub_center"]) if pd.notna(row["sub_center"]) else None,
            "voter_count": int(row["voter_count"]) if pd.notna(row["voter_count"]) else 0,
            "voter_from_serial": int(row["voter_from_serial"]) if pd.notna(row["voter_from_serial"]) else 0,
            "voter_to_serial": int(row["voter_to_serial"]) if pd.notna(row["voter_to_serial"]) else 0,
            "source_file": str(row["source_file"]) if pd.notna(row["source_file"]) else None,
            "language": str(row["language"]) if pd.notna(row["language"]) else None,
        }
        voting_centers.append(record)

    # Calculate summary statistics
    total_voters = sum(center["voter_count"] for center in voting_centers)
    voters_from_serial = min((center["voter_from_serial"] for center in voting_centers if center["voter_from_serial"] > 0), default=0)
    voters_to_serial = max((center["voter_to_serial"] for center in voting_centers if center["voter_to_serial"] > 0), default=0)

    # Build applied filters dict
    filtered_by = {}
    if province:
        filtered_by["province"] = province
    if district:
        filtered_by["district"] = district
    if election_area is not None:
        filtered_by["election_area"] = str(election_area)
    if palika_name:
        filtered_by["palika_name"] = palika_name
    if ward_no is not None:
        filtered_by["ward_no"] = str(ward_no)
    if polling_center_code is not None:
        filtered_by["polling_center_code"] = str(polling_center_code)

    summary = {
        "total_centers": len(voting_centers),
        "total_voters": total_voters,
        "voters_from_serial": voters_from_serial,
        "voters_to_serial": voters_to_serial,
        "filtered_by": filtered_by
    }

    logger.info(f"Returning {len(voting_centers)} voting centers with {total_voters} total voters")

    return {
        "voting_centers": voting_centers,
        "summary": summary
    }


class CoupleInfo(BaseModel):
    """Couple candidate information."""
    spouse_index: str
    candidate_1: Dict[str, Any]
    candidate_2: Dict[str, Any]


class CouplesResponse(BaseModel):
    """Response containing couple candidates."""
    couples: List[CoupleInfo]
    total_couples: int
    answer: str


@app.get(f"{API_V1_PREFIX}/couples", response_model=CouplesResponse)
async def get_couple_candidates():
    """
    Get couple candidates (spouses running together).
    
    Returns information about couples where both spouses are candidates.
    Uses RAG service for intelligent matching if available.
    """
    if rag_service is None:
        return {
            "couples": [],
            "total_couples": 0,
            "answer": "RAG service not available. Couple search feature is currently disabled."
        }
    
    try:
        result = rag_service.find_couple_candidates()
        return result
    except Exception as e:
        logger.error(f"Error fetching couple candidates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch couple candidates")


@app.get(f"{API_V1_PREFIX}/longitudinal/compare")
async def compare_elections(
    years: str = Query(..., description="Comma-separated list of election years (e.g., '2017,2022')"),
    metric: str = Query("party_distribution", description="Metric to compare"),
):
    """
    Compare elections across multiple years.
    
    Supported metrics:
    - party_distribution: Compare party representation across years
    - candidate_count: Compare total candidate counts
    - constituency_count: Compare constituency counts
    """
    try:
        year_list = [int(y.strip()) for y in years.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid years format. Use comma-separated integers.")
    
    if len(year_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 years required for comparison")
    
    # Load all requested elections
    election_data = {}
    for year in year_list:
        try:
            df, _ = loader.load_election(year)
            election_data[year] = df
        except FileNotFoundError:
            logger.warning(f"Election {year} not found, skipping")
            continue
    
    if not election_data:
        raise HTTPException(status_code=404, detail="No election data found for requested years")
    
    # Generate comparison based on metric
    if metric == "party_distribution":
        comparison = {}
        for year, df in election_data.items():
            if "party" in df.columns:
                party_counts = df["party"].value_counts().to_dict()
                comparison[year] = party_counts
        return {"metric": metric, "comparison": comparison}
    
    elif metric == "candidate_count":
        comparison = {year: len(df) for year, df in election_data.items()}
        return {"metric": metric, "comparison": comparison}
    
    elif metric == "constituency_count":
        comparison = {}
        for year, df in election_data.items():
            if "constituency" in df.columns:
                comparison[year] = df["constituency"].nunique()
            else:
                comparison[year] = 0
        return {"metric": metric, "comparison": comparison}
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported metric: {metric}. Supported: party_distribution, candidate_count, constituency_count"
        )


# Serve frontend static files when built (Docker / production)
# Must be registered last so / and /health are matched first
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA: static files if present, else index.html for client-side routing."""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler. Avoids leaking internal error details to clients."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
