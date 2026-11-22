# Fase F: Pwin da 0,55 a 0,95 (22 novembre 2026)

Questo disegno è fissato prima di eseguire qualsiasi parte della fase.

## Scopo

Nel match C, in un'analisi esplorativa e non pre-registrata, la differenza ShashChess − Stockfish cresceva con la probabilità di vittoria della parte favorita, Pfav: +25 Elo per 0,1, IC 95% da +6 a +45, p = 0,010. L'andamento non si ritrovava in E4 (−17) né sulle aperture UHO (−8). La fase F lo mette alla prova con un test pre-registrato, su posizioni nuove e su un intervallo largo di Pfav. Risponde anche al punto 2 del revisore 2, che chiede il confronto per fasce di Pwin, comprese posizioni più equilibrate e più decise.

In parallelo F misura, da 0,55 a 0,95, come cambiano la quota di partite decise e la sicurezza della parte favorita.

## Posizioni

**Fasce di Pfav.** Pfav è la media di tre analisi di Stockfish 19 a 60 s. Le fasce sono quattro: [0,55; 0,65), [0,65; 0,75), [0,75; 0,85) e [0,85; 0,95). Con L_fav = 0, una Pfav vicina a 0,50 corrisponderebbe a una patta certa, per questo la prima fascia comincia da 0,55.

**Idonee.** Sono idonee tutte le posizioni con tre analisi:

- le 2.321 candidate (`posizioni/medie_3analisi.csv`);
- le 360 nuove candidate delle fasce esterne (`posizioni/fasce_candidate.csv`).

Le 360 nuove candidate le sceglie `preseleziona_fasce.py` (seme 2026) dal registro dell'estrazione. Hanno L_fav = 0 nella prima analisi e Pfav nelle fasce esterne. Ne vengono prese 180 per fascia, una per linea di partita, escluse le posizioni del pool e quelle sulla stessa linea.

**Classificazione.** Sulla media delle tre analisi una posizione appartiene a una fascia se L_fav medio = 0 e Pfav cade nella fascia. Non c'è nessuna condizione su ΔWDL. Sono escluse le posizioni del pool e quelle sulla stessa linea di una posizione del pool. Due posizioni stanno sulla stessa linea se le mosse che portano a una sono l'inizio di quelle che portano all'altra.

**Rianalisi.** `config_fasce_rianalisi.json` prevede due analisi a 60 s per ciascuna delle 360 nuove candidate. Le condizioni sono quelle dell'estrazione: stesso eseguibile di Stockfish 19, 4 thread, 2 GB di hash, Syzygy, 47 analisi in parallelo.

**Scelta.** La esegue `seleziona_fasce.py` con seme 2026 e 80 posizioni per fascia:

- le idonee di ogni fascia sono ordinate per FEN e mescolate con il seme;
- si prende a turno una posizione per fascia, scartando quelle sulla stessa linea di una già presa;
- se una fascia ha meno di 80 posizioni idonee, si usano tutte.

## Partite

ShashChess 42.3 contro Stockfish 19, con gli stessi eseguibili e le stesse condizioni del match C (`comune2026.sh`):

- cadenza 25'+10";
- 47 partite simultanee, 4 thread e 2 GB di hash per motore;
- una coppia a colori invertiti per posizione: 320 × 2 = 640 partite.

## Analisi

**Ipotesi primaria.** La pendenza del punteggio di coppia di ShashChess rispetto a Pfav è zero.

- Stima: minimi quadrati del punteggio di coppia (punti/2, da 0 a 1) su (Pfav − 0,75)/0,1.
- Errori standard robusti: HC1, perché c'è una coppia per posizione.
- Test bilaterale con α = 0,05.
- La pendenza si riporta anche in Elo per 0,1 di Pfav, convertita al punteggio del 50%.

**Analisi secondarie.**

- S1: Elo pentanomiale ShashChess − Stockfish per fascia e su tutte le posizioni, con IC 95%.
- S2: quota di partite decise per fascia, con intervalli di Wilson, e regressione logistica delle partite decise su Pfav. Si riporta l'odds ratio per 0,1, con errori robusti per posizione.
- S3: partite vinte dalla parte sfavorita, per fascia.
- S4: correlazione di Spearman fra la quota di partite decise per posizione e ΔWDL, a scopo descrittivo.

**Analisi esplorativa.** Il confronto per zona di Shashin della parte favorita.

## Potenza

Con la varianza del match C (errore standard della pendenza 9,9 Elo per 0,1, deviazione standard di Pfav 0,032) e Pfav distribuita fra 0,55 e 0,95 (deviazione standard circa 0,115), l'errore standard atteso della pendenza su 320 posizioni è circa 3,5 Elo per 0,1. La differenza minima rilevabile all'80% è quindi circa 10 Elo per 0,1. La stima esplorativa di C era +25.

## Ordine

`coda_lunedi.sh` parte dopo la fine di `coda_domenica.sh` (E5) ed esegue rianalisi, scelta e match. Non sono previste analisi intermedie né arresti anticipati. Durata prevista: circa 20 minuti di rianalisi e circa 17 ore di match.

## File della fase

- `preseleziona_fasce.py`
- `seleziona_fasce.py`
- `posizioni/fasce_candidate.csv`
- `config_fasce_rianalisi.json` (nella radice del repository)
- `coda_lunedi.sh`
