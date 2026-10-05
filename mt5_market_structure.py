"""
MT5 Market Structure Analyzer
------------------------------
- Connexion l MT5 terminal (login / password / server)
- Liste dyal ga3 les symboles li f compte
- Kay9ra M5 dyal 3 paires forex
- Kay analyser structure: UP (HH + HL) / DOWN (LH + LL) / RANGE

Install:
    pip install MetaTrader5 pandas

Note: package MetaTrader5 khdam ghir 3la Windows (wla Wine), w terminal MT5 khaso ykon installé.
"""

import os
import getpass
from datetime import datetime

import MetaTrader5 as mt5
import pandas as pd

# ============================================================
# CONFIG
# ============================================================
# Credentials: ila khliti hadou khawyin, script ghadi ytlabhom mnk f terminal.
# T9der tani t7tehom f variables d'environnement: MT5_LOGIN, MT5_PASSWORD, MT5_SERVER
MT5_LOGIN = os.getenv("MT5_LOGIN", "")        # ex: "12345678"
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")      # ex: "ICMarketsSC-Demo"
MT5_PATH = os.getenv("MT5_PATH", "")          # optionnel: chemin dyal terminal64.exe

# 3 paires li bghiti t analyser (script kay9leb automatiquement 3la suffix dyal broker, ex: EURUSD.m)
FOREX_PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]

TIMEFRAME = mt5.TIMEFRAME_M5
BARS = 300            # ch7al mn bougie
SWING_LOOKBACK = 3    # bougies 3la kol jiha bach n3tabro swing high/low (fractal)
EMA_FAST = 20
EMA_SLOW = 50


# ============================================================
# CONNEXION
# ============================================================
def get_credentials():
    login = MT5_LOGIN or input("MT5 Login (numéro de compte): ").strip()
    password = MT5_PASSWORD or getpass.getpass("MT5 Password: ")
    server = MT5_SERVER or input("MT5 Server (ex: Broker-Demo): ").strip()
    return int(login), password, server


def connect():
    login, password, server = get_credentials()
    kwargs = dict(login=login, password=password, server=server)
    if MT5_PATH:
        kwargs["path"] = MT5_PATH

    if not mt5.initialize(**kwargs):
        raise SystemExit(f"[X] Connexion fachlat: {mt5.last_error()}")

    info = mt5.account_info()
    if info is None:
        mt5.shutdown()
        raise SystemExit(f"[X] Ma9dertch n9ra account info: {mt5.last_error()}")

    print("=" * 60)
    print(f"[OK] Connecté: {info.login} | {info.server} | {info.company}")
    print(f"     Balance: {info.balance} {info.currency} | Equity: {info.equity} | Leverage: 1:{info.leverage}")
    print("=" * 60)


# ============================================================
# SYMBOLES
# ============================================================
def list_all_symbols():
    symbols = mt5.symbols_get()
    if symbols is None:
        print(f"[!] symbols_get fachal: {mt5.last_error()}")
        return []

    rows = [{
        "symbol": s.name,
        "path": s.path,
        "description": s.description,
        "visible": s.visible,
        "digits": s.digits,
        "spread": s.spread,
    } for s in symbols]
    df = pd.DataFrame(rows)

    print(f"\nGa3 les marchés f compte: {len(df)} symboles")
    # Groupement b catégorie (awel jouz dyal path, ex: Forex\Majors -> Forex)
    df["category"] = df["path"].str.split("\\").str[0]
    print(df.groupby("category").size().to_string())
    return df


def resolve_symbol(base, all_names):
    """Kay9leb 3la smiya l7a9i9ia 3nd broker (EURUSD, EURUSD.m, EURUSDpro...)."""
    if base in all_names:
        return base
    candidates = [n for n in all_names if n.upper().startswith(base.upper())]
    return sorted(candidates, key=len)[0] if candidates else None


# ============================================================
# DATA
# ============================================================
def get_rates(symbol, timeframe=TIMEFRAME, count=BARS):
    if not mt5.symbol_select(symbol, True):
        print(f"[!] Ma9dertch nzid {symbol} l Market Watch")
        return None
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        print(f"[!] Ma kaynach data l {symbol}: {mt5.last_error()}")
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


# ============================================================
# MARKET STRUCTURE
# ============================================================
def find_swings(df, lookback=SWING_LOOKBACK):
    """Swing high = high akbar mn 'lookback' bougies 3la jouj jihat (ou l3aks l swing low).
    Bougies l2akhrin (li ma tsddouch) ma kay7sbouch, bach ma ykounch repaint."""
    highs, lows = [], []
    h, l = df["high"].values, df["low"].values
    for i in range(lookback, len(df) - lookback):
        window_h = h[i - lookback:i + lookback + 1]
        window_l = l[i - lookback:i + lookback + 1]
        if h[i] == window_h.max():
            highs.append((df["time"].iloc[i], h[i]))
        if l[i] == window_l.min():
            lows.append((df["time"].iloc[i], l[i]))
    return highs, lows


def analyze_structure(df):
    highs, lows = find_swings(df)
    if len(highs) < 2 or len(lows) < 2:
        return {"structure": "UNKNOWN", "reason": "swings ma kafyinch"}

    (_, ph), (_, lh) = highs[-2], highs[-1]   # previous high, last high
    (_, pl), (_, ll) = lows[-2], lows[-1]     # previous low, last low

    hh, hl = lh > ph, ll > pl
    lh_, ll_ = lh < ph, ll < pl

    if hh and hl:
        structure = "UP"
    elif lh_ and ll_:
        structure = "DOWN"
    else:
        structure = "RANGE"

    # Break of Structure: close l2akhir fat l2akhir swing
    last_close = df["close"].iloc[-1]
    bos = None
    if last_close > lh:
        bos = "BOS haut (close fo9 l2akhir swing high)"
    elif last_close < ll:
        bos = "BOS bas (close ta7t l2akhir swing low)"

    # Confirmation b EMA
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


# ============================================================
# MAIN
# ============================================================
def main():
    connect()
    try:
        symbols_df = list_all_symbols()
        all_names = set(symbols_df["symbol"]) if len(symbols_df) else set()

        print(f"\nAnalyse M5 — {datetime.now():%Y-%m-%d %H:%M}")
        for base in FOREX_PAIRS:
            sym = resolve_symbol(base, all_names)
            if not sym:
                print(f"\n[!] {base} ma kaynch f had compte")
                continue
            df = get_rates(sym)
            if df is None:
                continue
            print_report(sym, df, analyze_structure(df))
        print("\n" + "=" * 60)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
