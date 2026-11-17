#!/usr/bin/env bash
# comune2026.sh - impostazioni e funzioni comuni agli script cutechess della revisione 2026.
# Non si esegue: si include con "source" da match_nuggets2026.sh e roundrobin_nuggets2026.sh.
# Percorsi, versioni e risorse si cambiano SOLO qui, cosi' tutti gli esperimenti restano allineati.

# --- Motori: ultime versioni (aggiornare percorsi e nomi prima di partire) -------------
SF=/home/sdp/Stockfish/src/Stockfish19-universal
SC=/home/sdp/ShashChessDev/src/ShashChess42-universal
RK=/home/sdp/Reckless/target/release/reckless          # da adattare al percorso reale
PC=/home/sdp/PlentyChess/PlentyChess                   # da adattare al percorso reale
NOME_SF=Stockfish19
NOME_SC=ShashChess42
NOME_RK=Reckless          # mettere la versione nel nome, es. Reckless0.9.0
NOME_PC=PlentyChess       # es. PlentyChess8.0.0

# --- Condizioni di gioco: identiche in tutti gli esperimenti --------------------------
TB=/home/sdp/syzygy                     # piu' cartelle: separarle con ':'
BASE=/home/sdp/ShashChessDev/tests/Tests2026
TC=${TC:-1500+10}                       # 25'+10"; per le prove di fumo: TC=10+0.1
THREADS=4                               # thread per istanza: regola fissa del protocollo
HASH=2048                               # MB per istanza
CONC=${CONC:-47}                        # partite simultanee: 47 x 4 = 188 thread su 192 core fisici

# Aggiudicazioni e opzioni di cutechess-cli comuni a tutti i match (dallo script match2026.sh)
ARGS_COMUNI=(
  -each proto=uci "tc=$TC" timemargin=1000 restart=on
  -draw movenumber=40 movecount=10 score=10
  -resign movecount=5 score=1000 twosided=true
  -maxmoves 200
  -tb "$TB" -tbpieces 6
  -recover
)

# Codice del motore -> M_NOME, M_CMD, M_EXTRA (opzioni specifiche del motore)
definisci_motore() {
  case $1 in
    SF) M_NOME=$NOME_SF; M_CMD=$SF; M_EXTRA=() ;;
    SC) M_NOME=$NOME_SC; M_CMD=$SC; M_EXTRA=("Persisted learning=Off" "Experience Book=false") ;;
    RK) M_NOME=$NOME_RK; M_CMD=$RK; M_EXTRA=() ;;
    PC) M_NOME=$NOME_PC; M_CMD=$PC; M_EXTRA=() ;;
    *)  echo "[ERRORE] motore sconosciuto: $1 (codici ammessi: SF SC RK PC)" >&2; return 1 ;;
  esac
  [[ -x $M_CMD ]] || { echo "[ERRORE] eseguibile non trovato o non eseguibile: $M_CMD" >&2; return 1; }
}

# Opzioni UCI dichiarate da un motore, una per riga
opzioni_uci() {
  printf 'uci\nquit\n' | timeout 60 "$1" 2>/dev/null | sed -n 's/^option name \(.*\) type .*/\1/p'
}

# Argomenti "-engine ..." per cutechess-cli in ARGS_MOTORE, con le sole opzioni che il motore
# dichiara: un'opzione non supportata viene segnalata e omessa, mai passata alla cieca.
# Uso: args_motore NOME ESEGUIBILE [Opzione=valore ...]
args_motore() {
  local nome=$1 cmd=$2 supportate coppia chiave
  shift 2
  supportate=$(opzioni_uci "$cmd")
  [[ -n $supportate ]] || { echo "[ERRORE] $cmd non risponde al comando uci" >&2; return 1; }
  ARGS_MOTORE=(-engine "name=$nome" "cmd=$cmd" "dir=$(dirname "$cmd")")
  for coppia in "Threads=$THREADS" "Hash=$HASH" "SyzygyPath=$TB" "SyzygyProbeDepth=1" \
                "Syzygy50MoveRule=true" "SyzygyProbeLimit=7" "$@"; do
    chiave=${coppia%%=*}
    if grep -qxF -- "$chiave" <<< "$supportate"; then
      ARGS_MOTORE+=("option.$coppia")
    else
      echo "[AVVISO] $nome: opzione '$chiave' non dichiarata dal motore, omessa" >&2
    fi
  done
}

# Formato e numero delle posizioni di partenza
formato_aperture() {
  case "${1,,}" in
    *.epd) echo epd ;;
    *.pgn) echo pgn ;;
    *) echo "[ERRORE] estensione non riconosciuta (serve .epd o .pgn): $1" >&2; return 1 ;;
  esac
}
conta_aperture() {
  case "${1,,}" in
    *.epd) grep -cv '^[[:space:]]*$' "$1" ;;
    *.pgn) grep -c '^\[Event ' "$1" ;;
  esac
}

# Condizioni della macchina, salvate con i risultati (servono per la Tabella 2 del paper)
descrivi_macchina() {
  {
    echo "data: $(date -Is)"; echo "host: $(hostname)"; uname -a
    lscpu
    echo "SMT attivo: $(cat /sys/devices/system/cpu/smt/active 2>/dev/null || echo '?')"
    echo "governor cpu0: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo '?')"
    free -g
    numactl -H 2>/dev/null || true
    echo "cutechess-cli: $(command -v cutechess-cli)"
    cutechess-cli --version 2>&1 | head -2 || true
  } > "$1/macchina.txt" 2>&1
}

# Firma dei motori: id, hash dell'eseguibile, firma di bench (se il motore la fornisce)
firma_motori() {
  local dir=$1 cmd
  shift
  for cmd in "$@"; do
    {
      echo "== $cmd"
      sha256sum "$cmd"
      printf 'uci\nquit\n' | timeout 60 "$cmd" 2>/dev/null | grep -E '^id (name|author)' || true
      echo "-- bench"
      (cd "$(dirname "$cmd")" && timeout 900 "$cmd" bench 2>&1 | grep -iE 'nodes|nps|bench' | tail -3) || true
      echo
    } >> "$dir/motori.txt"
  done
}

# Controllo delle risorse: thread richiesti contro core fisici, limite dei descrittori
controlla_risorse() {
  local fisici richiesti
  fisici=$(lscpu -p=CORE,SOCKET 2>/dev/null | grep -v '^#' | sort -u | wc -l)
  richiesti=$(( CONC * THREADS ))
  echo "[*] Core fisici: $fisici; thread di ricerca richiesti: $CONC x $THREADS = $richiesti"
  if (( fisici > 0 && richiesti > fisici )); then
    echo "[AVVISO] Piu' thread che core fisici: si usa l'SMT e ogni motore va piu' lento." >&2
    echo "[AVVISO] Il controllo di tempo effettivo si riduce: dichiararlo nel paper." >&2
  fi
  ulimit -n 65536 2>/dev/null || ulimit -n "$(ulimit -Hn)"
}
