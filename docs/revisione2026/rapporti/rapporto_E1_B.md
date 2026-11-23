# Rapporto delle fasi E1 e B (22 novembre 2026)

## E1: controllo UHO

### E1: controllo UHO

Partite: 500 · posizioni: 250 · coppie a colori invertiti: 250 (partite non appaiate: 0)

Disegno incrociato (ogni coppia di motori sulle stesse posizioni): SI

#### Classifica

| Motore | Partite | V-P-S | Punti | Rating BT | IC 95% |
| --- | --- | --- | --- | --- | --- |
| ShashChess42.3 | 500 | 142-222-136 | 253.0 | 4.2 | [-6.3; 14.6] |
| Stockfish19 | 500 | 136-222-142 | 247.0 | 0.0 | [0.0; 0.0] |

#### Accoppiamenti (modello pentanomiale)

| A vs B | V-P-S di A | Punteggio A | Coppie 0/½/1/1½/2 | Elo A-B [IC 95%] | p | p cluster | McNemar p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ShashChess42.3 vs Stockfish19 | 142-222-136 | 50.6% | 0/26/192/32/0 | +4.2 [-6.2; +14.5] | 0.430 | 0.432 | 0.512 |

#### Posizioni

Partite decisive: 278 (55.6%). Vittorie della parte favorita: 278; della parte sfavorita: 0; patte: 222.
Posizioni sempre patte: 82; sempre decisive: 110.

#### Potenza (80%, alfa 0,05)

5 Elo: 2193 coppie, 10 Elo: 549 coppie, 15 Elo: 244 coppie, 20 Elo: 138 coppie, 30 Elo: 62 coppie

#### Interazione

Differenza Elo (ShashChess42.3 - Stockfish19) fra 'E1: controllo UHO' e 'confronto': +10.2 Elo, ES 6.6, z = 1.54, p = 0.125

#### Esecuzione

Dal 2026-11-21 11:56:46.057000 al 2026-11-22 01:24:31.226000 (13.5 h); massimo 47 partite simultanee; durata media 73.0 min.

#### Analisi S5 (E1)

| Coppia | Decisive | Quota [IC Wilson 95%] | Vittorie della parte sfavorita | Elo [IC 95%] | Elo normalizzato [IC 95%] |
|---|---|---|---|---|---|
| ShashChess42.3 - Stockfish19 | 278/500 | 55.6% [51.2; 59.9] | 0 | +4.2 [-6.2; +14.5] | +12 [-18; +43] |

Totale: 278/500 decisive (55.6% [51.2; 59.9]); vittorie della parte sfavorita: 0

| Motore | Da favorito: vinte | Conversione [IC 95%] | Da favorito: perse | Da sfavorito: perse | Quota perse [IC 95%] | Da sfavorito: vinte |
|---|---|---|---|---|---|---|
| ShashChess42.3 | 142/250 | 56.8% [50.6; 62.8] | 0 | 136/250 | 54.4% [48.2; 60.5] | 0 |
| Stockfish19 | 136/250 | 54.4% [48.2; 60.5] | 0 | 142/250 | 56.8% [50.6; 62.8] | 0 |

Spearman, quota di decisive per posizione contro Pwin della parte favorita (pre-partita): rho = 0.362, p = 0.0000
Esplorativo: contro Delta WDL rho = 0.080, p = 0.2087; contro la prima valutazione dei motori in partita rho = 0.567, p = 1.2e-22

| Pwin favorita | Posizioni | Partite | Decisive | Quota [IC 95%] |
|---|---|---|---|---|
| 0.69-0.72 | 25 | 50 | 14 | 28.0% [17.5; 41.7] |
| 0.72-0.75 | 72 | 144 | 60 | 41.7% [33.9; 49.8] |
| 0.75-0.78 | 72 | 144 | 90 | 62.5% [54.4; 70.0] |
| 0.78-0.82 | 81 | 162 | 114 | 70.4% [62.9; 76.9] |


### Controllo UHO (E1): nugget contro UHO di pari Pwin, stesse condizioni (25'+10", Stockfish 19 - ShashChess 42.3)

- Partite decisive: nugget (match C) 486/1040 (46.7%), UHO (E1) 278/500 (55.6%); differenza UHO - nugget +8.9 punti, IC 95% bootstrap per posizione [+0.8; +17.0]
- Pwin della parte favorita, media di 3 analisi: nugget 0.755 (mediana 0.758); UHO 0.766 (mediana 0.766; alla selezione 0.760); UHO fuori fascia con la media di 3 analisi: 32/250
- L della parte favorita nelle UHO (media di 3 analisi): media 0.0000; posizioni con L > 0: 10
- Delta WDL mediano (media di 3 analisi): nugget 0.028, UHO 0.100

| Modello (logistico, errori robusti per posizione) | Termine | OR [IC 95%] | p |
|---|---|---|---|
| grezzo | UHO | 1.43 [1.03; 1.98] | 0.0342 |
| pwin | UHO | 1.19 [0.85; 1.67] | 0.3154 |
| pwin | Pwin favorita (per 0,1) | 8.63 [4.72; 15.77] | 0.0000 |
| pwin_delta | UHO | 1.06 [0.72; 1.56] | 0.7607 |
| pwin_delta | Pwin favorita (per 0,1) | 8.68 [4.73; 15.91] | 0.0000 |
| pwin_delta | Delta WDL (per 0,1) | 1.11 [0.94; 1.31] | 0.2092 |

Nota: le posizioni UHO partono sempre con il Bianco favorito; nelle 500 partite 278 vittorie del Bianco, 222 patte, nessuna vittoria del Nero.

## B: Lc0 contro Stockfish

### Fase B: Lc0 (t3-512x15x16h, 10.000 nodi) contro Stockfish 19 (media di 3 analisi)

- Posizioni: 2321; nodi mediani per posizione: 10014
- Pwin della mossa migliore: rho di Spearman 0.750 (r di Pearson 0.954); Bland-Altman Lc0 - Stockfish: media -0.023, limiti al 95% [-0.172; +0.127]
- Delta WDL: rho di Spearman 0.693 (p = 0); mediana Stockfish 0.142, Lc0 0.045; Bland-Altman media -0.069, limiti [-0.232; +0.094]
- Mossa migliore di Lc0 fra le migliori delle 3 analisi di Stockfish: 85.5% (posizioni con mossa stabile per Stockfish, 1981: 85.9%)
- Fascia di Pwin (0,75 o 0,25 +/- 0,06): Stockfish 1274, Lc0 1248, entrambi 714; kappa 0.050
- Nugget (pre-registrato; Stockfish con L = 0, Lc0 senza): Stockfish 233, Lc0 737, entrambi 132 (confermati 56.7%); kappa 0.141 [IC 95% 0.106; 0.176]
- Nugget con lo stesso criterio per i due oracoli (fascia + Delta, senza L): Stockfish 260, entrambi 139; kappa 0.136 [0.099; 0.171]
- Probabilita' di vittoria della parte sfavorita secondo Lc0: nei 233 nugget di Stockfish mediana 0.070 (Q1 0.049, Q3 0.092; zero in 0); in tutte le candidate mediana 0.068
- S4, match C (130 posizioni del pool): nugget di consenso 69 posizioni, decisive 285/552 (51.6%), ShashChess - Stockfish -4.4 [-15.1; +6.3]; solo-Stockfish 61 posizioni, decisive 201/488 (41.2%), ShashChess - Stockfish -7.8 [-19.4; +3.7]

#### Contesto ed esplorativi

- Accordo di Stockfish con se stesso (tre analisi singole a 60 s delle stesse 2.321 posizioni): kappa sulla classificazione nugget 0,426, 0,461 e 0,438; kappa sulla fascia di Pwin 0,252, 0,270 e 0,356.
- Pwin della parte favorita (secondo Stockfish), Lc0 - Stockfish: media -0,048, DS 0,063, limiti al 95% [-0,172; +0,075]: Lc0 e' piu' prudente sul vantaggio.
- Lc0: nodi mediani 10.014, 79 nodi/s mediani per istanza, 126 s mediani per posizione; durata totale 1 h 47 min (47 istanze).
- S4 corretto per la Pwin della parte favorita (logistica, errori robusti per posizione): nugget di consenso contro solo-Stockfish OR 1,32 [0,80; 2,16], p = 0,28; i nugget di consenso hanno Pwin favorita media 0,760 contro 0,750.
