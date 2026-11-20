#!/usr/bin/env bash
# roundrobin_nuggets2026.sh - round robin a 4 motori in disegno completamente incrociato.
#
# Ogni coppia di motori gioca OGNI posizione con entrambi i colori. Per garantirlo non si usa il
# round robin interno di cutechess-cli (che assegna aperture diverse alle diverse coppie: e' cio'
# che e' successo nel torneo del 2025): si lanciano 6 match separati a due motori, uno per coppia,
# con lo stesso file di posizioni e gli stessi parametri. I 6 match girano in parallelo e si
# dividono le partite simultanee (47 -> 8,8,8,8,8,7), cosi' tutte le coppie giocano nelle stesse
# condizioni di carico della macchina.
#
# Uso:   ./roundrobin_nuggets2026.sh POSIZIONI.epd ETICHETTA [CICLI]
#   partite = 6 coppie x 2 colori x posizioni x CICLI  (100 posizioni -> 1.200 partite)
# Variabili opzionali: MOTORI (default "SF SC RK TR"), CONC (default 47), PARALLELO=0 (coppie una
#   dopo l'altra, ciascuna con CONC partite simultanee), DRY=1 (scrive i comandi senza giocare)
set -euo pipefail
QUI=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=comune2026.sh
source "$QUI/comune2026.sh"

POS=$(readlink -f "${1:?indicare il file delle posizioni (.epd o .pgn)}")
ETI=${2:?indicare un etichetta, es. top100}
CICLI=${3:-1}
[[ -s $POS ]] || { echo "[ERRORE] file delle posizioni vuoto o assente: $POS" >&2; exit 1; }
FMT=$(formato_aperture "$POS")
NPOS=$(conta_aperture "$POS")
ROUNDS=$(( NPOS * CICLI ))
read -r -a CODICI <<< "${MOTORI:-SF SC RK TR}"
(( ${#CODICI[@]} >= 3 )) || { echo "[ERRORE] servono almeno 3 motori" >&2; exit 1; }

OUT=$BASE/risultati/$(date +%Y%m%d_%H%M)_rr_${ETI}
mkdir -p "$OUT"
cp "$POS" "$OUT/"
cp "$0" "$QUI/comune2026.sh" "$OUT/"
controlla_risorse
descrivi_macchina "$OUT"

# Argomenti -engine di ogni motore (opzioni verificate una volta sola)
declare -A NOME CMDM ARGS
for c in "${CODICI[@]}"; do
  definisci_motore "$c"
  args_motore "$M_NOME" "$M_CMD" ${M_EXTRA[@]+"${M_EXTRA[@]}"}
  NOME[$c]=$M_NOME; CMDM[$c]=$M_CMD
  ARGS[$c]=$(printf '%q ' "${ARGS_MOTORE[@]}")
done

# Coppie e ripartizione delle partite simultanee
COPPIE=()
for (( i = 0; i < ${#CODICI[@]}; i++ )); do
  for (( j = i + 1; j < ${#CODICI[@]}; j++ )); do COPPIE+=("${CODICI[i]}:${CODICI[j]}"); done
done
NC=${#COPPIE[@]}
if [[ ${PARALLELO:-1} == 1 ]]; then
  (( CONC >= NC )) || { echo "[ERRORE] CONC=$CONC e' minore del numero di coppie ($NC)" >&2; exit 1; }
  QUOTA=$(( CONC / NC )); RESTO=$(( CONC % NC ))
fi

echo "[*] $NC coppie x $NPOS posizioni x $CICLI cicli x 2 colori = $(( NC * 2 * ROUNDS )) partite; risultati in $OUT"
[[ ${DRY:-0} == 1 ]] || firma_motori "$OUT" "${CMDM[@]}"

PIDS=(); k=0
for coppia in "${COPPIE[@]}"; do
  a=${coppia%%:*}; b=${coppia##*:}
  if [[ ${PARALLELO:-1} == 1 ]]; then
    conc=$(( QUOTA + (k < RESTO ? 1 : 0) ))
  else
    conc=$CONC
  fi
  k=$(( k + 1 ))
  eval "ARGS_A=(${ARGS[$a]})"
  eval "ARGS_B=(${ARGS[$b]})"
  CMD=(cutechess-cli
    -event "RoundRobin nuggets 2026 - $ETI - $TC" -site "$(hostname)"
    -tournament round-robin
    "${ARGS_A[@]}" "${ARGS_B[@]}"
    "${ARGS_COMUNI[@]}"
    -openings "file=$POS" "format=$FMT" order=sequential
    -repeat 2 -games 2 -rounds "$ROUNDS"
    -concurrency "$conc"
    -ratinginterval 10
    -pgnout "$OUT/partite_${NOME[$a]}_${NOME[$b]}.pgn")
  printf '%q ' "${CMD[@]}" > "$OUT/comando_${NOME[$a]}_${NOME[$b]}.txt"
  echo >> "$OUT/comando_${NOME[$a]}_${NOME[$b]}.txt"
  echo "[*] ${NOME[$a]} - ${NOME[$b]}: $conc partite simultanee"
  [[ ${DRY:-0} == 1 ]] && continue
  if [[ ${PARALLELO:-1} == 1 ]]; then
    "${CMD[@]}" > "$OUT/cutechess_${NOME[$a]}_${NOME[$b]}.log" 2>&1 &
    PIDS+=($!)
  else
    "${CMD[@]}" 2>&1 | tee "$OUT/cutechess_${NOME[$a]}_${NOME[$b]}.log"
  fi
done
[[ ${DRY:-0} == 1 ]] && { echo "[DRY] comandi in $OUT/comando_*.txt"; exit 0; }

ERRORI=0
for p in ${PIDS[@]+"${PIDS[@]}"}; do wait "$p" || ERRORI=$(( ERRORI + 1 )); done
cat "$OUT"/partite_*.pgn > "$OUT/roundrobin.pgn"
NPART=$(grep -c '^\[Result ' "$OUT/roundrobin.pgn" || true)
echo "[*] Round robin terminato: $NPART partite su $(( NC * 2 * ROUNDS )) in $OUT/roundrobin.pgn; match con errori: $ERRORI"
(( ERRORI == 0 ))
