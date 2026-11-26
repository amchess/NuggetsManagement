# Verifiche prima del nuovo invio (novembre 2026)

Questi script rispondono alle domande tecniche ricevute sul manoscritto ICG-26-0040 prima del nuovo
invio. Leggono soltanto file gia' presenti nel commit `bd689c8` (registri, posizioni, PGN) e scrivono
i rapporti in `docs/revisione2026/rapporti/verifiche_*`. Si lanciano dalla radice del repository e
usano solo la libreria standard di Python.

| Script | Domande | Serve un motore | Rapporto |
|---|---|---|---|
| `registri.py` | 1, 3, 4 | no | `verifiche_registri.json` |
| `esiti_partite.py` | 5, 6 | no | `verifiche_esiti.json`, `.md` |
| `linee_pool.py` | 4 | si' | `verifiche_linee_pool.json` |
| `patte_punteggio.py` | 6 | si' | `verifiche_patte_punteggio.json`, `.md` |

`scacchi_min.py` contiene le funzioni comuni: lettura dei file `.gz`, SAN di una mossa, motore UCI.
I due script con il motore chiedono a quest'ultimo le mosse legali (`go perft 1`) e la FEN (`d`):
vanno bene Stockfish e i motori derivati.

```
python3 docs/revisione2026/verifiche/registri.py
python3 docs/revisione2026/verifiche/esiti_partite.py
python3 docs/revisione2026/verifiche/linee_pool.py --motore /percorso/stockfish
python3 docs/revisione2026/verifiche/patte_punteggio.py --motore /percorso/stockfish \
    --ms 60000 --threads 4 --hash 2048 --syzygy /percorso/syzygy --processi 47
```

## Risultati

**Domanda 1, medie delle tre analisi.** Le medie sono per rango delle linee MultiPV
(`pool_robusto.py`), non per mossa. In 142 delle 6.963 analisi singole dei candidati (2,0%) la
seconda linea ha una Pwin piu' alta della prima, sempre con profondita' diverse delle due linee.
Per questo in 125 posizioni la media dei Delta differisce dal Delta delle medie; con il secondo
ordine le pepite robuste sarebbero 241 invece di 233. La mossa migliore e' la stessa nelle tre
analisi in 1.981 candidati su 2.321 e in 56 posizioni del pool su 130.

**Domanda 3, filtri.** Prima analisi: 85.491 FEN distinte (1.303 sono la stessa posizione con
contatori diversi), 391 scartate per meno di due mosse legali, 888 non pepite senza WDL per un matto
nella prima linea, 287 pepite. I candidati sono tutte e sole le 2.321 posizioni con
|Pfav − 0,75| ≤ 0,10 e comprendono le 287 pepite.

**Domanda 4, deduplicazione.** La regola di `genera_pgn.py` (Delta crescente, poi distanza da 0,75,
poi FEN; si scarta una posizione la cui linea e' prefisso di una gia' tenuta o viceversa) riproduce
il pool di 130. Delle 103 pepite robuste scartate, quella tenuta al loro posto viene dopo nella
partita in 51 casi e prima in 52. Le 130 linee rigiocate finiscono ciascuna nella sua FEN; nessuna
passa per un'altra posizione del pool e non ci sono doppioni a meno dei contatori.

**Domande 5 e 6, partite.** 4.680 partite su 700 posizioni distinte, nessuna vinta dalla parte
sfavorita. Limite superiore unilaterale al 95% sul suo tasso di vittoria: 0,064% per partita con
partite indipendenti, 0,43% con le 700 posizioni come unita' (0,20–0,28% con una correlazione
intraclasse di 0,20–0,44). Le partite aggiudicate sono 4.488 (95,9%): 2.103 vinte con la regola dei
10 pedoni, 1.451 patte per punteggio, 68 vinte e 865 patte con le tablebase, 1 al limite di 200
mosse; nessuna partita e' finita con un matto.

**Domanda 6, patte per punteggio.** Prova preliminare, non con l'oracolo: ShashChess 43-dev (amchess/ShashChess, commit `510dec5`), 500 ms, 1 thread, 64 MB. Valutazione assoluta mediana 16 cp; almeno 1 pedone in 12 posizioni, almeno 2 in una. La probabilita' di vittoria della parte sfavorita non supera mai l'1,1%; quella della favorita supera il 10% in 165 posizioni. Prese alla lettera, queste probabilita' darebbero circa 65 vittorie in piu' della parte favorita e circa 3 della sfavorita: la quota di decisive passerebbe dal 46,4% al 47,8% (da +0,8 a +1,8 punti a seconda della fase). La verifica definitiva e' la stessa con l'oracolo, con il comando indicato sopra.
