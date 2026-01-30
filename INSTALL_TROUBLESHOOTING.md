# Installation Troubleshooting

## Common Issues

### 1. pandas Installation Fails (metadata-generation-failed)

**Problem**: pandas fails to install, often on macOS with newer Python versions.

**Solutions**:

#### Option A: Upgrade pip and setuptools first
```bash
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt
```

#### Option B: Install numpy first (pandas dependency)
```bash
python3 -m pip install numpy
python3 -m pip install -r requirements.txt
```

#### Option C: Use Python 3.11 (recommended)
If you're using Python 3.14 or 3.13, pandas may not have pre-built wheels yet. Use Python 3.11:

```bash
# Install Python 3.11 via Homebrew
brew install python@3.11

# Create venv with Python 3.11
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### Option D: Install build dependencies (macOS)
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Then try installing again
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 2. geopandas Installation Fails

**Problem**: geopandas requires system libraries (GDAL, GEOS, etc.)

**Solutions**:

#### macOS (Homebrew)
```bash
brew install gdal geos proj
pip install geopandas
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev libgeos-dev libproj-dev
pip install geopandas
```

### 3. Module Not Found Errors

**Problem**: After installation, Python can't find modules.

**Solution**: Ensure virtual environment is activated
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. CORS Errors in Frontend

**Problem**: Frontend can't connect to backend API.

**Solutions**:
- Ensure backend is running on port 8000
- Check `frontend/vite.config.js` proxy configuration
- Verify backend CORS settings in `app/core/settings.py`

### 5. Map Not Loading

**Problem**: Map shows error or doesn't load.

**Solutions**:
- Check browser console for specific errors
- Ensure internet connection (map tiles load from OpenStreetMap)
- MapLibre GL JS works without any API tokens - no setup needed!

## Step-by-Step Clean Installation

If you're having persistent issues, try a clean installation:

```bash
# 1. Remove old virtual environment
rm -rf venv

# 2. Create new venv with Python 3.11 (recommended)
python3.11 -m venv venv
source venv/bin/activate

# 3. Upgrade pip and build tools
pip install --upgrade pip setuptools wheel

# 4. Install system dependencies (macOS)
brew install gdal geos proj  # Skip if not on macOS

# 5. Install Python packages
pip install -r requirements.txt

# 6. Verify installation
python -c "import pandas, geopandas, fastapi; print('All packages installed successfully!')"
```

## Getting Help

If issues persist:
1. Check Python version: `python3 --version` (should be 3.11+)
2. Check pip version: `pip --version`
3. Check error messages carefully - they often indicate missing dependencies
4. Try installing packages one by one to identify the problematic package
