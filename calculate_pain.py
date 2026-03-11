import os
import json
import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone

# --- Singapore Timezone ---
SGT = timezone(timedelta(hours=8))


def calculate_max_pain(ticker_obj, expiry_date):
    """Calculates Max Pain strike and total Open Interest with retries."""
    for attempt in range(3):
        try:
            chain = ticker_obj.option_chain(expiry_date)
            total_call_oi = int(chain.calls['openInterest'].sum())
            total_put_oi  = int(chain.puts['openInterest'].sum())
            total_oi      = total_call_oi + total_put_oi

            if total_oi == 0 and attempt < 2:
                time.sleep(2)
                continue

            calls = chain.calls[chain.calls['openInterest'] >= 10][['strike', 'openInterest']].fillna(0)
            puts  = chain.puts[chain.puts['openInterest']  >= 10][['strike', 'openInterest']].fillna(0)

            strikes = sorted(set(calls['strike']).union(set(puts['strike'])))
            if not strikes:
                return None, total_call_oi, total_put_oi

            pain_results = []
            for s in strikes:
                cl = calls[calls['strike'] < s].apply(lambda x: (s - x['strike']) * x['openInterest'], axis=1).sum()
                pl = puts[puts['strike']  > s].apply(lambda x: (x['strike'] - s) * x['openInterest'], axis=1).sum()
                pain_results.append({'strike': s, 'total': cl + pl})

            max_p = float(pd.DataFrame(pain_results).sort_values('total').iloc[0]['strike'])
            return max_p, total_call_oi, total_put_oi

        except Exception as e:
            if attempt < 2:
                time.sleep(2)

    return None, 0, 0


def safe_json_load(path, default):
    """Reads a JSON file safely — returns default if missing or empty/corrupt."""
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            content = f.read().strip()
            return json.loads(content) if content else default
    except (json.JSONDecodeError, ValueError):
        print(f"  ⚠️  Could not parse {path}, starting fresh")
        return default


def update_expiry_history(ticker_sym, chain_data):
    """Maintains a rolling 10-day history for every expiry."""
    path      = f'data/{ticker_sym}/expiry_history.json'
    history   = safe_json_load(path, {})
    today_sgt = datetime.now(SGT).strftime("%Y-%m-%d")

    for entry in chain_data:
        exp = entry['date']
        if exp not in history:
            history[exp] = []

        if not history[exp] or history[exp][-1]['trade_date'] != today_sgt:
            history[exp].append({
                "trade_date": today_sgt,
                "max_pain":   entry['max_pain'],
                "call_oi":    entry['call_oi'],
                "put_oi":     entry['put_oi']
            })
        history[exp] = history[exp][-10:]

    # Clean up expiry keys older than 180 days
    cutoff  = (datetime.now(SGT) - timedelta(days=180)).strftime("%Y-%m-%d")
    history = {k: v for k, v in history.items() if k >= cutoff}

    with open(path, 'w') as f:
        json.dump(history, f, indent=4)


def update_spot_log(ticker_sym, spot):
    """Appends today's spot price to the rolling 60-day log."""
    log_path = f'data/{ticker_sym}/history_log.json'
    log      = safe_json_load(log_path, [])
    today    = datetime.now(SGT).strftime("%Y-%m-%d")

    if log and log[-1]['date'] == today:
        log[-1]['spot'] = round(spot, 2)
    else:
        log.append({"date": today, "spot": round(spot, 2)})

    with open(log_path, 'w') as f:
        json.dump(log[-60:], f, indent=4)


def process_ticker(ticker_sym):
    """Runs the full update pipeline for a single ticker."""
    print(f"\n{'=' * 60}")
    print(f"  {ticker_sym}  |  {datetime.now(SGT).strftime('%Y-%m-%d %H:%M SGT')}")
    print(f"{'=' * 60}")

    ticker = yf.Ticker(ticker_sym)

    # --- Spot price ---
    try:
        spot = float(ticker.history(period="1d")['Close'].iloc[-1])
        print(f"  Spot: ${spot:.2f}")
    except Exception as e:
        print(f"  ⚠️  Could not fetch spot price: {e}")
        spot = 0.0

    # --- Options expiries within 180 days ---
    cutoff     = (datetime.now(SGT) + timedelta(days=180)).strftime("%Y-%m-%d")
    try:
        all_expiries = [e for e in ticker.options if e <= cutoff]
    except Exception as e:
        print(f"  ⚠️  Could not fetch options chain: {e}")
        return

    print(f"  Fetching {len(all_expiries)} expiries...\n")

    chain_data = []
    for i, exp in enumerate(all_expiries, 1):
        print(f"  [{i}/{len(all_expiries)}] {exp}...", end=" ")
        m_pain, call_oi, put_oi = calculate_max_pain(ticker, exp)

        if m_pain:
            chain_data.append({
                "date":       exp,
                "max_pain":   round(m_pain, 2),
                "call_oi":    call_oi,
                "put_oi":     put_oi,
                "pc_ratio":   round(put_oi / call_oi, 4) if call_oi > 0 else None,
                "is_monthly": (15 <= int(exp.split('-')[2]) <= 21)
            })
            print(f"✓ Pain: ${m_pain:.2f}  |  C/P: {call_oi}/{put_oi}")
        else:
            total_oi = call_oi + put_oi
            if total_oi > 0:
                print(f"⚠️  OI ({total_oi}) but no calculable pain")
            else:
                print(f"✗ Zero OI")

        time.sleep(0.3)

    # --- Write data/{TICKER}/ files ---
    os.makedirs(f'data/{ticker_sym}', exist_ok=True)

    payload = {
        "last_update": datetime.now(SGT).strftime("%Y-%m-%d %H:%M"),
        "spot":        round(spot, 2),
        "data":        chain_data
    }
    with open(f'data/{ticker_sym}/history.json', 'w') as f:
        json.dump(payload, f, indent=4)

    update_expiry_history(ticker_sym, chain_data)
    update_spot_log(ticker_sym, spot)

    print(f"\n  ✓ Done — {len(chain_data)} expiries saved")


def run_all():
    """Loads tickers.json and processes every active ticker."""
    with open('tickers.json') as f:
        tickers = json.load(f)

    active = [t for t in tickers if t.get('active', True)]
    print(f"\n{'#' * 60}")
    print(f"  Stock Max Pain Monitor  |  {len(active)} active tickers")
    print(f"  {datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')}")
    print(f"{'#' * 60}")

    for entry in active:
        try:
            process_ticker(entry['ticker'])
        except Exception as e:
            print(f"\n  ❌ Fatal error on {entry['ticker']}: {e}")

    print(f"\n{'#' * 60}")
    print(f"  All tickers processed.")
    print(f"{'#' * 60}\n")


if __name__ == "__main__":
    run_all()
