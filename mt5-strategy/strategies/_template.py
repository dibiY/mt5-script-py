"""
TEMPLATE dyal strategy jdida
-----------------------------
1. Copie had fichier f nfs dossier (strategies/) w smmih b smiya bla "_" f lwl,
   ex: strategies/breakout_h1.py
2. Kteb logic dyalk f fonction run(cfg).
3. Lanci run.bat -> strategy jdida ghadi tban f menu automatiquement.

Les fichiers li kaybdaw b "_" (b7al hada) ma kaybanouch f menu.

cfg fih:
    cfg["NAME"]    -> smiya dyal compte (ex: demo)
    cfg["PAIRS"]   -> liste dyal paires (ex: ["EURUSD", "GBPUSD"])
    cfg["MT5_SERVER"], cfg["MT5_LOGIN"] ...
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5  # noqa: E402
from core import load_account, connect, shutdown, list_all_symbols, resolve_symbol, get_rates  # noqa: E402


def run(cfg):
    all_names = set(list_all_symbols(verbose=False)["symbol"])

    for base in cfg["PAIRS"]:
        sym = resolve_symbol(base, all_names)
        if not sym:
            print(f"[!] {base} ma kaynch")
            continue

        df = get_rates(sym, mt5.TIMEFRAME_H1, 200)
        if df is None:
            continue

        # ===== Kteb strategy dyalk hna =====
        print(f"{sym}: close = {df['close'].iloc[-1]}")


if __name__ == "__main__":
    cfg = load_account()
    connect(cfg)
    try:
        run(cfg)
    finally:
        shutdown()
