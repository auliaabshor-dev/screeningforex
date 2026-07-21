"""
Screening Forex — Session Breakout (H1) + Trend Filter (H4)
Dijalankan via GitHub Actions 2x per hari trading:
  - mode "london" : breakout dari range sesi Asia  (00:00-06:59 UTC)
  - mode "ny"     : breakout dari range sesi London (07:00-11:59 UTC)
Output: signals.json (dibaca dashboard GitHub Pages)

CATATAN: alat bantu screening, bukan saran finansial.
"""

import json
import sys
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "NZDUSD": "NZDUSD=X",
    "USDCHF": "USDCHF=X",
    "XAUUSD": "GC=F",  # proxy emas (futures)
}

ATR_PERIOD = 14
EMA_TREND = 50          # EMA di H4
SL_ATR = 1.5
TP1_ATR = 2.0
TP2_ATR = 3.0
BUFFER_ATR = 0.10       # buffer breakout di atas/bawah range

SESSIONS = {
    "london": {"range_start": 0, "range_end": 7,  "label": "Asia range → London breakout"},
    "ny":     {"range_start": 7, "range_end": 12, "label": "London range → NY breakout"},
}


def pip_size(pair: str) -> float:
    if pair == "XAUUSD":
        return 0.1
    return 0.01 if "JPY" in pair else 0.0001


def digits(pair: str) -> int:
    if pair == "XAUUSD":
        return 2
    return 3 if "JPY" in pair else 5


def atr(df: pd.DataFrame, period: int) -> pd.Series:
    hl = df["High"] - df["Low"]
    hc = (df["High"] - df["Close"].shift()).abs()
    lc = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def analyze(pair: str, ticker: str, mode: str) -> dict | None:
    df = yf.download(ticker, period="90d", interval="1h",
                     progress=False, auto_adjust=False)
    if df.empty or len(df) < EMA_TREND * 4:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = df.index.tz_convert("UTC")

    # --- Trend H4: resample dari H1 ---
    h4 = df.resample("4h").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    ).dropna()
    ema = h4["Close"].ewm(span=EMA_TREND, adjust=False).mean()
    trend = "up" if h4["Close"].iloc[-1] > ema.iloc[-1] else "down"

    # --- ATR H1 ---
    df["ATR"] = atr(df, ATR_PERIOD)
    last = df.iloc[-1]
    cur_atr = float(last["ATR"])
    price = float(last["Close"])

    # --- Range sesi hari ini (UTC) ---
    ses = SESSIONS[mode]
    today = df.index[-1].date()
    day = df[df.index.date == today]
    rng = day[(day.index.hour >= ses["range_start"]) &
              (day.index.hour < ses["range_end"])]
    if len(rng) < 3:
        return None
    hi, lo = float(rng["High"].max()), float(rng["Low"].min())
    buf = BUFFER_ATR * cur_atr

    signal, entry = None, None
    if trend == "up" and price > hi + buf:
        signal, entry = "BUY", price
    elif trend == "down" and price < lo - buf:
        signal, entry = "SELL", price

    status = "SIGNAL" if signal else "WATCH"
    if not signal:
        # level pantau: rencana breakout searah trend
        signal = "BUY" if trend == "up" else "SELL"
        entry = (hi + buf) if trend == "up" else (lo - buf)

    sign = 1 if signal == "BUY" else -1
    sl = entry - sign * SL_ATR * cur_atr
    tp1 = entry + sign * TP1_ATR * cur_atr
    tp2 = entry + sign * TP2_ATR * cur_atr
    d = digits(pair)

    return {
        "pair": pair,
        "status": status,          # SIGNAL = sudah breakout, WATCH = pending
        "direction": signal,
        "trend_h4": trend,
        "session": ses["label"],
        "range_high": round(hi, d),
        "range_low": round(lo, d),
        "price": round(price, d),
        "entry": round(entry, d),
        "sl": round(sl, d),
        "tp1": round(tp1, d),
        "tp2": round(tp2, d),
        "atr_h1": round(cur_atr, d),
        "sl_pips": round(abs(entry - sl) / pip_size(pair), 1),
    }


def main() -> None:
    now = datetime.now(timezone.utc)
    if now.weekday() >= 5:
        print("Akhir pekan, pasar tutup — skip.")
        return

    mode = sys.argv[1] if len(sys.argv) > 1 else (
        "london" if now.hour < 11 else "ny")
    if mode not in SESSIONS:
        raise SystemExit(f"Mode tidak dikenal: {mode}")

    results = []
    for pair, ticker in PAIRS.items():
        try:
            r = analyze(pair, ticker, mode)
            if r:
                results.append(r)
                print(f"{pair}: {r['status']} {r['direction']} @ {r['entry']}")
        except Exception as e:  # satu pair gagal jangan matikan semua
            print(f"{pair}: error {e}")

    out = {
        "generated_at": now.isoformat(),
        "mode": mode,
        "disclaimer": "Alat bantu screening pribadi, bukan saran finansial.",
        "signals": results,
    }
    with open("signals.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Selesai: {len(results)} pair, mode {mode}.")


if __name__ == "__main__":
    main()
