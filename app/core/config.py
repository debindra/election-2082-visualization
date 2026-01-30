"""
Core configuration for the Election Data Visualization System.
"""
from pathlib import Path
from typing import Optional

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
ELECTIONS_DIR = DATA_DIR / "elections"
GEOSPATIAL_DIR = DATA_DIR / "geospatial"

# Ensure directories exist
ELECTIONS_DIR.mkdir(parents=True, exist_ok=True)
GEOSPATIAL_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
API_V1_PREFIX = "/api/v1"
API_TITLE = "Nepal House of Representatives Election Data API"
API_DESCRIPTION = """
Longitudinal Election Data Visualization & Insight System for Nepal House of Representatives.

This API provides endpoints for analyzing election data across multiple election cycles,
supporting province → district → constituency hierarchical analysis.
"""
API_VERSION = "1.0.0"
