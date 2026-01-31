# Nepal House of Representatives Election Data Visualization & Insight System

A **full-stack** production-ready system for longitudinal analysis and visualization of Nepal House of Representatives election data. Includes FastAPI backend with comprehensive analytics and React frontend with interactive maps and charts.

## Overview

This system provides APIs for analyzing election data across multiple election cycles, supporting hierarchical analysis from province → district → constituency levels. It is designed to handle real-world CSV data files with robust validation, graceful error handling, and comprehensive documentation.

## Features

- **Longitudinal Analysis**: Compare election data across multiple years
- **Hierarchical Analysis**: Province → District → Constituency breakdowns
- **Robust Data Handling**: Validates CSV structure, handles missing columns gracefully
- **Flexible Schema**: Documents assumptions, validates presence, provides fallbacks
- **Production-Ready**: Comprehensive error handling, logging, and API documentation

## Tech Stack

### Backend
- **Python 3.11**
- **FastAPI** - Modern, fast web framework
- **pandas** - Data manipulation and analysis
- **geopandas** - Geospatial data handling
- **shapely** - Geometric operations
- **pydantic** - Data validation
- **uvicorn** - ASGI server

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **MapLibre GL JS** - Interactive map visualization (free, open-source)
- **Apache ECharts** - Chart library for trends
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client

## Project Structure

```
election-visualization/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration constants
│   │   └── settings.py         # Pydantic settings
│   └── data/
│       ├── __init__.py
│       ├── loader.py           # CSV loading logic
│       ├── validator.py        # Column validation
│       ├── schema_notes.py     # Documented CSV assumptions
│       └── preprocess.py       # Data cleaning and enrichment
├── data/
│   └── elections/             # Place CSV files here
│       ├── election_2017.csv
│       ├── election_2022.csv
│       └── election_2026.csv
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

### Backend Setup

1. **Create a virtual environment**:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Create data directory** (if not exists):
```bash
mkdir -p data/elections
```

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install Node.js dependencies**:
```bash
npm install
```

3. **Set up environment variables** (optional):
```bash
cp .env.example .env
# No API token needed! MapLibre uses free OpenStreetMap tiles
```

4. **Start the development server**:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Usage

### Adding Election Data

Place your CSV files in the `data/elections/` directory with names like:
- `election_2017.csv`
- `election_2022.csv`
- `election_2026.csv`

Or any filename containing the year (e.g., `nepal_election_2017.csv`).

### Running the System

1. **Start the backend** (from project root):
```bash
# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start the frontend** (in a separate terminal):
```bash
cd frontend
npm run dev
```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Expected CSV Columns

#### Required Columns
- `candidate_id` - Unique identifier for the candidate
- `candidate_name` - Full name of the candidate
- `party` - Political party affiliation
- `district` - District name
- `constituency` - Constituency identifier/name
- `province` - Province name or identifier
- `election_year` - Year of the election (can be inferred from filename)

#### Optional Columns
- `is_independent` - Boolean flag for independent candidates
- `age` - Candidate age
- `gender` - Gender (M/F/Other)
- `education_level` - Highest education level
- `birth_district` - District of birth
- `symbol` - Election symbol identifier
- `votes_received` - Number of votes received
- `votes_percentage` - Percentage of votes
- `is_winner` - Boolean flag indicating winner
- `margin` - Victory margin
- `total_voters` - Total registered voters
- `voter_turnout` - Voter turnout percentage

**Note**: Column names are normalized (case-insensitive, spaces converted to underscores). The system will attempt to match common variations.

### Running the Server

```bash
python -m app.main
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Environment Variables

Create a `.env` file (optional) to override defaults:

```env
HOST=0.0.0.0
PORT=8000
RELOAD=false
STRICT_VALIDATION=false
LOG_WARNINGS=true
```

## API Endpoints

### Health & Info

- `GET /` - Root endpoint with API info
- `GET /health` - Health check and available elections

### Elections

- `GET /api/v1/elections` - List all available election years
- `GET /api/v1/elections/{year}/summary` - Get election summary statistics
- `GET /api/v1/elections/{year}/candidates` - Get candidates (with filters)
- `GET /api/v1/elections/{year}/provinces` - Get province-level statistics
- `GET /api/v1/elections/{year}/districts` - Get district-level statistics
- `GET /api/v1/elections/{year}/constituencies` - Get constituency-level statistics

### Map Data

- `GET /api/v1/map` - Get GeoJSON map data with candidate information
  - Query params: `election_year`, `province`, `district`, `party`, `independent`, `age_min`, `age_max`, `gender`, `education_level`

### Trends

- `GET /api/v1/trends` - Get trend analysis across multiple years
  - Query params: `years` (comma-separated), `metric` (optional)
  - Metrics: `independent_shift`, `party_footprint`, `age_trends`, `education_evolution`, `party_volatility`, `candidate_density`, `symbol_saturation`, `political_churn`

### Insights

- `GET /api/v1/insights` - Get comprehensive insights for an election
  - Query params: `election_year`, `compare_with` (optional)
- `GET /api/v1/insights/independent-wave` - District-level independent strength
- `GET /api/v1/insights/competition-pressure` - District competition (margins)
- `GET /api/v1/insights/party-saturation` - Party saturation vs reach
- `GET /api/v1/insights/age-gap` - Age gap between political movements

The **Insights** tab shows four main visualizations (Independent Wave, Competition Pressure, Party Saturation vs Reach, Age Gap) plus a **Key metrics** strip from the full insights API. Niche metrics (e.g. symbol saturation, candidate density) appear in the strip only to keep the dashboard focused.

### Candidate Comparison

- `GET /api/v1/compare/candidates` - Compare candidates by ID
  - Query params: `candidate_ids` (comma-separated), `election_year` (optional)

### Longitudinal Analysis

- `GET /api/v1/longitudinal/compare` - Compare elections across years

### Example Requests

```bash
# List available elections
curl http://localhost:8000/api/v1/elections

# Get summary for 2017 election
curl http://localhost:8000/api/v1/elections/2017/summary

# Get candidates from a specific district
curl "http://localhost:8000/api/v1/elections/2017/candidates?district=Kathmandu"

# Compare party distribution across years
curl "http://localhost:8000/api/v1/longitudinal/compare?years=2017,2022&metric=party_distribution"
```

## Data Validation

The system performs comprehensive validation:

1. **Column Presence**: Checks for required vs optional columns
2. **Column Normalization**: Normalizes column names (case-insensitive, handles spaces)
3. **Type Inference**: Attempts to infer and convert data types
4. **Data Quality**: Logs warnings for missing data, unexpected columns

Validation results are included in election summaries and can be accessed via the API.

## Error Handling

The system handles errors gracefully:

- **Missing Files**: Returns 404 with descriptive message
- **Missing Columns**: Logs warnings (or fails in strict mode)
- **Invalid Data**: Attempts to clean/convert, logs issues
- **API Errors**: Returns appropriate HTTP status codes with error details

## Development

### Project Structure Details

- **`app/core/config.py`**: Paths and constants
- **`app/core/settings.py`**: Environment-based configuration
- **`app/data/schema_notes.py`**: Documented CSV assumptions
- **`app/data/validator.py`**: Column validation logic
- **`app/data/loader.py`**: CSV loading with caching
- **`app/data/preprocess.py`**: Data cleaning and type conversion
- **`app/main.py`**: FastAPI routes and application logic

### Adding New Endpoints

1. Define Pydantic models for request/response in `main.py`
2. Add route handler with appropriate path
3. Use `loader.load_election()` to get data
4. Apply filters/transformations
5. Return structured response

### Testing

```bash
# Run with reload for development
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/health
```

## Analytics Modules

The system includes 10 comprehensive analytics modules:

1. **Independent Shift** - Structural shift in independent candidate participation
2. **Party Retrenchment** - Party footprint index (expansion vs retrenchment)
3. **Age Trends** - Leadership renewal analysis (candidate age trends)
4. **Urban Fragmentation** - Political fragmentation in urban areas
5. **Education Evolution** - Evolution of candidate education profiles
6. **Local vs Outsider** - Trend analysis of local vs outsider candidates
7. **Party Volatility** - Party stability vs volatility index
8. **Candidate Density** - Candidate density vs voter choice metrics
9. **Symbol Saturation** - Ballot UX metric (symbol saturation)
10. **Political Churn** - Political churn index (candidate turnover)

## Frontend Features

### Map View
- Interactive MapLibre GL JS map (free, open-source)
- Uses OpenStreetMap tiles (no API key required)
- Drill-down navigation (province → district → constituency)
- Hover tooltips with candidate information
- Color-coded visualization based on candidate count
- Click to view detailed information

### Trend Charts
- Multi-year trend visualization
- Select multiple election years
- ECharts-based interactive charts
- All analytics metrics visualized

### Candidate Comparison
- Compare up to 10 candidates by ID
- Side-by-side comparison view
- Comparison metrics (age range, party distribution, etc.)
- Detailed candidate information

### Filters Panel
- Election year selection
- Province, district, party filters
- Independent candidate filter
- Age range filter
- Gender filter
- Education level filter

## Future Enhancements

- Load actual geospatial boundary data (shapefiles) for accurate map visualization
- Advanced statistical analysis (correlations, regressions)
- Export functionality (PDF reports, Excel)
- Authentication and rate limiting
- Database integration for large datasets
- Real-time data updates
- Mobile-responsive optimizations

## License

MIT License. See [LICENSE](LICENSE) in the project root.

Election data is sourced from the [Election Commission, Nepal](https://election.gov.np/); map boundaries from [geoJSON-Nepal](https://github.com/mesaugat/geoJSON-Nepal). See [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md) and the in-app **Data sources** page for attribution and methodology.

## Contributing

[Contributing guidelines]

## Support

For issues or questions, please open an issue on GitHub or contact **deb.katwal+electionviz@gmail.com**.
