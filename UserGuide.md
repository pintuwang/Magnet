# 📈 Stock Options Max Pain Tracker — User Guide

This guide explains how to manage your ticker watchlist and interpret the three charts in the dashboard. The tracker runs automatically twice a day on a GitHub Actions schedule, requiring no manual intervention once set up.

---

## 🕐 Update Schedule (SGT)

| Run | UTC | SGT | Purpose |
|:----|:----|:----|:--------|
| Intraday | 1 PM | 9 PM | Mid-session options snapshot |
| Post-close | 10 PM | 6 AM (next day) | Final daily close snapshot |

Updates run **Monday to Friday** only, matching US market days. You can also trigger a manual run anytime from the GitHub Actions tab.

---

## 📋 Managing Your Ticker Watchlist

All ticker management is done by editing a single file: **`tickers.json`** in the root of the repository. The Python script and the UI both read from this file — it is the single source of truth. **You never need to manually create any data folders or seed files** — the script handles that automatically.

### File Location
```
/tickers.json
```

### File Format
```json
[
  { "ticker": "AEHR", "added": "2026-03-11", "active": true },
  { "ticker": "SLDP", "added": "2026-03-11", "active": true }
]
```

| Field | Required | Description |
|:------|:---------|:------------|
| `ticker` | ✅ | Yahoo Finance ticker symbol (uppercase) |
| `added` | ✅ | Date you added it — used to show "Tracking Since" in the UI |
| `active` | ✅ | `true` to track, `false` to soft-remove (see below) |

---

## ➕ Adding a New Ticker

1. Open `tickers.json` in the GitHub editor (click the file → pencil icon)
2. Add a new entry to the array:

```json
{ "ticker": "NVDA", "added": "2026-03-12", "active": true }
```

3. Commit the change to `main`
4. Either wait for the next scheduled run, or trigger a manual run from the **GitHub Actions** tab

That's all. On the next run, the script will automatically:
- Create the `data/NVDA/` folder
- Seed the three JSON files inside it
- Fetch the current options chain and spot price
- Populate Chart 1 immediately

> ⚠️ **What to expect when a ticker is first added:**
> - **Chart 1 (Max Pain Snapshot)** — Fully populated immediately ✅
> - **Chart 2 (Evolution Tracker)** — Sparse at first, fills in over 1–2 weeks of daily snapshots 🟡
> - **Chart 3 (Expiry Accuracy + Put/Call Ratio)** — Empty until the first tracked expiry passes ❌
>
> Chart 3 cannot be backfilled — it only captures data from the day you start tracking. The longer you run it, the more valuable it becomes.

---

## ➖ Soft Removing a Ticker

Soft remove keeps all historical data intact but stops the script from updating the ticker and hides it in the UI. This is the **recommended approach** — data is preserved and the ticker can be reactivated at any time.

1. Open `tickers.json`
2. Set `"active": false` for the ticker you want to remove:

```json
{ "ticker": "SLDP", "added": "2026-03-11", "active": false }
```

3. Commit the change

From the next run onwards, SLDP will be skipped by the script and hidden in the UI. Its folder `data/SLDP/` remains untouched on GitHub.

---

## 🗑️ Hard Removing a Ticker (Permanent)

Only do this if you are certain you no longer need the history.

1. Delete the ticker's entry from `tickers.json`
2. Delete the `data/TICKER/` folder from the repository
3. Commit both changes

> ⚠️ This is irreversible unless you dig through Git commit history.

---

## 🔄 Reactivating a Soft-Removed Ticker

1. Set `"active": true` in `tickers.json`
2. Commit the change

The script resumes on the next run. All previously stored data is still there and the charts continue from where they left off, with a visible gap in Charts 2 and 3 for the inactive period.

---

## 📊 Understanding the Three Charts

Each ticker has its own view with the same three-chart layout.

---

### Chart 1 — Max Pain Snapshot (Current)

**What it shows:** The current max pain strike price and open interest (calls vs puts) for every upcoming expiry within the next 180 days.

| Element | Description |
|:--------|:------------|
| 🟢 Green Line | Max Pain strike — the price where the most options expire worthless. Market makers tend to "pin" toward this level |
| 🟩 Green Bars | Total call open interest at each expiry. Acts as a resistance ceiling |
| 🟥 Orange Bars | Total put open interest at each expiry. Acts as a support floor |
| ● Yellow Dot | Monthly expiry (3rd Friday) — highest liquidity, strongest pinning effect |

**How to read it:** When spot price is significantly above or below the max pain line, expect a gravitational pull back toward max pain as expiry approaches. The bigger the OI bars, the stronger the magnetic effect.

---

### Chart 2 — Max Pain Evolution Tracker

**What it shows:** How the max pain strike for each expiry has shifted day by day over the past 10 snapshots. Grouped by expiry date, with dividers between groups.

| Element | Description |
|:--------|:------------|
| 🟢 Line | Daily max pain value for that expiry |
| 🟩/🟥 Bars | Call and put OI on each snapshot day |
| White background zone | Future expiry (not yet passed) |

**How to read it:** A max pain line steadily drifting upward suggests institutional positioning is turning bullish for that expiry. A sudden jump or drop often signals large new positions being opened. This chart starts thin on day one and becomes more useful after 1–2 weeks of data.

---

### Chart 3 — Expiry Accuracy + Put/Call Ratio

**What it shows:** For every expiry that has already passed while the tracker was running — how close was the final max pain prediction to the actual closing price? The put/call ratio bars give context on market positioning at the time.

| Element | Description |
|:--------|:------------|
| ⭐ Yellow Stars | Actual closing spot price on or after expiry day |
| 🟢 Green Line | Final max pain prediction recorded before expiry |
| 📊 Yellow Bars | Put/Call OI ratio at the time of expiry (right axis) |

**Put/Call Ratio interpretation:**

| Ratio | Meaning |
|:------|:--------|
| > 1.0 | More puts than calls — bearish positioning or heavy downside hedging |
| < 1.0 | More calls than puts — bullish sentiment or low hedging demand |
| ~ 1.0 | Balanced positioning — max pain pinning effect is likely strongest |

**How to read it:** The closer the yellow stars are to the green line across multiple expiries, the more reliable max pain is as a predictor for that ticker. Some stocks pin tightly to max pain; others do not — Chart 3 tells you which category your ticker falls into over time.

> 📅 This chart is **empty when a ticker is first added**. It populates automatically after the first tracked expiry passes. There is no way to backfill historical data.

---

## 📁 Data Folder Structure

For reference — you never need to touch these files manually. The script manages them entirely.

```
data/
  AEHR/
    history.json          ← Current max pain snapshot (feeds Chart 1)
    expiry_history.json   ← Rolling 10-day evolution per expiry (feeds Chart 2)
    history_log.json      ← Daily spot price log (feeds Chart 3)
  SLDP/
    history.json
    expiry_history.json
    history_log.json
tickers.json              ← Master watchlist — the only file you edit
```

---

## 🔧 Troubleshooting

| Issue | Likely Cause | Fix |
|:------|:-------------|:----|
| New ticker not appearing in UI | Run hasn't happened yet after editing `tickers.json` | Trigger a manual run from the Actions tab |
| Chart 1 empty for a ticker | Ticker has no listed options or very low OI | Verify on any options chain site; remove if no options exist |
| Chart 2 looks thin / only 1 bar | Ticker was recently added | Normal — fills in over 1–2 weeks of twice-daily snapshots |
| Chart 3 is empty | No expiries have passed yet since tracking started | Normal — wait for the first expiry date to pass |
| Charts were working, now blank | JSON file may have been corrupted | Check the Actions log for errors; trigger a manual re-run |
| GitHub Action failed | API timeout or yfinance rate limit | Re-run manually from the Actions tab — usually self-resolving |
| Ticker shows stale "Last Sync" time | Action ran but data didn't change | Normal if market was closed; check Actions tab to confirm run succeeded |

---

*This tracker is for informational and research purposes only. It does not constitute financial advice.*
