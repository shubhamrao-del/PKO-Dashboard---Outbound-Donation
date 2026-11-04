# Calling Analytics & Outreach Intelligence Dashboard

A high-performance executive dashboard and multi-sheet Google Sheets repository designed for tracking and analyzing outbound calling operations.

---

## 🌟 Key Features

1. **Google Sheets Link Repository**:
   - **One-Click Link Ingestion**: Simply paste any Google Sheets link (e.g. `https://docs.google.com/spreadsheets/d/.../edit?usp=sharing`). The backend automatically downloads and parses the latest data.
   - **Intelligent Working Tab Auto-Detection**: Automatically identifies the active working sheet by detecting month and year patterns (e.g., `September 2026`, ` Jan, 2026`, `March 2026`, `Oct-25`, `09-2026`) across any naming format.
   - **Compile Tab Detection**: Automatically detects `Compile`, `Donation`, `Membership`, and master records tabs, letting you switch between monthly caller logs and compiled records seamlessly.
   - **Live Re-sync**: Click "Sync" to pull live updates directly from Google Sheets at any time.

2. **Caller (POC) Performance Analysis**:
   - **POC Calling Volume**: Total calls attempted by each POC.
   - **Answered vs Not Answered Status**: Real-time breakdown of answered calls vs unanswered/dropped calls.
   - **POC Leaderboard**: Performance ranking with color-coded answer conversion rate badges (`High > 40%`, `Medium 15-40%`, `Low < 15%`).
   - **Caller Deep-Dive**: Click on any POC name in the leaderboard to instantly isolate and filter all charts and records for that caller.

3. **Status Breakdown & Granular Categorization**:
   - Classifies calls into **Answered** vs **Unanswered**.
   - Detailed donut chart drilldown for specific statuses: `Answered`, `Not Answered`, `Busy`, `Switch Off`, `Incoming Off`, `Out of Network`, `Invalid / Wrong No.`, and more.

4. **Demographics (Male / Female Analytics)**:
   - Total Male vs Female counts.
   - Percentage share and ratio badges (`% M / % F`).
   - Normalizes varied inputs (`Male`, `Female`, `FEMALE`, `M`, `F`, etc.).

5. **Date of Calling Trajectory**:
   - Daily volume timeline showing call progression across the calendar month.
   - Tracks daily spikes in answered vs dropped calls.

6. **Donations & Membership Conversions**:
   - Built-in tracking for Membership inquiries (`Yes` / `No`) and Donation statuses.
   - Ready for standalone or consolidated `Compile` tabs.

7. **Multi-Sheet Aggregated (Retro) View**:
   - Switch between individual sheets or select **"All Sheets Combined"** to analyze cumulative performance across months.

8. **Export & Detailed Data Grid**:
   - Real-time search, multi-column filtering, pagination (25, 50, 100 records).
   - "Export to CSV" button to download filtered datasets.

---

## 🚀 Pre-Loaded Google Sheets

This repository comes pre-configured with the two sheets provided:
- **Link 1**: `https://docs.google.com/spreadsheets/d/1VUkgSQvxW0803m4nX-LQddoDTIQQCAudk25kAk0Fft4/edit?usp=sharing`
  - *Detected Working Tab*: `September 2026` (6,560 records)
- **Link 2**: `https://docs.google.com/spreadsheets/d/1-99JfloH45bUZAkLH8jukV099kg-Zx32kFz0nvw8exE/edit?usp=sharing`
  - *Detected Working Tab*: ` Jan, 2026` (15,598 records)

---

## 🛠️ Quick Start

### 1. Launch the Dashboard
Run the automated start script:
```bash
cd /Users/shubham/Desktop/AntigravityProjects/Dashboard
./start.sh
```

Or run manually:
```bash
./venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Open in Your Browser
Visit:
```
http://localhost:8000
```

---

## 📂 Project Architecture

```
/Users/shubham/Desktop/AntigravityProjects/Dashboard/
├── backend/
│   ├── app.py              # FastAPI application & REST endpoints
│   ├── sheet_parser.py     # Tab auto-detector, regex engine & openpyxl parser
│   ├── repository.py       # Sheet registry & cache management
│   └── config.py           # Paths, default sheets & settings
├── data/
│   ├── registry.json       # Persistent metadata of connected sheets
│   ├── downloads/          # Downloaded spreadsheets
│   └── cache/              # Cached parsed analytics for instant loading
├── static/
│   ├── css/
│   │   └── style.css       # Modern dark UI theme with glowing accents
│   ├── js/
│   │   ├── app.js          # Main dashboard logic & table pagination
│   │   ├── charts.js       # Chart.js visualization engine
│   │   └── sheet_manager.js# Repository modal & sheet ingestion
│   └── index.html          # Executive dashboard UI
├── requirements.txt        # Python package dependencies
├── start.sh                # Executable startup script
└── README.md
```

---

## 📋 How to Connect Future Google Sheets

1. In the top navigation bar, click **"Sheet Repository"**.
2. Paste your Google Sheet URL into the input field.
3. (Optional) Provide a friendly label (e.g. `March 2026`).
4. Click **"Add & Analyze Sheet"**.
5. The system will:
   - Connect to Google Sheets.
   - Scan all workbook tabs.
   - Automatically pick the month + year working sheet.
   - Generate analytics and save the sheet to your repository.

> **Note on Permissions**: Ensure your Google Sheet sharing setting is set to **"Anyone with the link can view"** so the export endpoint can fetch the data.

