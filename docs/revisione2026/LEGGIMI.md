# Revisione 2026 (ICG-26-0040): sequenza dei comandi

Questa cartella contiene tutto ciò che serve a rifare gli esperimenti della revisione e a
ricalcolarne le statistiche. I comandi partono dalla radice del repository, salvo dove indicato.

Regola fissa del protocollo: **4 thread per istanza, 47 istanze simultanee** (188 thread di ricerca
sui 192 core fisici). Stessi motori, stesse opzioni e stesso controllo di tempo (25'+10") in tutti
i match. Un solo esperimento alla volta sulla macchina.

| File | A cosa serve |
|---|---|
| `comune2026.sh` | Percorsi dei motori, opzioni comuni, aggiudicazioni: si modifica solo qui |
| `match_nuggets2026.sh` | Match a due motori da un file di posizioni (.epd o .pgn) |
| `roundrobin_nuggets2026.sh` | Round robin a 4 motori in disegno incrociato (6 match paralleli) |
| `misura_nps.py` | NPS ripetuti sotto carico, con intervalli di confidenza |
| `stabilita_registri.py` | Ripetibilità di Pwin e Delta WDL fra analisi ripetute |
| `confronta_oracoli.py` | Selezione delle posizioni per Lc0 e confronto Stockfish–Lc0 |
| `statistiche_match.py` | Statistiche di match e round robin (trinomiale, pentanomiale, cluster, Bradley–Terry, interazione) |

## 0. Preparazione della macchina (una volta)

```bash
sudo cpupower frequency-set -g performance          # frequenza stabile durante le misure
cat /home/sdp/syzygy/*.rtbw > /dev/null              # tablebase WDL nella cache del sistema
pip install -r requirements.txt
python tests/test_registro.py                        # deve stampare "tutti i test superati"
# aggiornare percorsi e nomi dei motori in docs/revisione2026/comune2026.sh
```

Facoltativo, ma rende le misure più pulite: spegnere l'SMT per la durata degli esperimenti
(`echo off | sudo tee /sys/devices/system/cpu/smt/control`, poi `on` alla fine).

## 1. Prove di fumo (circa 15 minuti)

```bash
python src/main.py --config config_test2026.json --conta     # conta le posizioni e stima la durata
cd docs/revisione2026
DRY=1 ./match_nuggets2026.sh /home/sdp/ShashChessDev/tests/Tests2026/matches2026/Test2026.pgn prova
TC=10+0.1 CONC=4 ./match_nuggets2026.sh /home/sdp/ShashChessDev/tests/Tests2026/matches2026/Test2026.pgn fumo
cd ../..
```

## 2. Fase A: estrazione dei nugget dai Mondiali (circa 32 ore)

```bash
python src/main.py --config config.json --conta
nohup python src/main.py --config config.json > data/estrazione_2026.log 2>&1 &
```

Se l'esecuzione si interrompe, si rilancia lo stesso comando: il registro
`tutte_le_posizioni.csv` è scritto riga per riga e le posizioni già analizzate vengono saltate.

## 3. Selezione delle posizioni

```bash
cd docs/outputLTCWch
python genera_pgn.py --csv ../../data/outputWch2026_SF19/nuggets.csv --n 100000 \
       --pwin-tol 0.06 --delta-tol 0.06 --out ../../data/outputWch2026_SF19/nuggets_pool
python genera_pgn.py --csv ../../data/outputWch2026_SF19/nuggets.csv --n 100 \
       --pwin-tol 0.03 --delta-tol 0.03 --out ../../data/outputWch2026_SF19/nuggets_top100
cd ../..
```

## 4. Fasi A2 e A3: rivalidazione delle 50 posizioni e ripetibilità

```bash
python src/main.py --config config_test2026.json                     # circa 3 minuti
for r in 01 02 03 04 05; do
  python src/main.py --config config_rumore.json --output-dir data/rumore/run$r
done
python docs/revisione2026/stabilita_registri.py \
       --registri data/rumore/run*/tutte_le_posizioni.csv --out data/rumore/stabilita_2026
```

## 5. Fase B: validazione con Lc0 su CPU

```bash
python docs/revisione2026/confronta_oracoli.py seleziona \
       --registro data/outputWch2026_SF19/tutte_le_posizioni.csv \
       --out data/outputWch2026_SF19/candidati_lc0.csv --finestra 0.15
OPENBLAS_NUM_THREADS=1 python src/main.py --config config_lc0.json --conta
OPENBLAS_NUM_THREADS=1 nohup python src/main.py --config config_lc0.json > data/lc0_2026.log 2>&1 &
python docs/revisione2026/confronta_oracoli.py confronta \
       --sf data/outputWch2026_SF19/tutte_le_posizioni.csv \
       --lc0 data/outputWch2026_Lc0/tutte_le_posizioni.csv --out data/outputWch2026_Lc0/confronto_sf_lc0
```

## 6. Fasi C, C2, D, E: partite

```bash
cd docs/revisione2026
./match_nuggets2026.sh ../../data/outputWch2026_SF19/nuggets_pool.epd pool_wch        # C: confermativo
./match_nuggets2026.sh /home/sdp/ShashChessDev/tests/Tests2026/matches2026/Test2026.pgn test2026 3   # C2
./roundrobin_nuggets2026.sh ../../data/outputWch2026_SF19/nuggets_top100.epd top100   # D
./match_nuggets2026.sh /percorso/uho_250.epd controllo_uho                            # E: controllo UHO
```

Il file `uho_250.epd` si estrae da un libro UHO con un seme fisso:

```bash
python3 -c "import random,sys; r=[l for l in open(sys.argv[1]) if l.strip()]; random.seed(2026); sys.stdout.writelines(random.sample(r,250))" LIBRO_UHO.epd > uho_250.epd
```

## 7. NPS sotto carico (circa 1 ora)

```bash
source docs/revisione2026/comune2026.sh
python docs/revisione2026/misura_nps.py --motore $NOME_SF=$SF --motore $NOME_SC=$SC \
       --motore $NOME_RK=$RK --motore $NOME_PC=$PC \
       --opzione "$NOME_SC:Persisted learning=Off" --opzione "$NOME_SC:Experience Book=false" \
       --posizioni data/outputWch2026_SF19/nuggets_top100.epd --riferimento $NOME_SF \
       --out $BASE/risultati/nps_2026
```

## 8. Analisi

```bash
cd docs/revisione2026
R=/home/sdp/ShashChessDev/tests/Tests2026/risultati
python statistiche_match.py --pgn $R/*_pool_wch/partite.pgn --aperture ../../data/outputWch2026_SF19/nuggets_pool.epd \
       --a ShashChess42 --b Stockfish19 --confronta $R/*_controllo_uho/partite.pgn \
       --etichetta "Match confermativo sul pool" --out $R/statistiche_pool_wch
python statistiche_match.py --pgn $R/*_test2026/partite.pgn \
       --aperture /home/sdp/ShashChessDev/tests/Tests2026/matches2026/Test2026.pgn \
       --a ShashChess42 --b Stockfish19 --etichetta "Replica Test2026" --out $R/statistiche_test2026
python statistiche_match.py --pgn $R/*_rr_top100/roundrobin.pgn --aperture ../../data/outputWch2026_SF19/nuggets_top100.epd \
       --a ShashChess42 --b Stockfish19 --ancora Stockfish19 --etichetta "Round robin Top-100" --out $R/statistiche_rr_top100
```

Le figure del paper si rigenerano con gli script di `docs/outputLTCWch/` (`generaDiagrammi.py`,
`crosstable_generator.py`, `tournament_visuals.py`) sui nuovi file. Alla fine si copiano in questa
cartella i PGN, i file .epd, i rapporti .md/.json e i file `macchina.txt`, `motori.txt` e
`comando*.txt` di ogni esperimento: sono la documentazione della Tabella 2.
