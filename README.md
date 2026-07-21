# Screening Forex

Screening otomatis pair forex (H1) dengan strategi **session breakout** + filter trend H4. Lanjutan dari pendekatan repo screening-Saham-IDX, disesuaikan untuk pasar forex (tanpa filter volume, TP/SL berbasis ATR).

## Cara kerja

Dua run per hari trading (Senin–Jumat) via GitHub Actions:

| Run | Jadwal (WIB) | Range acuan | Breakout sesi |
|---|---|---|---|
| London | 15:15 | Asia (07:00–14:00 WIB) | London |
| New York | 20:15 | London (14:00–19:00 WIB) | New York |

Logika per pair:
1. Trend H4: close terakhir vs EMA50 → hanya BUY saat uptrend, SELL saat downtrend.
2. Breakout: harga menembus high/low range sesi acuan + buffer 0.1×ATR.
3. Level: SL = 1.5×ATR(14) H1, TP1 = 2×ATR, TP2 = 3×ATR.
4. Status `SIGNAL` = sudah breakout; `WATCH` = level pending searah trend.

Hasil ditulis ke `signals.json` dan di-commit otomatis, siap dibaca dashboard GitHub Pages.

## Pair

EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD, USDCHF, XAUUSD (proxy GC=F).

## Setup

1. Buat repo baru, push semua file ini.
2. Settings → Actions → General → Workflow permissions → **Read and write permissions**.
3. Uji manual: tab Actions → Screening Forex → Run workflow (pilih mode).

## Uji lokal

```
pip install -r requirements.txt
python screener.py london   # atau: ny
python test_logic.py        # uji logika tanpa jaringan
```

> Alat bantu screening pribadi — bukan saran finansial.
