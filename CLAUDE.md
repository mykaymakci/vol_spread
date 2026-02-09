# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time option pricing dashboard that calculates Black-Scholes option prices using live spot prices from an Excel workbook. The application is built with Flask and provides a web interface for monitoring options with dynamic spread adjustments and implied volatility calculations.

## Running the Application

```bash
# Run the Flask application
python flask_app.py
```

The application will:
- Start a Flask server on port 8000
- Automatically open http://localhost:8000 in your browser
- Continuously fetch live data from the open Excel file

**Prerequisites:**
- `fiyat.xlsx` must be open in Microsoft Excel before running
- Required Python packages: `flask`, `pandas`, `numpy`, `scipy`, `xlwings`

## Data Structure

### Input Files

**1.csv**: Static option definitions (no header row)
- Column order: `ad` (name), `dayanak` (underlying asset), `strike`, `vol` (volatility as decimal), `vade` (expiration date DD.MM.YYYY), `carpan` (multiplier), `tip` (type: 'c' for call, 'p' for put)
- Example: `AOIHC,xagusd,55,0.656,27.02.2026,0.02,c`

**fiyat.xlsx**: Live price data source
- Must be open in Excel while the app runs
- App reads range A1:D100 from first sheet
- Column A contains asset names (must match `dayanak` values in CSV)
- Column D contains current prices
- Must include a row for `usdtry` exchange rate

## Architecture

### Backend (flask_app.py)

**Black-Scholes Calculation**:
- `black_scholes_r0()`: Implements Black-Scholes model with risk-free rate r=0
- Uses scipy's `norm.cdf()` for cumulative normal distribution
- Handles expired options (T <= 0) with intrinsic value

**Data Flow**:
1. `/api/data` endpoint initializes COM for xlwings (required for multi-threading)
2. Loads CSV data with pandas, parses dates with format `%d.%m.%Y`
3. Connects to active Excel instance via xlwings
4. Reads spot prices from Excel range A1:D100
5. Calculates time to expiration in years (365.25 days)
6. Computes option prices in USD, converts to TRY using `usdtry` rate
7. Returns JSON with timestamp and results array

### Frontend (templates/index.html)

**Key Features**:
- Client-side Black-Scholes implementation for real-time spread calculations
- Two-way spread system:
  - **Spread TL (Kuruş)**: Direct price adjustment in Turkish Lira cents
  - **Spread Vol (%)**: Volatility adjustment that recalculates price
- Implied volatility calculation using bisection method
- Auto-refresh every 1 second via `setInterval`
- Sortable columns with ascending/descending indicators
- Filter by underlying asset, option type (call/put), and expiration date
- Bulk spread operations that apply to filtered rows
- Input focus preservation during re-renders

**Ask Price Calculation**:
1. Apply volatility spread: `newSigma = originalVol + (spreadVol / 100)`
2. Recalculate Black-Scholes price in USD with new volatility
3. Convert to TRY: `priceTRY = priceUSD * usdtry * carpan`
4. Add spread in kuruş: `askPrice = priceTRY + (spreadTL / 100)`

**Ask IV Calculation**:
1. Reverse-engineer volatility from ask price
2. Convert ask price back to USD: `targetUSD = askPrice / (usdtry * carpan)`
3. Use bisection to find volatility that produces target price
4. Range: 0-500%, tolerance: 0.0001, max iterations: 20

## Important Notes

- xlwings requires Microsoft Excel to be installed and running (Windows/macOS only)
- The app uses `pythoncom.CoInitialize()` to handle COM threading for xlwings
- Debug mode is disabled in production (`debug=False`)
- Browser auto-opens via threading to avoid blocking server startup
- Volatility values in CSV are stored as decimals (0.656 = 65.6%)
- All price calculations assume risk-free rate r=0
