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

All ticker management is done by editing a single file: **`tickers.json`** in the root of the repository. The Python script and the UI both read from this file — it is the single source of truth.

### File Location
```
/tickers.json
```

### File Format
```json
[
  { "ticker": "AAPL", "added": "2026-01-01", "active": true },
  { "ticker": "NVDA", "added": "2026-01-01", "active": true },
  { "ticker": "TSLA", "added": "2026-01-01", "active": true }
]
```

| Field | Required | Description |
|:------|:---------|:------------|
| `ticker` | ✅ | Yahoo Finance ticker symbol (uppercase) |
| `added` | ✅ | Date you added it — used to show "Tracking Since" in the UI |
| `active` | ✅ | `true` to track, `false` to soft-remove (see below) |

---

## ➕ Adding a New Ticker

1. Open `tickers.json` in the GitHub editor (or locally)
2. Add a new entry to the array:

```json
{ "ticker": "META", "added": "2026-03-11", "active": true }
```

3. Commit the change to `main`
4. Either wait for the next scheduled run, or trigger a manual run from the **GitHub Actions** tab

On the next run, the script will:
- Create a `data/META/` folder automatically
- Fetch the current options chain and spot price
- Start building all three charts from that day forward

> ⚠️ **What to expect when a ticker is first added:**
> - **Chart 1 (Max Pain Snapshot)** — Fully populated immediately ✅
> - **Chart 2 (Evolution Tracker)** — Sparse at first, fills in over 1–2 weeks of daily snapshots 🟡
> - **Chart 3 (Expiry Accuracy + Put/Call Ratio)** — Empty until the first tracked expiry passes ❌
>
> Chart 3 cannot be backfilled. It rewards consistent tracking — the longer you run it, the more valuable it becomes.

---

## ➖ Soft Removing a Ticker

Soft remove keeps all historical data intact but stops the script from updating the ticker and hides it in the UI. This is the **recommended approach** — data is preserved and the ticker can be reactivated at any time.

1. Open `tickers.json`
2. Set `"active": false` for the ticker you want to remove:

```json
{ "ticker": "TSLA", "added": "2026-01-01", "active": false }
```

3. Commit the change

From the next run onwards, TSLA will be skipped by the script and hidden in the UI. Its folder `data/TSLA/` remains untouched on GitHub.

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

The script resumes on the next run. All previously stored data is still there and the charts will continue from where they left off, with a visible gap in Chart 2 and Chart 3 for the period it was inactive.

---

## 📊 Understanding the Three Charts

Each ticker has its own dedicated page with the same three-chart layout.

---

### Chart 1 — Max Pain Snapshot (Current)

**What it shows:** The current max pain strike price and open interest (calls vs puts) for every upcoming expiry within the next 180 days.

| Element | Description |
|:--------|:------------|
| 🟢 Green Line | Max Pain strike — the price where the most options expire worthless. Market makers tend to "pin" toward this level |
| 🟩 Green Bars (Calls) | Total call open interest at each expiry. Acts as a resistance ceiling |
| 🟥 Red Bars (Puts) | Total put open interest at each expiry. Acts as a support floor |
| ◆ Diamond Markers | Monthly expirations (3rd Friday) — highest liquidity, strongest pinning effect |

**How to read it:** When spot price is significantly above or below the max pain line, expect a gravitational pull back toward max pain as expiry approaches.

---

### Chart 2 — Max Pain Evolution Tracker (Historical)

**What it shows:** How the max pain strike for each upcoming expiry has *shifted* day by day over the past 10 snapshots. Grouped by expiry, with yellow dividers between groups.

| Element | Description |
|:--------|:------------|
| 🟢 Line | Daily max pain value for that expiry |
| 🟩/🟥 Bars | Call and put OI on that snapshot day |
| White background | Future expiry (not yet passed) |

**How to read it:** A max pain line that is steadily drifting upward suggests institutional positioning is turning bullish for that expiry. A sudden jump or drop often signals large new positions being opened.

---

### Chart 3 — Expiry Accuracy + Put/Call Ratio

**What it shows:** For every expiry that has already passed while the tracker was running — how close was the final max pain prediction to the actual closing price? Also displays the put/call OI ratio at the time of expiry.

| Element | Description |
|:--------|:------------|
| ⭐ Star (Yellow) | Actual closing spot price on expiry day |
| 🟢 Line | Final max pain prediction before expiry |
| 📊 Bars | Put/Call ratio at expiry (to be implemented) |

**Put/Call Ratio interpretation:**
- **Ratio > 1.0** — More puts than calls. Bearish positioning or heavy downside hedging
- **Ratio < 1.0** — More calls than puts. Bullish sentiment or low hedging demand
- **Ratio near 1.0** — Balanced positioning, max pain pinning effect likely strongest

**How to read it:** The closer the star is to the green line across multiple expiries, the more reliable max pain is as a predictor for that particular ticker. Some stocks pin tightly, others do not — this chart tells you which category your ticker falls into.

> 📅 This chart is **empty when a ticker is first added**. It will populate automatically as expiries pass.

---

## 📁 Data Folder Structure

For reference, each ticker stores three JSON files:

```
data/
  AAPL/
    history.json          ← Current max pain snapshot (Chart 1)
    expiry_history.json   ← Rolling 10-day evolution per expiry (Chart 2)
    history_log.json      ← Daily spot price log (Chart 3)
  NVDA/
    history.json
    expiry_history.json
    history_log.json
  tickers.json            ← Master watchlist (you edit this)
```

You do not need to manually edit any files inside the ticker data folders — the script manages them automatically.

---

## 🔧 Troubleshooting

| Issue | Likely Cause | Fix |
|:------|:-------------|:----|
| New ticker not appearing in UI | `active` not set to `true`, or run hasn't happened yet | Check `tickers.json`, trigger manual run |
| Chart 1 shows no data for a ticker | Ticker has no listed options (e.g. too small a stock) | Remove from watchlist |
| Chart 2 looks thin | Ticker was recently added | Normal — fills in over 1–2 weeks |
| Chart 3 is empty | No expiries have passed yet since tracking started | Normal — wait for first expiry to pass |
| GitHub Action failed | API timeout or yfinance issue | Re-run manually from Actions tab; usually self-resolving |

---

*This tracker is for informational and research purposes only. It does not constitute financial advice.*
