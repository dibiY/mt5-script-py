#!/usr/bin/env bash
# ============================================================
#  MT5 Strategy Launcher
#
#  Menu (sahl):      bash setup.sh        (wla double-click 3la run.bat)
#  Direct (rapide):  bash setup.sh --account demo --strategy market_structure
#
#  Comptes    -> dossier accounts/   (fichier .env l kol compte)
#  Strategies -> dossier strategies/ (fichier .py l kol strategy)
# ============================================================

cd "$(dirname "$0")" || exit 1

VENV_DIR=".venv"
ACCOUNTS_DIR="accounts"
STRAT_DIR="strategies"
LAST_FILE=".last_choice"
ACCOUNT=""
STRATEGY=""

# --- Couleurs ---
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[1;34m'; C='\033[1;36m'; N='\033[0m'
ok()    { echo -e "${G}[OK]${N} $1"; }
info()  { echo -e "${B}[..]${N} $1"; }
warn()  { echo -e "${Y}[!]${N} $1"; }
pause() { read -rp "Clicker Entrée bach tkemmel..." _; }
fail()  { echo -e "${R}[X]${N} $1"; echo; pause; exit 1; }

# --- Arguments ---
ARG_ACCOUNT=""; ARG_STRATEGY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --account)  ARG_ACCOUNT="$2"; shift 2 ;;
    --strategy) ARG_STRATEGY="$2"; shift 2 ;;
    *) warn "Option ma m3roufach: $1"; shift ;;
  esac
done

# ============================================================
# 1. INSTALLATION (mra wa7da, mn b3d kadoz dghya)
# ============================================================
install_env() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
    Darwin*)              OS="mac" ;;
    *)                    OS="linux" ;;
  esac
  if [ "$OS" != "windows" ]; then
    warn "Package MetaTrader5 khdam ghir 3la Windows. 3la $OS t9der tfchel installation."
  fi

  PY=""
  for c in "py -3" python3 python; do
    if $c -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" >/dev/null 2>&1; then
      PY="$c"; break
    fi
  done
  [ -z "$PY" ] && fail "Python 3.8+ ma kaynch. Telechargih mn https://www.python.org/downloads/ (cochi 'Add Python to PATH') w 3awed."

  if [ ! -d "$VENV_DIR" ]; then
    info "Awel mra: kanwjjed environnement..."
    $PY -m venv "$VENV_DIR" || fail "Ma9dertch nwjjed venv."
  fi
  if [ -f "$VENV_DIR/Scripts/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/Scripts/activate"
  else
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
  fi

  # Kaninstalli packages ghir ila tbdl requirements.txt
  if ! cmp -s requirements.txt "$VENV_DIR/.requirements.installed"; then
    info "Kaninstalli les packages (t9der takhod chi d9i9a)..."
    python -m pip install --upgrade pip -q
    python -m pip install -r requirements.txt -q || fail "Installation dyal packages fchlat."
    cp requirements.txt "$VENV_DIR/.requirements.installed"
  fi
  ok "Environnement wajd"

  mkdir -p "$ACCOUNTS_DIR" "$STRAT_DIR"
  # Migration: .env l9dim -> accounts/default.env
  if [ -f ".env" ] && [ -z "$(ls -A "$ACCOUNTS_DIR"/*.env 2>/dev/null)" ]; then
    mv .env "$ACCOUNTS_DIR/default.env" && ok ".env l9dim tn9el l accounts/default.env"
  fi
}

# ============================================================
# 2. OUTILS
# ============================================================
get_accounts() {
  ACCOUNTS=()
  for f in "$ACCOUNTS_DIR"/*.env; do
    [ -e "$f" ] && ACCOUNTS+=("$(basename "$f" .env)")
  done
}

get_strategies() {
  STRATS=()
  for f in "$STRAT_DIR"/*.py; do
    [ -e "$f" ] || continue
    b="$(basename "$f" .py)"
    [[ "$b" == _* ]] && continue
    STRATS+=("$b")
  done
}

save_last() { printf "ACCOUNT=%s\nSTRATEGY=%s\n" "$ACCOUNT" "$STRATEGY" > "$LAST_FILE"; }

load_last() {
  [ -f "$LAST_FILE" ] || return
  ACCOUNT="$(grep '^ACCOUNT=' "$LAST_FILE" | cut -d= -f2-)"
  STRATEGY="$(grep '^STRATEGY=' "$LAST_FILE" | cut -d= -f2-)"
  [ -f "$ACCOUNTS_DIR/$ACCOUNT.env" ] || ACCOUNT=""
  [ -f "$STRAT_DIR/$STRATEGY.py" ]    || STRATEGY=""
}

# Kayt9awed l valeur bach python-dotenv y9raha s7i7a (7ta ila fiha # wla espace)
quote() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\'/\\\'}"
  printf "'%s'" "$s"
}

# choose "Titre" item1 item2 ... -> CHOICE
choose() {
  local title="$1"; shift
  local items=("$@") i=1 n
  echo; echo -e "${C}$title${N}"
  for it in "${items[@]}"; do echo "  [$i] $it"; i=$((i + 1)); done
  read -rp "  Ra9m: " n
  if [[ "$n" =~ ^[0-9]+$ ]] && [ "$n" -ge 1 ] && [ "$n" -le "${#items[@]}" ]; then
    CHOICE="${items[$((n - 1))]}"; return 0
  fi
  warn "Ikhtiyar ghalat."; return 1
}

# ============================================================
# 3. COMPTES
# ============================================================
add_account() {
  local name login pass server pairs a
  echo; echo -e "${C}Zid compte jdid${N}"
  read -rp  "  Smiya (ex: demo, live, ftmo1)  : " name
  name="$(printf "%s" "$name" | tr -cd 'A-Za-z0-9_-')"
  [ -z "$name" ] && { warn "Smiya khawya (ghir 7rouf, ar9am, - w _)."; return 1; }
  if [ -f "$ACCOUNTS_DIR/$name.env" ]; then
    read -rp "  '$name' deja kayn. Tbdlo? (o/n): " a
    [[ "$a" =~ ^[oOyY] ]] || return 1
  fi
  read -rp  "  Login (numéro de compte)       : " login
  read -rsp "  Password                       : " pass; echo
  read -rp  "  Server (ex: Broker-Demo)       : " server
  read -rp  "  Paires [EURUSD,GBPUSD,USDJPY]  : " pairs
  pairs="${pairs:-EURUSD,GBPUSD,USDJPY}"

  [[ "$login" =~ ^[0-9]+$ ]] || { warn "Login khaso ykon ghir ar9am."; return 1; }
  [ -z "$pass" ]   && { warn "Password khawi."; return 1; }
  [ -z "$server" ] && { warn "Server khawi."; return 1; }

  {
    echo "MT5_LOGIN=$login"
    echo "MT5_PASSWORD=$(quote "$pass")"
    echo "MT5_SERVER=$(quote "$server")"
    echo "MT5_PATH="
    echo "FOREX_PAIRS=$pairs"
  } > "$ACCOUNTS_DIR/$name.env"
  chmod 600 "$ACCOUNTS_DIR/$name.env" 2>/dev/null

  ACCOUNT="$name"; save_last
  ok "Compte '$name' tsjjel w tkhtar."
}

choose_account() {
  get_accounts
  if [ "${#ACCOUNTS[@]}" -eq 0 ]; then
    warn "Ma kayn 7ta compte, zid wa7d."
    add_account; return
  fi
  local NEW="+ Zid compte jdid"
  choose "Khtar compte:" "${ACCOUNTS[@]}" "$NEW" || return 1
  if [ "$CHOICE" == "$NEW" ]; then add_account; else ACCOUNT="$CHOICE"; save_last; ok "Compte: $ACCOUNT"; fi
}

delete_account() {
  get_accounts
  [ "${#ACCOUNTS[@]}" -eq 0 ] && { warn "Ma kayn 7ta compte."; return; }
  choose "Ina compte bghiti tms7?" "${ACCOUNTS[@]}" || return
  local a; read -rp "  Mt2kked tms7 '$CHOICE'? (o/n): " a
  [[ "$a" =~ ^[oOyY] ]] || return
  rm -f "$ACCOUNTS_DIR/$CHOICE.env" && ok "Compte '$CHOICE' tms7."
  [ "$ACCOUNT" == "$CHOICE" ] && ACCOUNT="" && save_last
}

# ============================================================
# 4. STRATEGIES
# ============================================================
choose_strategy() {
  get_strategies
  [ "${#STRATS[@]}" -eq 0 ] && { warn "Ma kayn 7ta strategy f dossier $STRAT_DIR/."; return 1; }
  if [ "${#STRATS[@]}" -eq 1 ]; then STRATEGY="${STRATS[0]}"; save_last; return 0; fi
  choose "Khtar strategy:" "${STRATS[@]}" || return 1
  STRATEGY="$CHOICE"; save_last; ok "Strategy: $STRATEGY"
}

run_strategy() {
  [ -z "$ACCOUNT" ]  && { choose_account  || return; }
  [ -z "$STRATEGY" ] && { choose_strategy || return; }
  [ -f "$ACCOUNTS_DIR/$ACCOUNT.env" ] || { warn "Compte '$ACCOUNT' ma kaynch."; ACCOUNT=""; return; }
  [ -f "$STRAT_DIR/$STRATEGY.py" ]    || { warn "Strategy '$STRATEGY' ma kaynach."; STRATEGY=""; return; }

  echo
  echo -e "${B}=============================================="
  echo "  Compte: $ACCOUNT  |  Strategy: $STRATEGY"
  echo -e "==============================================${N}"
  MT5_ACCOUNT_FILE="$ACCOUNTS_DIR/$ACCOUNT.env" python "$STRAT_DIR/$STRATEGY.py" \
    || warn "Strategy w9fat b erreur (t2kked anna MetaTrader 5 m7loul w les infos s7i7in)."
}

# ============================================================
# 5. MAIN
# ============================================================
install_env

# Mode direct: bla menu
if [ -n "$ARG_ACCOUNT" ] || [ -n "$ARG_STRATEGY" ]; then
  load_last
  [ -n "$ARG_ACCOUNT" ]  && ACCOUNT="$ARG_ACCOUNT"
  [ -n "$ARG_STRATEGY" ] && STRATEGY="$ARG_STRATEGY"
  [ -f "$ACCOUNTS_DIR/$ACCOUNT.env" ] || { echo "[X] Compte '$ACCOUNT' ma kaynch f $ACCOUNTS_DIR/"; exit 1; }
  [ -f "$STRAT_DIR/$STRATEGY.py" ]    || { echo "[X] Strategy '$STRATEGY' ma kaynach f $STRAT_DIR/"; exit 1; }
  MT5_ACCOUNT_FILE="$ACCOUNTS_DIR/$ACCOUNT.env" python "$STRAT_DIR/$STRATEGY.py"
  exit $?
fi

# Mode menu
load_last
[ -z "$ACCOUNT" ]  && choose_account
[ -z "$STRATEGY" ] && choose_strategy

while true; do
  echo
  echo -e "${C}=============== MENU ===============${N}"
  echo -e "  Compte   : ${G}${ACCOUNT:-(ma tkhtarch)}${N}"
  echo -e "  Strategy : ${G}${STRATEGY:-(ma tkhtarch)}${N}"
  echo "------------------------------------"
  echo "  [1] Lanci strategy"
  echo "  [2] Bdel compte"
  echo "  [3] Bdel strategy"
  echo "  [4] Zid compte jdid"
  echo "  [5] Ms7 compte"
  echo "  [0] Khrej"
  read -rp "  Ra9m: " opt
  case "$opt" in
    1) run_strategy ;;
    2) choose_account ;;
    3) choose_strategy ;;
    4) add_account ;;
    5) delete_account ;;
    0) echo "Bslama!"; exit 0 ;;
    *) warn "Ikhtiyar ghalat." ;;
  esac
done
