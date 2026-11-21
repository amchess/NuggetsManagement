#!/usr/bin/env bash
# coda_domenica.sh - dopo la fine di coda_sabato.sh: fase B (Lc0 sulle 2.321 posizioni candidate),
# poi fase E5 (pool robusto a 60'+30").
#
# Lanciare in tmux dalla radice del repository, con il venv attivo:
#   docs/revisione2026/coda_domenica.sh
# Aspetta che coda_sabato.sh sia terminata (controllo ogni minuto), poi esegue le due fasi una dopo l'altra;
# se una fase fallisce, passa alla successiva. Diario in $BASE/risultati/coda2_<data>.log.
# Durata prevista: B circa 3-4 h, E5 circa 18 h.
set -uo pipefail
QUI=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$QUI/../.." && pwd)
# shellcheck source=comune2026.sh
source "$QUI/comune2026.sh"
PY=$REPO/.venv/bin/python
[[ -x $PY ]] || PY=python3
mkdir -p "$BASE/risultati"
DIARIO=$BASE/risultati/coda2_$(date +%Y%m%d_%H%M).log
nota() { echo "[$(date '+%F %T')] $*" | tee -a "$DIARIO"; }

nota "In attesa della fine di coda_sabato.sh"
while pgrep -f "coda_sabato\.sh" >/dev/null; do sleep 60; done
nota "coda_sabato.sh terminata"

nota "B: Lc0 sulle 2.321 posizioni candidate (config_lc0.json)"
cd "$REPO" || exit 1
"$PY" src/main.py --config config_lc0.json 2>&1 | tee -a "$DIARIO"
nota "B terminata (codice ${PIPESTATUS[0]})"

nota "E5: pool robusto a 60'+30\", 130 posizioni x 2 colori = 260 partite"
TC=3600+30 CONC=47 "$QUI/match_nuggets2026.sh" "$QUI/posizioni/nuggets_pool_robusto.epd" pool_tc3600 1 2>&1 | tee -a "$DIARIO"
nota "E5 terminata (codice ${PIPESTATUS[0]})"
nota "Coda terminata"
