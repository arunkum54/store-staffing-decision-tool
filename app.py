"""
app.py  —  Retail Staffing Analyser
Flask backend: receives CSV upload, runs full 10-step analysis, returns JSON.

Run:  python3 app.py
Open: http://localhost:5000
"""

import io
import json
import logging
import os
import warnings

import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request
from scipy import stats
import streamlit as st

warnings.filterwarnings("ignore")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024   # 16 MB max upload

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

DEFAULT_SALARY  = 3.0
DEFAULT_GM_RATE = 0.45
DEFAULT_HORIZON = 6

MON = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
       7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTE: index
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTE: /analyse  — full 10-step analysis
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/analyse", methods=["POST"])
def analyse():
    """
    POST multipart/form-data:
      file      — CSV file
      resigned  — SP id e.g. "sp12"
      horizon   — forecast months (int)
      salary    — monthly salary per person (float)
      gm_rate   — net GM rate as % e.g. 45
    Returns JSON with every field needed by the frontend.
    """
    try:
        # ── inputs ────────────────────────────────────────────────────────────
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        csv_text  = request.files["file"].read().decode("utf-8")
        resigned  = request.form.get("resigned", "sp12").strip()
        horizon   = int(request.form.get("horizon",  DEFAULT_HORIZON))
        salary    = float(request.form.get("salary",  DEFAULT_SALARY))
        gm_rate   = float(request.form.get("gm_rate", 45)) / 100.0
        commission_rate = 1.0 - gm_rate - 0.50  # derive commission from rates
        # Simpler: gross_margin_rate = 50% - commission%; net_gm provided directly
        net_gm    = gm_rate
        gross_margin_pct = 0.50            # product gross margin
        comm_pct  = gross_margin_pct - net_gm   # commission rate (e.g. 5%)
        breakeven = salary / net_gm

        log.info("Analysis — resigned=%s horizon=%d salary=%s gm=%.0f%%",
                 resigned, horizon, salary, gm_rate * 100)

        # ── STEP 1: Load & clean CSV ──────────────────────────────────────────
        df = pd.read_csv(io.StringIO(csv_text))
        df.columns = [c.strip() for c in df.columns]

        sp_cols_raw = [c for c in df.columns
                       if "sp" in c.lower()
                       and c.strip().lower() not in {"sales", "month"}]
        rename_map  = {c: c.replace("sale ", "").replace("Sale ", "").strip()
                       for c in sp_cols_raw}
        df.rename(columns=rename_map, inplace=True)
        sp_cols = list(rename_map.values())

        if "Sales" not in df.columns:
            s_col = [c for c in df.columns if "sale" in c.lower() and "sp" not in c.lower()]
            if s_col:
                df.rename(columns={s_col[0]: "Sales"}, inplace=True)

        n = len(df)
        y = df["Sales"].values

        # ── STEP 1: Data Quality Audit ────────────────────────────────────────
        disc     = (df[sp_cols].sum(axis=1) - df["Sales"]).abs()
        outliers = df[np.abs(stats.zscore(y)) > 3]["Month"].tolist()
        dq = {
            "rows":           n,
            "missing":        int(df.isnull().sum().sum()),
            "duplicates":     int(df["Month"].duplicated().sum()),
            "sp_count":       len(sp_cols),
            "max_disc":       round(float(disc.max()), 4),
            "mean_disc":      round(float(disc.mean()), 4),
            "outlier_months": outliers,
            "consecutive":    bool((df["Month"].diff().dropna() == 1).all()),
        }

        # ── STEP 2: Staffing History ──────────────────────────────────────────
        df["headcount"] = (df[sp_cols] > 0).sum(axis=1)
        hc_dist = {int(k): int(v)
                   for k, v in df["headcount"].value_counts().sort_index().items()}

        tenure = []
        for sp in sp_cols:
            act = df[df[sp] > 0]["Month"]
            if len(act) > 0:
                tenure.append({
                    "SP":     sp,
                    "First":  int(act.min()),
                    "Last":   int(act.max()),
                    "Months": int(len(act)),
                    "Status": "Active" if act.max() == df["Month"].max() else "Departed",
                })

        # ── STEP 3: Salesperson Productivity (with trend per SP) ──────────────
        prod = []
        for sp in sp_cols:
            active_df = df[df[sp] > 0][["Month", sp]].copy()
            active    = active_df[sp]
            if len(active) == 0:
                continue
            # Trend slope: positive = improving, negative = declining
            if len(active) >= 3:
                sp_slope, _ = np.polyfit(active_df["Month"].values, active.values, 1)
            else:
                sp_slope = 0.0
            # Performance tier vs breakeven
            avg_val = float(active.mean())
            tier = ("TOP" if avg_val >= breakeven * 2
                    else "MID" if avg_val >= breakeven
                    else "WEAK")
            prod.append({
                "SP":        sp,
                "AM":        int(len(active)),
                "avg":       round(avg_val, 2),
                "med":       round(float(active.median()), 2),
                "std":       round(float(active.std() if len(active) > 1 else 0), 2),
                "cv":        round(float(active.std() / active.mean()
                                  if len(active) > 1 and active.mean() > 0 else 0), 3),
                "tot":       round(float(active.sum()), 2),
                "trend_slope": round(float(sp_slope), 3),   # NEW: trend per SP
                "trend_dir": ("↑ Improving" if sp_slope > 0.1
                              else "↓ Declining" if sp_slope < -0.1
                              else "→ Stable"),
                "tier":      tier,                           # NEW: TOP/MID/WEAK
                "inc_gm":    round(net_gm * avg_val - salary, 2),  # NEW: individual GM
            })

        prod_df = (pd.DataFrame(prod)
                   .sort_values("avg", ascending=False)
                   .reset_index(drop=True))
        prod_df["rank"] = range(1, len(prod_df) + 1)

        sp12_row  = (prod_df[prod_df["SP"] == resigned].iloc[0]
                     if resigned in prod_df["SP"].values else prod_df.iloc[-1])
        sp12_avg  = float(sp12_row["avg"])
        sp12_rank = int(sp12_row["rank"])
        total_sps = len(prod_df)

        # ── STEP 4: Marginal Contribution — all 4 methods ─────────────────────
        # Detrend for Methods A & B
        sl_t, ic_t = np.polyfit(df["Month"].values, y, 1)
        df["detrended"] = y - (sl_t * df["Month"].values + ic_t)

        grp = {hc: df[df["headcount"] == hc] for hc in df["headcount"].unique()}

        # Method A: 6 vs 7 staff (raw)
        a_6v7 = float(grp[7]["Sales"].mean() - grp[6]["Sales"].mean()) \
                if 6 in grp and 7 in grp else None
        a_6v7_detr = float(grp[7]["detrended"].mean() - grp[6]["detrended"].mean()) \
                     if 6 in grp and 7 in grp else None
        a_6v7_n    = (len(grp[6]) if 6 in grp else 0, len(grp[7]) if 7 in grp else 0)

        # Method B: 7 vs 8 staff (raw + detrended)
        a_7v8      = float(grp[8]["Sales"].mean()     - grp[7]["Sales"].mean())     if 8 in grp and 7 in grp else 0.0
        b_7v8      = float(grp[8]["detrended"].mean() - grp[7]["detrended"].mean()) if 8 in grp and 7 in grp else 0.0
        a_7v8_n    = (len(grp[7]) if 7 in grp else 0, len(grp[8]) if 8 in grp else 0)

        # Method C: OLS regression Sales ~ Headcount + Month
        X    = np.column_stack([np.ones(n), df["headcount"].values, df["Month"].values])
        beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        yp   = X @ beta
        r2   = float(1 - np.sum((y - yp)**2) / np.sum((y - y.mean())**2))
        marg = float(beta[1])   # marginal sales per extra person (regression)

        # t-test significance for headcount coefficient
        residuals = y - yp
        mse       = np.sum(residuals**2) / (n - 3)
        XtX_inv   = np.linalg.pinv(X.T @ X)
        se_beta   = np.sqrt(mse * np.diag(XtX_inv))
        t_stat_hc = beta[1] / se_beta[1] if se_beta[1] > 0 else 0
        p_val_hc  = float(2 * (1 - stats.t.cdf(abs(t_stat_hc), df=n-3)))

        # Method D: resigned SP's own historical average (direct evidence)
        # Conservative rule: use the MINIMUM of regression & SP direct history
        # so a weak hire is never over-valued by generic regression
        marg_conservative = min(marg, sp12_avg)

        # Incremental GM for each method
        def inc_gm(marginal_sales):
            return round(net_gm * marginal_sales - salary, 2)

        marginal_methods = {
            "A_raw_6v7":    {"sales": round(a_6v7, 2) if a_6v7 is not None else None,
                             "inc_gm": inc_gm(a_6v7) if a_6v7 is not None else None,
                             "n": a_6v7_n, "note": "Raw mean diff; confounded by trend"},
            "A_detr_6v7":   {"sales": round(a_6v7_detr, 2) if a_6v7_detr is not None else None,
                             "inc_gm": inc_gm(a_6v7_detr) if a_6v7_detr is not None else None,
                             "n": a_6v7_n, "note": "Detrended 6v7; better than raw"},
            "B_raw_7v8":    {"sales": round(a_7v8, 2), "inc_gm": inc_gm(a_7v8),
                             "n": a_7v8_n, "note": "Raw 7v8; trend confounded"},
            "B_detr_7v8":   {"sales": round(b_7v8, 2), "inc_gm": inc_gm(b_7v8),
                             "n": a_7v8_n, "note": "Detrended 7v8; most reliable group comparison"},
            "C_regression": {"sales": round(marg, 2), "inc_gm": inc_gm(marg),
                             "r2": round(r2, 4), "t_stat": round(t_stat_hc, 3),
                             "p_val": round(p_val_hc, 4),
                             "note": f"OLS controls for time trend (R²={r2:.3f})"},
            "D_direct_sp":  {"sales": round(sp12_avg, 2), "inc_gm": inc_gm(sp12_avg),
                             "note": f"{resigned} own 36-month history; most SP-specific"},
            "USED":         {"sales": round(marg_conservative, 2),
                             "inc_gm": inc_gm(marg_conservative),
                             "note": "Conservative min(C, D) used in scenarios"},
        }

        # ── STEP 5: Cannibalization ───────────────────────────────────────────
        df["sph"] = df["Sales"] / df["headcount"]
        sph_hc    = {int(k): round(float(v), 2)
                     for k, v in df.groupby("headcount")["sph"].mean().items()}
        try:
            corr_r, corr_p = stats.pearsonr(df["headcount"], df["sph"])
        except Exception:
            corr_r, corr_p = 0.0, 1.0

        # Diminishing returns: slope of sph vs headcount
        hc_vals  = np.array(list(sph_hc.keys()), dtype=float)
        sph_vals = np.array(list(sph_hc.values()), dtype=float)
        can_slope = float(np.polyfit(hc_vals, sph_vals, 1)[0]) if len(hc_vals) > 1 else 0.0

        # ── STEP 6: Seasonality ───────────────────────────────────────────────
        df["moy"]   = ((df["Month"] - 1) % 12) + 1
        df["ma12"]  = df["Sales"].rolling(12, center=True).mean()
        df["ratio"] = df["Sales"] / df["ma12"]
        seas        = df.groupby("moy")["ratio"].mean()
        seas        = seas / seas.mean()
        seas_dict   = {int(k): round(float(v), 3) for k, v in seas.items()}
        peak_months = [m for m, si in seas_dict.items() if si > 1.10]
        slow_months = [m for m, si in seas_dict.items() if si < 0.85]

        # ── STEP 7: Forecasting — 4 methods ──────────────────────────────────
        fm   = list(range(n + 1, n + horizon + 1))
        fmoy = [((m - 1) % 12) + 1 for m in fm]
        ma12 = float(y[-12:].mean())

        sl36, ic36 = np.polyfit(np.arange(min(36, n)), y[-min(36, n):], 1)
        fc_a = [ma12] * horizon                                          # Method A: MA
        fc_b = [float(sl36 * (min(36, n) + i) + ic36) for i in range(horizon)]  # Method B: trend
        fc_c = [float(ma12 * seas.get(m, 1.0)) for m in fmoy]          # Method C: seasonal
        fc_d = [float(sl_t * (n + i) + ic_t)   for i in range(horizon)] # Method D: OLS global
        fc_w = [0.15*fc_a[i] + 0.25*fc_b[i] + 0.40*fc_c[i] + 0.20*fc_d[i]
                for i in range(horizon)]                                  # Weighted consensus

        # ── STEP 8: Scenario Modeling (with commission shown separately) ──────
        def scenario_detail(sales_l, hc_l):
            """Return full P&L breakdown for a scenario."""
            total_sales  = sum(sales_l)
            total_salary = sum(salary * h for h in hc_l)
            total_comm   = comm_pct * total_sales
            gross_margin = net_gm * total_sales - total_salary
            # Risk: std dev of monthly GM
            monthly_gms  = [net_gm * s - salary * h for s, h in zip(sales_l, hc_l)]
            gm_std       = float(np.std(monthly_gms)) if len(monthly_gms) > 1 else 0.0
            return {
                "sales":       round(total_sales, 2),
                "salary":      round(total_salary, 2),
                "commission":  round(total_comm, 2),       # NOW SHOWN SEPARATELY
                "gm":          round(gross_margin, 2),
                "avg_gm_mo":   round(gross_margin / len(sales_l), 2),
                "gm_std":      round(gm_std, 2),           # RISK metric
                "risk":        ("Low"    if gm_std < 5
                                else "Medium" if gm_std < 15
                                else "High"),
            }

        b6      = fc_w
        b7      = [s + marg_conservative for s in b6]
        flex_hc = [7 if seas.get(m, 1.0) > 1.0 else 6 for m in fmoy]
        flex_s  = [b7[i] if flex_hc[i] == 7 else b6[i] for i in range(horizon)]

        s1 = scenario_detail(b7, [7] * horizon)
        s2 = scenario_detail(b6, [6] * horizon)
        s3 = scenario_detail(b6[:3] + b7[3:], [6, 6, 6] + [7] * (horizon - 3))
        s4 = scenario_detail(flex_s, flex_hc)

        diff = round(s1["gm"] - s2["gm"], 2)

        # ── STEP 9: Sensitivity Analysis ──────────────────────────────────────
        sens = []
        for label, sm, mm in [
            ("Base case",               1.0, 1.0),
            ("Sales −10%",              0.9, 1.0),
            ("Sales +10%",              1.1, 1.0),
            ("Marginal −50%",           1.0, 0.5),
            ("Marginal +50%",           1.0, 1.5),
            ("Sales −10% + Marg −50%",  0.9, 0.5),
            ("Sales +10% + Marg +50%",  1.1, 1.5),
        ]:
            a6_ = [s * sm for s in b6]
            a7_ = [s + marg_conservative * mm for s in a6_]
            d1  = scenario_detail(a7_, [7] * horizon)
            d2  = scenario_detail(a6_, [6] * horizon)
            verdict = "REPLACE" if d1["gm"] > d2["gm"] else "NO REPLACE"
            sens.append({
                "label":  label,
                "s1_gm":  d1["gm"],
                "s2_gm":  d2["gm"],
                "s1":     d1["gm"],   # alias for frontend compat
                "s2":     d2["gm"],
                "diff":   round(d1["gm"] - d2["gm"], 2),
                "v":      verdict,
            })

        always_replace = all(s["v"] == "REPLACE" for s in sens)

        # ── STEP 10: Decision Framework ───────────────────────────────────────
        inc_gm_val     = round(net_gm * sp12_avg - salary, 2)
        replace        = diff > 0
        times_breakeven = round(sp12_avg / breakeven, 2) if breakeven > 0 else 0

        # Confidence level — based on evidence strength
        evidence_score = sum([
            sp12_avg > breakeven,            # above breakeven
            sp12_rank <= total_sps // 2,     # top half performer
            always_replace,                  # all sensitivity tests agree
            inc_gm(b_7v8) > 0,              # detrended comparison positive
            r2 > 0.15,                       # regression has some fit
        ])
        confidence = ("HIGH"   if evidence_score >= 4
                      else "MEDIUM" if evidence_score >= 2
                      else "LOW")

        # ── Assemble result ───────────────────────────────────────────────────
        result = {
            # identifiers
            "n":              n,
            "resigned":       resigned,
            "horizon":        horizon,
            "NET_GM":         net_gm,
            "GROSS_MARGIN":   gross_margin_pct,
            "COMM_RATE":      comm_pct,
            "SAL":            salary,
            "BREAKEVEN":      round(breakeven, 2),

            # Step 1 — data quality
            "dq":             dq,

            # Step 2 — staffing history
            "hc_dist":        hc_dist,
            "avg_hc":         round(float(df["headcount"].mean()), 2),
            "median_hc":      float(df["headcount"].median()),
            "tenure":         tenure,

            # Step 3 — productivity
            "prod":           prod_df.to_dict("records"),
            "sp12_avg":       sp12_avg,
            "sp12_rank":      sp12_rank,
            "sp12_inc_gm":    inc_gm_val,
            "sp12_trend":     float(sp12_row.get("trend_slope", 0)),
            "sp12_trend_dir": str(sp12_row.get("trend_dir", "→ Stable")),
            "sp12_tier":      str(sp12_row.get("tier", "MID")),
            "total_sps":      total_sps,
            "breakeven":      round(breakeven, 2),
            "times_breakeven": times_breakeven,

            # Step 4 — marginal contribution (all 4 methods)
            "marginal_methods": marginal_methods,
            "marg":           round(marg, 2),
            "marg_used":      round(marg_conservative, 2),
            "inc_gm_reg":     inc_gm(marg),
            "inc_gm_used":    inc_gm(marg_conservative),
            "r2":             round(r2, 4),
            "t_stat_hc":      round(t_stat_hc, 3),
            "p_val_hc":       round(p_val_hc, 4),
            "a_7v8":          round(a_7v8, 2),
            "b_7v8":          round(b_7v8, 2),
            "a_6v7":          round(a_6v7, 2) if a_6v7 is not None else None,
            "trend":          round(float(sl_t), 3),

            # Step 5 — cannibalization
            "sph_hc":         sph_hc,
            "corr_r":         round(float(corr_r), 3),
            "corr_p":         round(float(corr_p), 4),
            "can_slope":      round(can_slope, 3),

            # Step 6 — seasonality
            "seas":           seas_dict,
            "peak_months":    peak_months,
            "slow_months":    slow_months,

            # Step 7 — forecast
            "fc_a":           [round(x, 1) for x in fc_a],
            "fc_b":           [round(x, 1) for x in fc_b],
            "fc_c":           [round(x, 1) for x in fc_c],
            "fc_d":           [round(x, 1) for x in fc_d],
            "fc_w":           [round(x, 1) for x in fc_w],
            "fm":             fm,
            "fmoy":           fmoy,

            # Step 8 — scenarios (full P&L each)
            "s1":             s1,
            "s2":             s2,
            "s3":             s3,
            "s4":             s4,
            # keep flat aliases for backward compat with frontend
            "s1_gm":          s1["gm"],
            "s2_gm":          s2["gm"],
            "s3_gm":          s3["gm"],
            "s4_gm":          s4["gm"],
            "s1_s":           s1["sales"],
            "s2_s":           s2["sales"],
            "s1_sal":         s1["salary"],
            "s2_sal":         s2["salary"],
            "s1_comm":        s1["commission"],
            "s2_comm":        s2["commission"],
            "diff_6mo":       diff,

            # Step 9 — sensitivity
            "sens":           sens,
            "always_replace": always_replace,

            # Step 10 — decision
            "replace":        replace,
            "confidence":     confidence,
            "evidence_score": evidence_score,
            "verdict":        ("REPLACE" if replace else "NO REPLACE"),
        }

        log.info("Done — verdict=%s diff=%s confidence=%s", result["verdict"], diff, confidence)
        return jsonify(result)

    except Exception as e:
        log.exception("Analysis failed")
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTE: /preview
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/preview", methods=["POST"])
def preview():
    """Return first 15 rows + smart SP suggestion for the preview panel."""
    try:
        csv_text = request.files["file"].read().decode("utf-8")
        df       = pd.read_csv(io.StringIO(csv_text))
        df.columns = [c.strip() for c in df.columns]

        sp_cols_raw = [c for c in df.columns
                       if "sp" in c.lower()
                       and c.strip().lower() not in {"sales", "month"}]
        sp_clean    = [c.replace("sale ", "").strip() for c in sp_cols_raw]

        last       = df.iloc[-1]
        active_sps = [c.replace("sale ", "").strip()
                      for c in sp_cols_raw if float(last.get(c, 0) or 0) > 0]

        # Per-SP stats for smart suggestion
        sp_stats = []
        for raw, clean in zip(sp_cols_raw, sp_clean):
            vals   = pd.to_numeric(df[raw], errors="coerce").fillna(0)
            active = vals[vals > 0]
            sp_stats.append({
                "sp":     clean,
                "avg":    round(float(active.mean()), 2) if len(active) > 0 else 0,
                "months": int(len(active)),
                "active": float(last.get(raw, 0) or 0) > 0,
            })

        # Suggest weakest active SP as most likely resign candidate
        active_stats      = [s for s in sp_stats if s["active"]]
        suggested_resigned = (min(active_stats, key=lambda s: s["avg"])["sp"]
                              if active_stats else (sp_clean[-1] if sp_clean else ""))

        return jsonify({
            "rows":               len(df),
            "cols":               list(df.columns),
            "sp_cols":            sp_clean,
            "active_sps":         active_sps,
            "sp_stats":           sp_stats,
            "suggested_resigned": suggested_resigned,
            "preview":            df.head(15).fillna("").to_dict("records"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
