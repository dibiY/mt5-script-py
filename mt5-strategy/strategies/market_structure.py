"""
Strategy: Market Structure M5
------------------------------
Kat analyser structure dyal les paires (UP / DOWN / RANGE)
b swing highs/lows (HH, HL, LH, LL) + confirmation EMA 20/50 + BOS.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5  # noqa: E402
from core import load_account, connect, shutdown, list_all_symbols, resolve_symbol, get_rates  # noqa: E402

# ===== Paramètres dyal strategy =====
TIMEFRAME = mt5.TIMEFRAME_M5
BARS = 300
SWING_LOOKBACK = 3
EMA_FAST = 20
EMA_SLOW = 50


def find_swings(df, lookback=SWING_LOOKBACK):
    highs, lows = [], []
    h, l = df["high"].values, df["low"].values
    for i in range(lookback, len(df) - lookback):
        if h[i] == h[i - lookback:i + lookback + 1].max():
            highs.append(h[i])
        if l[i] == l[i - lookback:i + lookback + 1].min():
            lows.append(l[i])
    return highs, lows


def analyze_structure(df):
    highs, lows = find_swings(df)
    if len(highs) < 2 or len(lows) < 2:
        return {"structure": "UNKNOWN", "reason": "swings ma kafyinch"}

    ph, lh = highs[-2], highs[-1]
    pl, ll = lows[-2], lows[-1]
    hh, hl = lh > ph, ll > pl

    if hh and hl:
        structure = "UP"
    elif lh < ph and ll < pl:
        structure = "DOWN"
    else:
        structure = "RANGE"

    last_close = df["close"].iloc[-1]
    bos = None
    if last_close > lh:
        bos = "BOS haut (close fo9 l2akhir swing high)"
    elif last_close < ll:
        bos = "BOS bas (close ta7t l2akhir swing low)"

    ema_fast = df["close"].ewm(span=EMA_FAST, adjust=False).mean().iloc[-1]
    ema_slow = df["close"].ewm(span=EMA_SLOW, adjust=False).mean().iloc[-1]
    ema_bias = "UP" if ema_fast > ema_slow else "DOWN"

    return {
        "structure": structure,
        "pattern": f"{'HH' if hh else 'LH'} + {'HL' if hl else 'LL'}",
        "last_high": lh, "prev_high": ph,
        "last_low": ll, "prev_low": pl,
        "close": last_close,
        "bos": bos,
        "ema_bias": ema_bias,
        "confirmed": structure == ema_bias,
    }


def print_report(symbol, df, r):
    print("\n" + "-" * 60)
    print(f"{symbol}  |  M5  |  dernière bougie: {df['time'].iloc[-1]}")
    if r["structure"] == "UNKNOWN":
        print(f"  Structure: UNKNOWN ({r['reason']})")
        return
    arrow = {"UP": "▲", "DOWN": "▼", "RANGE": "↔"}[r["structure"]]
    print(f"  Structure : {arrow} {r['structure']}  ({r['pattern']})")
    print(f"  Highs     : prev {r['prev_high']}  ->  last {r['last_high']}")
    print(f"  Lows      : prev {r['prev_low']}  ->  last {r['last_low']}")
    print(f"  Close     : {r['close']}")
    print(f"  EMA {EMA_FAST}/{EMA_SLOW}: {r['ema_bias']}  ->  {'confirmé ✔' if r['confirmed'] else 'pas confirmé'}")
    if r["bos"]:
        print(f"  {r['bos']}")


def run(cfg):
    symbols_df = list_all_symbols()
    all_names = set(symbols_df["symbol"])

    print(f"\nAnalyse M5 — {datetime.now():%Y-%m-%d %H:%M}")
    for base in cfg["PAIRS"]:
        sym = resolve_symbol(base, all_names)
        if not sym:
            print(f"\n[!] {base} ma kaynch f had compte")
            continue
        df = get_rates(sym, TIMEFRAME, BARS)
        if df is not None:
            print_report(sym, df, analyze_structure(df))
    print("\n" + "=" * 60)


if __name__ == "__main__":
    cfg = load_account()
    connect(cfg)
    try:
        run(cfg)
    finally:
        shutdown()
