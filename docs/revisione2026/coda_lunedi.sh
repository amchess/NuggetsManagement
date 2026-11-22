#!/usr/bin/env bash
# coda_lunedi.sh - fase F (Pwin da 0,55 a 0,95), dopo la fine di coda_domenica.sh (E5). Disegno in PREREGISTRAZIONE_F.md.
#
# Lanciare in tmux dalla radice del repository, con il venv attivo:
#   docs/revisione2026/coda_lunedi.sh
# Aspetta che coda_domenica.sh sia terminata (controllo ogni minuto), poi:
#   F1. due rianalisi a 60 s delle 360 candidate delle fasce esterne (circa 20 min);
#   F2. scelta delle posizioni con seleziona_fasce.py (seme 2026, 80 per fascia);
#   F3. ShashChess 42.3 - Stockfish 19 a 25'+10", una coppia a colori invertiti per posizione (640 partite, circa 17 h).
# Diario in $BASE/risultati/coda3_<data>.log.
set -uo pipefail
QUI=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$QUI/../.." && pwd)
# shellcheck source=comune2026.sh
source "$QUI/comune2026.sh"
PY=$REPO/.venv/bin/python
[[ -x $PY ]] || PY=python3
mkdir -p "$BASE/risultati"
DIARIO=$BASE/risultati/coda3_$(date +%Y%m%d_%H%M).log
nota() { echo "[$(date '+%F %T')] $*" | tee -a "$DIARIO"; }

nota "In attesa della fine di coda_domenica.sh"
while pgrep -f "coda_domenica\.sh" >/dev/null; do sleep 60; done
nota "coda_domenica.sh terminata"
cd "$REPO" || exit 1

nota "F1: rianalisi delle 360 candidate delle fasce esterne, 2 x 60 s"
for k in 01 02; do
  "$PY" src/main.py --config config_fasce_rianalisi.json --output-dir "data/fasce2026/rianalisi$k" 2>&1 | tee -a "$DIARIO"
  nota "Rianalisi $k terminata (codice ${PIPESTATUS[0]})"
done

nota "F2: scelta delle posizioni (seme 2026, 80 per fascia)"
"$PY" "$QUI/seleziona_fasce.py" --estrazione data/outputWch2026_SF19/tutte_le_posizioni.csv \
  --rianalisi data/fasce2026/rianalisi01/tutte_le_posizioni.csv data/fasce2026/rianalisi02/tutte_le_posizioni.csv \
  --candidate "$QUI/posizioni/fasce_candidate.csv" --medie "$QUI/posizioni/medie_3analisi.csv" \
  --pool "$QUI/posizioni/nuggets_pool_robusto.csv" --n 80 --seme 2026 --out "$QUI/posizioni/fasce_320" 2>&1 | tee -a "$DIARIO"
if [[ ${PIPESTATUS[0]} -ne 0 || ! -s $QUI/posizioni/fasce_320.epd ]]; then
  nota "[ERRORE] scelta delle posizioni non riuscita: match non avviato"
  exit 1
fi

nota "F3: match a 25'+10\" su $(wc -l < "$QUI/posizioni/fasce_320.epd") posizioni x 2 colori"
TC=1500+10 CONC=47 "$QUI/match_nuggets2026.sh" "$QUI/posizioni/fasce_320.epd" fasce_tc1500 1 2>&1 | tee -a "$DIARIO"
nota "F terminata (codice ${PIPESTATUS[0]})"
nota "Coda terminata"
