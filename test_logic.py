"""Uji logika analyze() dengan data sintetis (tanpa jaringan)."""
import numpy as np
import pandas as pd
import screener

def fake_h1(trend_up=True, breakout=True):
    # 90 hari x 24 jam H1, uptrend/downtrend + breakout hari terakhir
    n = 90 * 24
    idx = pd.date_range(end=pd.Timestamp.now(tz="UTC").floor("h"), periods=n, freq="1h")
    drift = 0.00002 if trend_up else -0.00002
    close = 1.10 + np.cumsum(np.random.normal(drift, 0.0004, n))
    df = pd.DataFrame(index=idx)
    df["Close"] = close
    df["Open"] = df["Close"].shift().fillna(close[0])
    df["High"] = df[["Open","Close"]].max(axis=1) + 0.0005
    df["Low"]  = df[["Open","Close"]].min(axis=1) - 0.0005
    if breakout:
        today = idx[-1].date()
        mask = (pd.Series(idx.date, index=idx) == today) & (idx.hour < 7)
        hi = df.loc[mask.values, "High"].max()
        lo = df.loc[mask.values, "Low"].min()
        jump = (hi + 0.003) if trend_up else (lo - 0.003)
        df.iloc[-1, df.columns.get_loc("Close")] = jump
        df.iloc[-1, df.columns.get_loc("High" if trend_up else "Low")] = jump
    df["Volume"] = 0
    return df

np.random.seed(42)
for trend_up, breakout in [(True, True), (True, False), (False, True)]:
    screener.yf.download = lambda *a, **k: fake_h1(trend_up, breakout)
    r = screener.analyze("EURUSD", "EURUSD=X", "london")
    print(f"trend_up={trend_up} breakout={breakout} -> {r['status']:6s} {r['direction']:4s} "
          f"entry={r['entry']} sl={r['sl']} tp1={r['tp1']} tp2={r['tp2']} sl_pips={r['sl_pips']}")
