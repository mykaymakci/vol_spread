# Live Option Tracking Dashboard

## Project Overview
This project is a real-time option pricing dashboard built with **Streamlit**. It calculates Black-Scholes option prices for a list of assets defined in a CSV file, using live spot prices fed dynamically from an open Excel workbook.

## Key Features
- **Real-time Integration:** Uses `xlwings` to read data directly from an active Excel instance (`fiyat.xlsx`) without requiring the file to be saved.
- **Black-Scholes Model:** Calculates theoretical option prices (Call/Put) assuming risk-free rate $r=0$.
- **Currency Conversion:** Automatically converts calculated USD prices to TRY based on the live `usdtry` rate fetched from Excel.

## File Structure

### `app.py`
The main application script. It handles:
- **UI:** Renders the dashboard using Streamlit.
- **Calculation:** Implements the Black-Scholes formula.
- **Data Fetching:** Connects to the Excel application to read the range `A1:D100`.

### `1.csv`
Contains the static definitions for the options to be tracked.
**Columns (no header expected):**
1. `ad` (Name)
2. `dayanak` (Underlying Asset)
3. `strike` (Strike Price)
4. `vol` (Volatility)
5. `vade` (Expiration Date - `DD.MM.YYYY`)
6. `carpan` (Multiplier)
7. `tip` (Type - 'c' for Call, 'p' for Put)

### `fiyat.xlsx`
The live data source. **This file must be open in Microsoft Excel while the script runs.**
- **Format:** The script reads columns A (Name) and D (Price) from the first sheet (Range `A1:D100`).
- **Required Data:** Must include rows for the underlying assets (matching `1.csv` "dayanak") and a row for `usdtry`.

## Setup & Usage

### 1. Prerequisites
Ensure you have Python installed along with the required libraries:
```bash
pip install streamlit pandas numpy scipy xlwings
```

### 2. Running the Application
1.  Open `fiyat.xlsx` in Microsoft Excel.
2.  Run the Streamlit app from your terminal:
    ```bash
    streamlit run app.py
    ```
3.  The dashboard will open in your default web browser and update automatically every ~0.5 seconds.

## Development Notes
- **xlwings:** This library requires a local installation of Microsoft Excel (Windows/macOS). It interacts with the *running* Excel process.
- **Performance:** The loop includes a `time.sleep(0.5)` to prevent excessive CPU usage while polling Excel.
