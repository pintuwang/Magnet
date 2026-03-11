# ⬡ Stock Max Pain Monitor

A GitHub-hosted options max pain tracker for a custom watchlist of stocks. Runs automatically twice daily via GitHub Actions and visualises three charts per ticker: current max pain snapshot, historical evolution, and expiry accuracy with put/call ratio.

## How it works

1. GitHub Actions runs `calculate_pain.py` twice a day (9 PM SGT and 6 AM SGT)
2. The script reads `tickers.json`, processes each active ticker, and saves JSON data under `data/{TICKER}/`
3. `index.html` reads those JSON files and renders the dashboard — no backend required

## Setup

1. Fork or clone this repository
2. Enable GitHub Actions (they are enabled by default on public repos)
3. Edit `tickers.json` to add your tickers
4. Enable GitHub Pages: **Settings → Pages → Source → Deploy from branch → main → / (root)**
5. Your dashboard will be live at `https://{your-username}.github.io/{repo-name}/`

## Managing tickers

Edit `tickers.json` in the GitHub editor. See `UserGuide.md` for full instructions on adding, soft-removing, and reactivating tickers.

## Data structure

```
data/
  {TICKER}/
    history.json          ← Current max pain snapshot (Chart 1)
    expiry_history.json   ← Rolling 10-day evolution per expiry (Chart 2)
    history_log.json      ← Daily spot price log (Chart 3)
tickers.json              ← Master watchlist
calculate_pain.py         ← Data collection script
index.html                ← Dashboard UI
```

## Schedule (SGT)

| Run | UTC | SGT |
|:----|:----|:----|
| Intraday | 1 PM | 9 PM |
| Post-close | 10 PM | 6 AM (next day) |

Monday – Friday only. Manual runs available from the GitHub Actions tab.

---
*For informational purposes only. Not financial advice.*
