# Quick Start Guide

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- No API keys needed! MapLibre uses free OpenStreetMap tiles

## Setup Steps

### 1. Backend Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data/elections
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# No environment setup needed!
# MapLibre GL JS works without any API tokens
```

### 3. Add Your CSV Data

Place your election CSV files in `data/elections/`:
- `election_2017.csv`
- `election_2022.csv`
- etc.

**Required columns**: `candidate_id`, `candidate_name`, `party`, `district`, `constituency`, `province`, `election_year`

**Optional columns**: `is_independent`, `age`, `gender`, `education_level`, `birth_district`, `symbol`, etc.

### 4. Run the System

**Terminal 1 - Backend:**
```bash
# From project root
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
# From frontend directory
npm run dev
```

### 5. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage

1. **Map View**: Select an election year and use filters to explore data on the map
2. **Trends**: Select multiple election years to view longitudinal trends
3. **Compare Candidates**: Enter candidate IDs (comma-separated) to compare candidates

## Troubleshooting

### Map not loading?
- Check browser console for errors
- Ensure internet connection (map tiles load from OpenStreetMap)

### API errors?
- Ensure backend is running on port 8000
- Check that CSV files are in `data/elections/` directory
- Verify CSV has required columns

### CORS errors?
- Backend CORS is configured to allow all origins by default
- Check that backend is running and accessible

## Next Steps

- Add actual geospatial boundary data (shapefiles) for accurate map visualization
- Customize filters and visualizations based on your data
- Explore the analytics modules in `app/analytics/`
- Check API documentation at `/docs` for all available endpoints
