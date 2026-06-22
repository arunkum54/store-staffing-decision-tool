<div align="center">

# 🏪 Retail Staffing Analyser
### **RevInsight — Hiring Decision Engine**

*Should you replace your resigned salesperson? This tool answers that question with data.*

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Web%20App-green?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-RevInsight-orange)](/)

</div>

---

## What This Does

A store owner asks: **"My salesperson sp12 just resigned. Do I need to replace them?"**

This tool answers that question by loading months of historical sales data and running a **10-step analytical framework** — from data quality checks all the way to sensitivity stress tests — returning a clear **REPLACE / DO NOT REPLACE** verdict with full reasoning.

```
Gross Margin = 0.45 × Sales − (3 × Headcount)
  ↳  50% product margin − 5% commission = 45% net rate
  ↳  Breakeven threshold = 3.0 ÷ 0.45 = 6.67 units/month per hire
```

A replacement hire is only justified if they generate **more than 6.67 units/month** in incremental store sales — enough to cover salary after commission.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Installation](#2-installation)
3. [Running the App](#3-running-the-app)
4. [Full Walkthrough](#4-full-walkthrough)
5. [Understanding the 9 Result Panels](#5-understanding-the-9-result-panels)
6. [Test Cases — Verify It Works](#6-test-cases--verify-it-works)
7. [CSV Format Requirements](#7-csv-format-requirements)
8. [Configuration Parameters](#8-configuration-parameters)
9. [The 10-Step Analysis Engine](#9-the-10-step-analysis-engine)
10. [How the Verdict Is Decided](#10-how-the-verdict-is-decided)
11. [Common Issues & Fixes](#11-common-issues--fixes)
12. [Project File Structure](#12-project-file-structure)
13. [API Reference](#13-api-reference)

---

## 1. Quick Start

```bash
# Install dependencies (one-time)
pip install -r requirements.txt

# Start the app
python app.py

# Open in browser
# → http://localhost:5000
```

Upload your CSV → select the resigned salesperson → click **⚡ Run Analysis**.

---

## 2. Installation

### Requirements

- Python **3.8 or higher**
- pip
- A modern browser (Chrome, Edge, Firefox, Safari)
- Internet connection for Google Fonts *(optional — the app works fully offline)*

### Check your Python version

```bash
python --version    # should show 3.8+
# or
python3 --version
```

### Step 1 — Extract the project

Download `staffing_analyser_local.zip` and extract. You'll get:

```
staffing-local/
├── app.py
├── requirements.txt
├── README.md
└── templates/
    └── index.html
```

### Step 2 — Open a terminal in the project folder

| OS | Instructions |
|----|-------------|
| **Windows** | `Win + R` → type `cmd` → `cd C:\Users\YourName\Downloads\staffing-local` |
| **macOS** | Open Terminal → `cd ~/Downloads/staffing-local` |
| **Linux** | `cd ~/Downloads/staffing-local` |

### Step 3 — Install Python packages

```bash
pip install -r requirements.txt
```

This installs: `flask`, `pandas`, `numpy`, `scipy`

> **Troubleshooting install:**
> - `pip` not found → try `pip3 install -r requirements.txt`
> - Permission errors → add `--user` flag: `pip install -r requirements.txt --user`
> - Nothing works → try `python -m pip install -r requirements.txt`

---

## 3. Running the App

```bash
python app.py
```

**Expected output:**

```
====================================================
  🚀  Staffing Analyser running!
  👉  Open http://localhost:5000 in your browser
====================================================
```

Open **http://localhost:5000** in your browser.

- **To stop:** press `Ctrl + C` in the terminal
- **To restart:** run `python app.py` again from the same folder

---

## 4. Full Walkthrough

### Step 1 — Upload your CSV

Drag your CSV file onto the upload zone, or click to browse. The app immediately calls `/preview` to detect columns and active salesperson names.

### Step 2 — Review the Data Preview

The app auto-navigates to the **Data Preview** panel showing the first 15 rows. Each SP is labelled `● active` or `○ departed`. Verify the columns look correct before running.

### Step 3 — Configure Parameters

Back on the **Upload & Configure** panel:

| Parameter | Default | What it means |
|-----------|---------|---------------|
| Resigned Salesperson | Auto-detected (weakest active) | The SP who has resigned |
| Forecast Horizon | 6 months | How many months to project forward |
| Salary per Person / Month | 3 | Monthly fixed salary (same units as Sales) |
| Net Gross Margin Rate | 45% | Product margin minus commission |

The **live formula box** updates as you change values:

```
Gross Margin = 45% × Sales − (3.00 × Headcount)
Breakeven monthly sales per hire = 3.00 ÷ 0.45 = 6.67
```

### Step 4 — Run the Analysis

Click **⚡ Run Analysis**. A spinner appears while all 10 analytical steps run server-side (~1–2 seconds). No data leaves your machine.

### Step 5 — Read the Results

Nine result panels unlock in the sidebar. Navigate freely between them.

---

## 5. Understanding the 9 Result Panels

### Panel 1 · Verdict 🏆

The top-level answer.

- 🟢 **Green banner** = REPLACE
- 🔴 **Red banner** = DO NOT REPLACE
- Shows 6-month gross margin gain, sp12's rank, confidence level, and whether all 7 sensitivity scenarios agree

**Example output (original RevI-Test.csv, sp12):**

```
✅ REPLACE sp12 — Immediately

  sp12 avg/month:      15.47
  sp12 rank:           #5 of 16
  Incremental GM/mo:   +3.96
  6-month GM gain:     +23.77
  Breakeven required:  6.67
  Times breakeven:     2.32×
  Confidence:          HIGH
```

---

### Panel 2 · Productivity 📈

Ranked table of every salesperson who ever worked at the store.

| Column | Description |
|--------|-------------|
| Avg Monthly Sales | Visual bar chart (proportional) |
| Median | Robust central tendency — less affected by outlier months |
| Std Dev / CV | Volatility; high CV = inconsistent performer |
| Trend | ↑ Improving / ↓ Declining / → Stable |
| Total | Lifetime sales contribution |
| Tier | **TOP** (≥ 2× breakeven) · **MID** (≥ breakeven) · **WEAK** (below breakeven) |
| Inc GM | Incremental gross margin per month |

The resigned SP row is **highlighted in gold**.

A **cannibalization check** below the table shows sales-per-employee by headcount level. A mild decline at 7→8 staff is normal and acceptable.

---

### Panel 3 · Marginal Analysis 🔬

Four independent methods estimate the incremental store sales from one additional person:

| Method | Approach | Reliability |
|--------|----------|-------------|
| A — Raw (6 vs 7 staff) | Mean difference between headcount levels | Medium |
| A — Detrended (6 vs 7) | Same, after removing long-run trend | Med-High |
| B — Raw (7 vs 8 staff) | Mean difference between 7 and 8 staff months | Medium |
| B — Detrended (7 vs 8) | Detrended 7v8 comparison | Med-High |
| C — OLS Regression | `Sales ~ Headcount + Month` with t-stat/p-value | High |
| D — Direct SP History | The resigned SP's own monthly average | **Highest** |

> **Conservative rule:** the scenario model uses `min(regression, SP_avg)`. A weak SP is never over-valued by the generic regression estimate.

---

### Panel 4 · Forecast 🔭

Four methods combined into a weighted consensus:

| Method | Weight | Description |
|--------|--------|-------------|
| A — Moving Average | 15% | Last 12 months flat average |
| B — Trend | 25% | Linear trend from last 36 months |
| C — Seasonal | **40%** | MA scaled by seasonal index *(highest — retail is seasonal)* |
| D — OLS Global | 20% | Long-run trend from full history |

A bar chart shows all 4 methods side-by-side per forecast month. A seasonal calendar highlights upcoming peak and slow months.

---

### Panel 5 · Scenarios ⚖️

Four staffing strategies compared over the forecast horizon:

| Scenario | Description |
|----------|-------------|
| **S1: Replace Now** | 7 staff all 6 months — hire immediately |
| **S2: No Replace** | 6 staff all 6 months — leave vacant |
| **S3: Delay 3 Months** | 6 staff months 1–3, then 7 staff months 4–6 |
| **S4: Flexible** | 7 staff in peak months, 6 in slow months |

Each scenario shows a full P&L: Total Sales · Salary Cost · Commission · **Gross Margin** · Avg GM/month · Risk (Low / Medium / High).

---

### Panel 6 · Sensitivity 🧪

Seven stress tests on the base-case verdict:

| Stress Scenario | What changes |
|-----------------|-------------|
| Base case | No change |
| Sales −10% | All forecasts reduced 10% |
| Sales +10% | All forecasts increased 10% |
| Marginal −50% | New hire generates half expected sales |
| Marginal +50% | New hire generates 50% more than expected |
| Sales −10% + Marg −50% | **Worst plausible case** |
| Sales +10% + Marg +50% | Best plausible case |

- All 7 show REPLACE → **Confidence: HIGH**
- Some flip → **Confidence: MEDIUM or LOW**

---

### Panel 7 · Full Report 📄

Embeds the complete HTML report with download options:

- **⬇ Download HTML Report** — full styled report, opens in any browser
- **⬇ Download Summary CSV** — key metrics, scenarios, and sensitivity table
- **🖨 Print** — use "Save as PDF" in the browser print dialog

---

## 6. Test Cases — Verify It Works

Four test CSV files are provided. Upload each one, select `sp12`, and verify the verdict matches.

---

### Test 1 · `test1_strong_REPLACE.csv` ✅

**Profile:** sp12 averages **~15.00/month** — a solid mid-tier performer.

| Metric | Expected |
|--------|----------|
| Verdict | ✅ **REPLACE** |
| sp12 avg/month | ~15.00 |
| Incremental GM/month | ~+3.75 |
| 6-month GM gain | > +20 |
| Confidence | **HIGH** |
| All sensitivity rows | REPLACE |

**Why REPLACE:** 15.00/month is 2.25× the breakeven of 6.67. After salary, this yields +3.75 incremental GM/month → approximately +22.50 in forgone profit over 6 months if not replaced.

---

### Test 2 · `test2_weak_NOREPLACE.csv` ❌

**Profile:** sp12 averages **~3.03/month** — dead last of 16, well below breakeven.

| Metric | Expected |
|--------|----------|
| Verdict | ❌ **DO NOT REPLACE** |
| sp12 avg/month | ~3.03 |
| Incremental GM/month | ~−1.64 |
| 6-month GM gain | < −9 |
| Confidence | **HIGH** |
| All sensitivity rows | NO REPLACE |

**Why DO NOT REPLACE:** 3.03/month is far below the 6.67 breakeven. After salary, this yields −1.64 GM/month — replacing would *cost* the store ~−9.84 over 6 months.

**Key logic being tested:** The OLS regression estimates ~15/month (generic average), but the conservative rule uses `min(15.53, 3.03) = 3.03` → correctly triggers NO REPLACE based on sp12's own history.

---

### Test 3 · `test3_borderline_UNCERTAIN.csv` ⚠️

**Profile:** sp12 averages **~7.00/month** — just barely above the 6.67 breakeven.

| Metric | Expected |
|--------|----------|
| Verdict | ✅ REPLACE *(barely)* |
| sp12 avg/month | ~7.00 |
| Incremental GM/month | ~+0.14 |
| 6-month GM gain | Small positive (< +5) |
| Confidence | **LOW or MEDIUM** |
| Sensitivity rows | Some may flip to NO REPLACE |

**What to look for:** The 6-month GM difference between S1 and S2 is very small. Confidence should **not** be HIGH. Check the Sensitivity panel for any NO REPLACE rows — this is the edge case the tool is designed to flag honestly.

---

### Test 4 · `test4_top_REPLACE.csv` 🌟

**Profile:** sp12 averages **~24.75/month** — ranked #1 of 16, a star performer.

| Metric | Expected |
|--------|----------|
| Verdict | ✅ **REPLACE** |
| sp12 avg/month | ~24.75 |
| Incremental GM/month | ~+8.14 |
| 6-month GM gain | > +45 |
| Confidence | **HIGH** |
| All sensitivity rows | REPLACE |

**Note on regression cap:** sp12 directly averages 24.75/month, but the regression estimates ~15/month (generic average). The conservative rule uses `min(15, 24.75) = 15` — we cannot assume a replacement hire will match a star's output.

---

### Summary

```
Test File                          sp12 Avg   Inc GM/mo   Verdict        Confidence
─────────────────────────────────────────────────────────────────────────────────────
test1_strong_REPLACE.csv           ~15.00     +3.75       REPLACE        HIGH
test2_weak_NOREPLACE.csv            ~3.03     −1.64       NO REPLACE     HIGH
test3_borderline_UNCERTAIN.csv      ~7.00     +0.14       REPLACE        LOW/MEDIUM
test4_top_REPLACE.csv              ~24.75     +8.14       REPLACE        HIGH
─────────────────────────────────────────────────────────────────────────────────────
Breakeven threshold                  6.67      0.00
```

If all 4 match → the app is working correctly.

---

## 7. CSV Format Requirements

### Column structure

```
Month, Sales, sale sp1, sale sp2, sale sp3, ...
    1,  95.3,      15.2,      13.1,      12.4, ...
    2, 101.7,      16.8,      14.2,      13.0, ...
```

### Rules

| Rule | Detail |
|------|--------|
| `Month` column | Must be named `Month` (case-insensitive); sequential integers starting at 1 |
| `Sales` column | Must be named `Sales`; total store sales that month |
| SP columns | Must contain `sp` in the name: `sale sp1`, `sp1`, `sp_1` all work |
| Zero = absent | A `0` in an SP column means that person was not employed that month |
| No missing values | All cells must have a value (use `0` for inactive SPs) |
| Minimum rows | At least 24 months recommended for seasonal analysis |

### Auto-detection

The app automatically detects:
- Which columns are salesperson columns *(any column name containing `sp`)*
- Which SPs are currently active *(non-zero in the last row)*
- The weakest active SP *(suggested as the default resign candidate)*

### Example valid CSV (abbreviated)

```csv
Month,Sales,sale sp1,sale sp2,sale sp3,sale sp4
1,45.2,12.1,10.4,8.7,0
2,52.8,13.5,11.2,9.1,0
3,61.4,14.8,12.6,10.0,8.2
4,70.9,15.2,13.1,10.8,9.3
```

---

## 8. Configuration Parameters

All parameters can be changed before each run. The formula box updates live.

| Parameter | Default | Range | Notes |
|-----------|---------|-------|-------|
| Resigned SP | Auto (weakest active) | Any active SP | Override in dropdown |
| Forecast horizon | 6 months | 3–12 | Slide to change |
| Salary per person/month | 3 | Any positive number | Same units as Sales column |
| Net GM rate | 45% | 20–70% | Product margin minus commission |

**Examples:**

- *Different salary:* If your salary is ₹15,000/month and sales are in ₹000s, enter `15`. The breakeven updates live.
- *Different GM rate:* If product margin is 60% and commission is 8%, set GM rate to `52%`. New breakeven = 3.0 ÷ 0.52 = **5.77**.

---

## 9. The 10-Step Analysis Engine

All analysis runs in `app.py` on the Flask backend. **No data leaves your machine.**

| Step | What Runs | Key Output |
|------|-----------|------------|
| **1** | Data Quality Audit | Missing values, duplicates, outliers, month continuity, SP-sum vs store-total discrepancy |
| **2** | Staffing History | Headcount per month, distribution, avg/median, tenure table, active/departed status |
| **3** | Productivity Analysis | Per-SP: avg, median, std dev, CV, total, trend slope/direction, tier, incremental GM |
| **4** | Marginal Contribution | 4 methods: raw/detrended group comparisons + OLS regression (t-stat/p-value) + direct SP history |
| **5** | Cannibalization | Sales-per-head by headcount level, Pearson correlation, diminishing-returns slope |
| **6** | Seasonality | 12 seasonal indices via ratio-to-MA method, peak/slow month classification |
| **7** | Forecasting | MA + Trend + Seasonal + OLS global; weighted 15/25/40/20 consensus |
| **8** | Scenario Modeling | 4 scenarios × full P&L (sales, salary, commission, GM, risk) |
| **9** | Sensitivity Analysis | 7 stress tests (±10% sales, ±50% marginal, combinations) |
| **10** | Decision Framework | Conservative verdict, confidence scoring (5-point evidence scale), staffing rule |

---

## 10. How the Verdict Is Decided

### Step 1 — Compute the marginal sales estimate

```python
marg_regression = OLS coefficient on headcount    # e.g. ~15.53
marg_sp_direct  = resigned SP's avg monthly sales # e.g. 15.47 for sp12
marg_used       = min(marg_regression, marg_sp_direct)  # conservative
```

**Why the minimum?**
The regression estimates what an *average* person adds. If the resigned SP is weaker (e.g. 3/month vs regression 15/month), their own track record is the more specific, relevant evidence. If they are stronger, the regression *caps* the estimate — we cannot assume a replacement will match a star's output.

### Step 2 — Compute scenario gross margins

```python
# Base forecast = weighted consensus for a 6-staff team
# marg_used = incremental sales from the 7th person

S1_GM = 0.45 × (forecast + marg_used) × horizon − 7 × salary × horizon
S2_GM = 0.45 × forecast × horizon − 6 × salary × horizon
diff  = S1_GM − S2_GM
```

### Step 3 — Issue the verdict

```python
verdict = "REPLACE" if diff > 0 else "NO REPLACE"
```

### Step 4 — Score confidence

Five evidence signals, each worth 1 point:

| Signal | Condition |
|--------|-----------|
| Above breakeven | `sp_avg > breakeven` |
| Top-half performer | `sp_rank ≤ total_sps ÷ 2` |
| All sensitivity agree | `always_replace == True` |
| Detrended comparison positive | Detrended 7v8 incremental GM > 0 |
| Regression has meaningful fit | `R² > 0.15` |

| Score | Confidence |
|-------|------------|
| 4 or 5 / 5 | **HIGH** |
| 2 or 3 / 5 | **MEDIUM** |
| 0 or 1 / 5 | **LOW** |

---

## 11. Common Issues & Fixes

| Problem | Likely Cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: flask` | Dependencies not installed | `pip install -r requirements.txt` |
| `Address already in use` (port 5000) | Another app using port 5000 | Change `port=5000` to `port=8080` in `app.py`; open `http://localhost:8080` |
| Port 5000 blocked on Mac | macOS AirPlay Receiver uses 5000 | System Preferences → AirDrop & Handoff → disable AirPlay Receiver, or change port to 8080 |
| CSV not loading | Wrong column format | Ensure SP columns contain `sp` in the name; see [CSV Format](#7-csv-format-requirements) |
| Dropdown shows wrong SP | App auto-suggests weakest active | Override manually in the dropdown |
| Verdict seems wrong | Wrong SP selected | Check the dropdown; reload and re-select |
| Fonts not loading | No internet connection | App still works; falls back to system fonts |
| `pip3` not found | Python path issue | `python -m pip install -r requirements.txt` |
| Analysis takes > 5 seconds | Very large CSV (200+ months) | Normal — wait for the spinner to clear |

---

## 12. Project File Structure

```
staffing-local/
│
├── app.py                    ← Flask backend — all 10 analysis steps
│   ├── GET  /                → serves index.html
│   ├── POST /analyse         → runs full analysis, returns JSON
│   └── POST /preview         → fast column detection for upload preview
│
├── requirements.txt          ← Python dependencies (flask, pandas, numpy, scipy)
│
├── README.md                 ← This file
│
├── templates/
│   └── index.html            ← Full frontend (HTML + CSS + JavaScript)
│       ├── Sidebar navigation (9 panels)
│       ├── Upload & Configure panel
│       ├── Data Preview panel
│       ├── Verdict panel
│       ├── Productivity panel
│       ├── Marginal Analysis panel
│       ├── Forecast panel
│       ├── Scenarios panel
│       ├── Sensitivity panel
│       └── Full Report panel (iframe + download buttons)
│
└── uploads/                  ← Temporary folder (auto-created; safe to delete)
```

---

## 13. API Reference

### `POST /analyse`

**Request:** `multipart/form-data`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file` | file | *required* | CSV file |
| `resigned` | string | `sp12` | SP column name |
| `horizon` | int | `6` | Forecast months |
| `salary` | float | `3` | Monthly salary per person |
| `gm_rate` | float | `45` | Net GM rate as percentage |

**Response (JSON):**

```json
{
  "verdict":        "REPLACE",
  "confidence":     "HIGH",
  "diff_6mo":       23.77,
  "sp12_avg":       15.47,
  "sp12_rank":      5,
  "sp12_inc_gm":    3.96,
  "sp12_tier":      "TOP",
  "sp12_trend_dir": "↑ Improving",
  "breakeven":      6.67,
  "s1_gm":          201.79,
  "s2_gm":          178.02,
  "s1": { "sales": 728.4, "salary": 126.0, "commission": 36.42, "gm": 201.79, "risk": "Low" },
  "s2": { "..." : "..." },
  "s3": { "..." : "..." },
  "s4": { "..." : "..." },
  "sens": [
    { "label": "Base case", "s1": 201.79, "s2": 178.02, "diff": 23.77, "v": "REPLACE" }
  ],
  "prod": [
    { "SP": "sp7", "avg": 21.21, "rank": 1, "tier": "TOP", "trend_dir": "↑ Improving" }
  ],
  "seas": { "1": 1.064, "2": 0.842 },
  "fc_w": [114.4, 113.5, 112.8, 108.9, 99.4, 86.6],
  "dq":   { "rows": 81, "missing": 0, "duplicates": 0, "outlier_months": [] }
}
```

---

### `POST /preview`

**Request:** `multipart/form-data` — `file` field only.

**Response (JSON):**

```json
{
  "rows": 81,
  "sp_cols": ["sp1", "sp2", "sp16"],
  "active_sps": ["sp8", "sp10", "sp12", "sp13", "sp14", "sp15", "sp16"],
  "suggested_resigned": "sp12",
  "sp_stats": [{ "sp": "sp12", "avg": 15.47, "months": 36, "active": true }],
  "preview": [{ "Month": 1, "Sales": 23.1 }]
}
```

---

## Adapting for Any Store

This tool works for **any retail store**, not just the original Bangalore clothing store. To adapt it:

1. **Different salary** — Change the salary slider (e.g. ₹12,000/month → enter `12` if sales are in ₹000s)
2. **Different margin** — Adjust the GM rate slider (e.g. 60% product margin − 8% commission = `52%`)
3. **Different horizon** — Use the horizon slider for 3, 6, or 12-month planning
4. **Different resigned SP** — Pick any active SP from the dropdown
5. **More/fewer staff** — The analysis adapts automatically to your headcount levels

The CSV only needs three things: a `Month` column, a `Sales` column, and one column per salesperson with `sp` somewhere in the name.

---

<div align="center">

*Built for RevInsight hiring challenge · Objective: maximise gross margin, not sales*

</div>
