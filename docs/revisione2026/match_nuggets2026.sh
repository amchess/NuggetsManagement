#!/usr/bin/env bash
# match_nuggets2026.sh - match a due motori da un insieme di posizioni, con cutechess-cli 1.5.1.
# Deriva da match2026.sh: stesse aggiudicazioni e opzioni, 4 thread per istanza, 47 partite simultanee.
#
# Uso:   ./match_nuggets2026.sh POSIZIONI.epd|.pgn ETICHETTA [CICLI]
#   Ogni posizione si gioca due volte a colori invertiti per ciclo:
#   partite = 2 x posizioni x CICLI   (es. 50 posizioni x 3 cicli = 300 partite, come match2026.sh)
#
# Variabili opzionali:
#   MOTORE_A, MOTORE_B  codici dei motori (default SF e SC; ammessi SF SC RK PC, vedi comune2026.sh)
#   CONC                partite simultanee (default 47)
#   DRY=1               prepara la cartella e scrive il comando senza giocare
#
# Esempi:
#   ./match_nuggets2026.sh $BASE/posizioni/nuggets_pool.epd pool_wch            # match confermativo
#   ./match_nuggets2026.sh $BASE/matches2026/Test2026.pgn test2026 3             # replica sulle 50 posizioni
#   MOTORE_A=SF MOTORE_B=SC ./match_nuggets2026.sh $BASE/posizioni/uho_250.epd controllo_uho
set -euo pipefail
QUI=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=comune2026.sh
source "$QUI/comune2026.sh"

POS=$(readlink -f "${1:?indicare il file delle posizioni (.epd o .pgn)}")
ETI=${2:?indicare un etichetta, es. pool_wch}
CICLI=${3:-1}
[[ -s $POS ]] || { echo "[ERRORE] file delle posizioni vuoto o assente: $POS" >&2; exit 1; }
FMT=$(formato_aperture "$POS")
NPOS=$(conta_aperture "$POS")
(( NPOS > 0 )) || { echo "[ERRORE] nessuna posizione in $POS" >&2; exit 1; }
ROUNDS=$(( NPOS * CICLI ))

definisci_motore "${MOTORE_A:-SF}"; NOME_A=$M_NOME; CMD_A=$M_CMD; EXTRA_A=(${M_EXTRA[@]+"${M_EXTRA[@]}"})
definisci_motore "${MOTORE_B:-SC}"; NOME_B=$M_NOME; CMD_B=$M_CMD; EXTRA_B=(${M_EXTRA[@]+"${M_EXTRA[@]}"})

OUT=$BASE/risultati/$(date +%Y%m%d_%H%M)_${ETI}
mkdir -p "$OUT"
cp "$POS" "$OUT/"
cp "$0" "$QUI/comune2026.sh" "$OUT/"
controlla_risorse
descrivi_macchina "$OUT"

args_motore "$NOME_A" "$CMD_A" ${EXTRA_A[@]+"${EXTRA_A[@]}"}; ARGS_A=("${ARGS_MOTORE[@]}")
args_motore "$NOME_B" "$CMD_B" ${EXTRA_B[@]+"${EXTRA_B[@]}"}; ARGS_B=("${ARGS_MOTORE[@]}")

CMD=(cutechess-cli
  -event "$NOME_A vs $NOME_B - $ETI - $TC" -site "$(hostname)"
  -tournament round-robin
  "${ARGS_A[@]}" "${ARGS_B[@]}"
  "${ARGS_COMUNI[@]}"
  -openings "file=$POS" "format=$FMT" order=sequential
  -repeat 2 -games 2 -rounds "$ROUNDS"
  -concurrency "$CONC"
  -ratinginterval 10
  -pgnout "$OUT/partite.pgn")
printf '%q ' "${CMD[@]}" > "$OUT/comando.txt"; echo >> "$OUT/comando.txt"

echo "[*] $NOME_A - $NOME_B: $NPOS posizioni x $CICLI cicli x 2 colori = $(( 2 * ROUNDS )) partite"
echo "[*] Concorrenza $CONC, $THREADS thread per motore, $TC; risultati in $OUT"
if [[ ${DRY:-0} == 1 ]]; then
  echo "[DRY] comando in $OUT/comando.txt"; exit 0
fi
firma_motori "$OUT" "$CMD_A" "$CMD_B"

set +e
"${CMD[@]}" 2>&1 | tee "$OUT/cutechess.log"
STATO=${PIPESTATUS[0]}
set -e
NPART=$( (grep -c '^\[Result ' "$OUT/partite.pgn" 2>/dev/null) || true)
echo "[*] cutechess-cli terminato (codice $STATO): ${NPART:-0} partite su $(( 2 * ROUNDS )) in $OUT/partite.pgn"
exit "$STATO"
