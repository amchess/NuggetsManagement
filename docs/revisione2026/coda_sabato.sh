#!/usr/bin/env bash
# coda_sabato.sh - fasi E3, E4, E1 e rianalisi delle posizioni UHO, una dopo l'altra (21 novembre 2026).
#
# Lanciare in tmux dalla radice del repository, con il venv attivo:
#   docs/revisione2026/coda_sabato.sh
#
# Ogni fase scrive nella propria cartella di risultati; se una fase fallisce, la coda passa alla successiva.
# Il diario della coda (ora di inizio e fine di ogni fase, codici di uscita) e' in $BASE/risultati/coda_<data>.log.
# Durata prevista: E3 circa 20 min, E4 circa 1 h, E1 circa 12-13 h, rianalisi circa 12 min.
set -uo pipefail
QUI=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$QUI/../.." && pwd)
# shellcheck source=comune2026.sh
source "$QUI/comune2026.sh"
PY=$REPO/.venv/bin/python
[[ -x $PY ]] || PY=python3
mkdir -p "$BASE/risultati"
DIARIO=$BASE/risultati/coda_$(date +%Y%m%d_%H%M).log
nota() { echo "[$(date '+%F %T')] $*" | tee -a "$DIARIO"; }

nota "Inizio coda: E3 (NPS), E4 (pool a 60+0.6), E1 (controllo UHO), rianalisi UHO"

nota "E3: NPS sotto carico, 4 motori, 47 istanze x 4 thread, 5 ripetizioni alternate"
NPS_OUT=$BASE/risultati/$(date +%Y%m%d_%H%M)_nps_2026
mkdir -p "$NPS_OUT"
"$PY" "$QUI/misura_nps.py" \
  --motore "$NOME_SF=$SF" --motore "$NOME_SC=$SC" --motore "$NOME_RK=$RK" --motore "$NOME_TR=$TR" \
  --opzione "$NOME_SC:Persisted learning=Off" --opzione "$NOME_SC:Experience Book=false" \
  --opzione "$NOME_TR:NumaSpread=false" \
  --posizioni "$QUI/posizioni/nuggets_top100_robusto.epd" --riferimento "$NOME_SF" \
  --out "$NPS_OUT/nps_2026" 2>&1 | tee -a "$DIARIO"
nota "E3 terminata (codice ${PIPESTATUS[0]}); risultati in $NPS_OUT"

nota "E4: pool robusto a 60+0.6, 130 posizioni x 4 cicli x 2 colori = 1040 partite"
TC=60+0.6 CONC=47 "$QUI/match_nuggets2026.sh" "$QUI/posizioni/nuggets_pool_robusto.epd" pool_tc60 4 2>&1 | tee -a "$DIARIO"
nota "E4 terminata (codice ${PIPESTATUS[0]})"

nota "E1: controllo UHO, 250 posizioni x 2 colori = 500 partite a 25'+10\""
TC=1500+10 CONC=47 "$QUI/match_nuggets2026.sh" "$QUI/posizioni/uho_250.epd" controllo_uho 1 2>&1 | tee -a "$DIARIO"
nota "E1 terminata (codice ${PIPESTATUS[0]})"

nota "Rianalisi descrittiva delle 250 posizioni UHO: altre 2 analisi a 60 s, per la Pwin media di 3 analisi"
cd "$REPO" || exit 1
for k in 01 02; do
  "$PY" src/main.py --config config_uho_rianalisi.json --output-dir "data/outputUHO2024_SF19/rianalisi$k" 2>&1 | tee -a "$DIARIO"
  nota "Rianalisi $k terminata (codice ${PIPESTATUS[0]})"
done
nota "Coda terminata"
