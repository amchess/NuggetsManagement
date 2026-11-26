#!/bin/bash
# prepara_commit_finale.sh - copia nel repository i risultati della revisione 2026, per il commit finale.
#
# Si lancia dalla radice del repository (~/NuggetsManagement), a esperimenti finiti:
#     bash docs/revisione2026/prepara_commit_finale.sh          (DRY=1 davanti: mostra soltanto cosa farebbe)
#
# Le partite (.pgn) e i registri (.csv) sono compressi con gzip: *.pgn e data/ sono esclusi da .gitignore,
# mentre i file .gz no. Nessun file sorgente viene modificato o cancellato.
set -uo pipefail

RIS=${RIS:-/home/sdp/ShashChessDev/tests/Tests2026/risultati}
DEST=docs/revisione2026
DRY=${DRY:-0}
mancanti=0

[[ -d .git && -d $DEST ]] || { echo "[ERRORE] lanciare dalla radice del repository NuggetsManagement"; exit 1; }

esegui() { if [[ $DRY == 1 ]]; then echo "  $*"; else "$@"; fi; }

copia() {            # copia <sorgente> <destinazione>; .pgn, .csv e .log vengono compressi
  local s=$1 d=$2
  if [[ ! -f $s ]]; then echo "[AVVISO] manca $s"; mancanti=$((mancanti + 1)); return; fi
  esegui mkdir -p "$(dirname "$d")"
  case $s in
    *.pgn|*.csv|*.log) if [[ $DRY == 1 ]]; then echo "  gzip -c $s > $d.gz"; else gzip -9 -c "$s" > "$d.gz"; fi ;;
    *) esegui cp -p "$s" "$d" ;;
  esac
}

# 1. Cartelle delle fasi giocate (C, D, E3, E4, E1, E5, F)
fasi=(20261118_2057_pool_robusto 20261120_0014_rr_top100_robusto 20261121_1027_nps_2026
      20261121_1045_pool_tc60 20261121_1156_controllo_uho)
e5=( "$RIS"/*_pool_tc3600 )
if [[ -d ${e5[0]} ]]; then fasi+=("$(basename "${e5[-1]}")"); else echo "[AVVISO] cartella di E5 non trovata"; mancanti=$((mancanti + 1)); fi
ff=( "$RIS"/*_fasce_tc1500 )
if [[ -d ${ff[0]} ]]; then fasi+=("$(basename "${ff[-1]}")"); else echo "[AVVISO] cartella di F non trovata"; mancanti=$((mancanti + 1)); fi
for f in "${fasi[@]}"; do
  [[ -d $RIS/$f ]] || { echo "[AVVISO] manca la cartella $RIS/$f"; mancanti=$((mancanti + 1)); continue; }
  echo "[*] fase $f"
  for s in "$RIS/$f"/*; do
    [[ -f $s ]] && copia "$s" "$DEST/risultati/$f/$(basename "$s")"
  done
done

# 2. Diari delle code notturne
for s in "$RIS"/coda_*.log "$RIS"/coda2_*.log "$RIS"/coda3_*.log; do
  [[ -f $s ]] && copia "$s" "$DEST/risultati/diari/$(basename "$s")"
done

# 3. Partite dei Mondiali e registri delle analisi (cartella data/, esclusa da git)
echo "[*] registri"
copia data/wch.pgn                                          $DEST/registri/wch.pgn
copia data/outputWch2026_SF19/pgn_sha256.txt                $DEST/registri/estrazione_pgn_sha256.txt
copia data/outputWch2026_SF19/metadati_esecuzione.json      $DEST/registri/estrazione_metadati.json
copia data/outputWch2026_SF19/tutte_le_posizioni.csv        $DEST/registri/estrazione_tutte_le_posizioni.csv
copia data/outputWch2026_SF19/nuggets.csv                   $DEST/registri/estrazione_nuggets.csv
copia data/outputWch2026_SF19/candidati.csv                 $DEST/registri/candidati_2321.csv
copia data/rumore/run01/tutte_le_posizioni.csv              $DEST/registri/rumore_run01.csv
copia data/rumore/run02/tutte_le_posizioni.csv              $DEST/registri/rumore_run02.csv
copia data/rumore/stabilita_2026.md                         $DEST/rapporti/stabilita_2026.md
copia data/rumore/stabilita_2026.json                       $DEST/rapporti/stabilita_2026.json
copia data/outputUHO2024_SF19/rianalisi01/tutte_le_posizioni.csv $DEST/registri/uho_rianalisi01.csv
copia data/outputUHO2024_SF19/rianalisi02/tutte_le_posizioni.csv $DEST/registri/uho_rianalisi02.csv
copia data/outputWch2026_Lc0/tutte_le_posizioni.csv         $DEST/registri/lc0_tutte_le_posizioni.csv
[[ -f data/outputWch2026_Lc0/metadati_esecuzione.json ]] && copia data/outputWch2026_Lc0/metadati_esecuzione.json $DEST/registri/lc0_metadati.json
for k in 01 02; do      # fase F: due rianalisi delle 360 nuove candidate delle fasce esterne
  copia data/fasce2026/rianalisi$k/tutte_le_posizioni.csv     $DEST/registri/fasce_rianalisi$k.csv
  copia data/fasce2026/rianalisi$k/metadati_esecuzione.json   $DEST/registri/fasce_rianalisi${k}_metadati.json
done

# 4. Posizioni della fase F, scritte da seleziona_fasce.py direttamente in posizioni/ (restano dove sono)
for s in $DEST/posizioni/fasce_320.csv $DEST/posizioni/fasce_320.epd $DEST/posizioni/fasce_320.md; do
  [[ -f $s ]] || { echo "[AVVISO] manca $s"; mancanti=$((mancanti + 1)); }
done

echo
if [[ $DRY == 1 ]]; then
  echo "[DRY] nessun file scritto. Avvisi: $mancanti"
else
  du -sh $DEST/risultati $DEST/registri 2>/dev/null
  find $DEST/risultati $DEST/registri -type f -size +50M -exec echo "[AVVISO] file oltre 50 MB: {}" \;
  echo "[OK] copia finita. Avvisi: $mancanti. Controllare con: git status --short | head -50"
fi
