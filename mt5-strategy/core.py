"""
core.py — Outils mchtarkin bin ga3 les strategies
--------------------------------------------------
- Kay9ra compte li tkhtar (accounts/<smiya>.env)
- Connexion / déconnexion MT5
- Symboles + data (bougies)

Strategy jdida ma khasshach t3awed had lcode, ghir:
    from core import load_account, connect, shutdown, get_rates, ...
"""

import os
import pandas as pd
import MetaTrader5 as mt5
from dotenv import dotenv_values

ROOT = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_DIR = os.path.join(ROOT, "accounts")
DEFAULT_PAIRS = "EURUSD,GBPUSD,USDJPY"


# ============================================================
# COMPTE
# ============================================================
def load_account():
    """Kay9ra compte mn MT5_ACCOUNT_FILE (li kay3tih setup.sh).
    Ila ma kanch, kayakhod awel compte f dossier accounts/."""
    path = os.getenv("MT5_ACCOUNT_FILE", "")

    if not path:
        files = []
        if os.path.isdir(ACCOUNTS_DIR):
            files = sorted(f for f in os.listdir(ACCOUNTS_DIR) if f.endswith(".env"))
        if not files:
            raise SystemExit("[X] Ma kayn 7ta compte. Lanci run.bat (wla setup.sh) bach tzid wa7d.")
        path = os.path.join(ACCOUNTS_DIR, files[0])
    elif not os.path.isabs(path):
        path = os.path.join(ROOT, path)

    if not os.path.isfile(path):
        raise SystemExit(f"[X] Fichier dyal compte ma kaynch: {path}")

    cfg = {k: (v or "") for k, v in dotenv_values(path).items()}
    cfg["NAME"] = os.path.splitext(os.path.basename(path))[0]
    pairs = cfg.get("FOREX_PAIRS") or DEFAULT_PAIRS
    cfg["PAIRS"] = [p.strip().upper() for p in pairs.split(",") if p.strip()]
    return cfg


# ============================================================
# CONNEXION
# ============================================================
def connect(cfg):
    login = cfg.get("MT5_LOGIN", "").strip()
    if not login.isdigit():
        raise SystemExit(f"[X] MT5_LOGIN ghalat f compte '{cfg['NAME']}'.")

    kwargs = dict(
        login=int(login),
        password=cfg.get("MT5_PASSWORD", ""),
        server=cfg.get("MT5_SERVER", ""),
    )
    if cfg.get("MT5_PATH"):
        kwargs["path"] = cfg["MT5_PATH"]

    if not mt5.initialize(**kwargs):
        raise SystemExit(f"[X] Connexion fachlat ({cfg['NAME']}): {mt5.last_error()}")

    info = mt5.account_info()
    if info is None:
        mt5.shutdown()
        raise SystemExit(f"[X] Ma9dertch n9ra account info: {mt5.last_error()}")

    print("=" * 60)
    print(f"[OK] Compte '{cfg['NAME']}' connecté: {info.login} | {info.server} | {info.company}")
    print(f"     Balance: {info.balance} {info.currency} | Equity: {info.equity} | Leverage: 1:{info.leverage}")
    print("=" * 60)
    return info


def shutdown():
    mt5.shutdown()


# ============================================================
# SYMBOLES
# ============================================================
def list_all_symbols(verbose=True):
    symbols = mt5.symbols_get()
    if symbols is None:
        print(f"[!] symbols_get fachal: {mt5.last_error()}")
        return pd.DataFrame(columns=["symbol", "path", "category"])

    df = pd.DataFrame([{
        "symbol": s.name,
        "path": s.path,
        "description": s.description,
        "visible": s.visible,
        "digits": s.digits,
        "spread": s.spread,
    } for s in symbols])
    df["category"] = df["path"].str.split("\\").str[0]

    if verbose:
        print(f"\nGa3 les marchés f compte: {len(df)} symboles")
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
def get_rates(symbol, timeframe=mt5.TIMEFRAME_M5, count=300):
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
