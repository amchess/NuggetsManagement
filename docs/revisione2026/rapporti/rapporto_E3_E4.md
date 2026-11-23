# Rapporto delle fasi E3 ed E4 (21 novembre 2026)

## E3

### NPS sotto carico (47 istanze x 4 thread, 5000 ms per posizione, 10 posizioni, 5 ripetizioni)

| Motore | NPS medio per istanza | DS fra ripetizioni | IC 95% | CV % | Profondita' mediana | Rapporto su Stockfish19 [IC 95%] |
|---|---|---|---|---|---|---|
| Stockfish19 | 3,505,284 | 58,756 | [3,433,564; 3,577,004] | 1.7 | 26.0 | 1 |
| ShashChess42.3 | 3,378,914 | 32,256 | [3,339,541; 3,418,288] | 1.0 | 26.0 | 0.964 [0.947; 0.981] |
| Reckless0.9.0 | 4,071,693 | 7,414 | [4,062,643; 4,080,743] | 0.2 | 24.0 | 1.162 [1.139; 1.184] |
| Triumviratus8.1 | 3,211,440 | 32,221 | [3,172,109; 3,250,771] | 1.0 | 28.0 | 0.916 [0.896; 0.936] |

Nota: gli NPS di motori diversi non sono confrontabili (ogni motore conta i nodi a modo suo); il confronto significativo e' ShashChess-Stockfish, che condividono il codice di base.

## E4

### E4: pool robusto a 60+0.6

Partite: 1040 · posizioni: 130 · coppie a colori invertiti: 520 (partite non appaiate: 0)

Disegno incrociato (ogni coppia di motori sulle stesse posizioni): SI

#### Classifica

| Motore | Partite | V-P-S | Punti | Rating BT | IC 95% |
| --- | --- | --- | --- | --- | --- |
| Stockfish19 | 1040 | 256-531-253 | 521.5 | 0.0 | [0.0; 0.0] |
| ShashChess42.3 | 1040 | 253-531-256 | 518.5 | -1.0 | [-10.7; 8.4] |

#### Accoppiamenti (modello pentanomiale)

| A vs B | V-P-S di A | Punteggio A | Coppie 0/½/1/1½/2 | Elo A-B [IC 95%] | p | p cluster | McNemar p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ShashChess42.3 vs Stockfish19 | 253-531-256 | 49.9% | 0/112/299/109/0 | -1.0 [-10.7; +8.7] | 0.840 | 0.840 | 0.893 |

#### Posizioni

Partite decisive: 509 (48.9%). Vittorie della parte favorita: 509; della parte sfavorita: 0; patte: 531.
Posizioni sempre patte: 8; sempre decisive: 4.

#### Potenza (80%, alfa 0,05)

5 Elo: 4027 coppie, 10 Elo: 1008 coppie, 15 Elo: 448 coppie, 20 Elo: 253 coppie, 30 Elo: 113 coppie

#### Interazione

Differenza Elo (ShashChess42.3 - Stockfish19) fra 'E4: pool robusto a 60+0.6' e 'confronto': +5.0 Elo, ES 6.4, z = 0.79, p = 0.432

#### Esecuzione

Dal 2026-11-21 10:45:17.821000 al 2026-11-21 11:56:38.514000 (1.2 h); massimo 47 partite simultanee; durata media 3.1 min.

#### Analisi S5 (E4)

| Coppia | Decisive | Quota [IC Wilson 95%] | Vittorie della parte sfavorita | Elo [IC 95%] | Elo normalizzato [IC 95%] |
|---|---|---|---|---|---|
| ShashChess42.3 - Stockfish19 | 509/1040 | 48.9% [45.9; 52.0] | 0 | -1.0 [-10.7; +8.7] | -2 [-23; +19] |

Totale: 509/1040 decisive (48.9% [45.9; 52.0]); vittorie della parte sfavorita: 0

| Motore | Da favorito: vinte | Conversione [IC 95%] | Da favorito: perse | Da sfavorito: perse | Quota perse [IC 95%] | Da sfavorito: vinte |
|---|---|---|---|---|---|---|
| ShashChess42.3 | 253/520 | 48.7% [44.4; 52.9] | 0 | 256/520 | 49.2% [45.0; 53.5] | 0 |
| Stockfish19 | 256/520 | 49.2% [45.0; 53.5] | 0 | 253/520 | 48.7% [44.4; 52.9] | 0 |

Spearman, quota di decisive per posizione contro Pwin della parte favorita (pre-partita): rho = 0.399, p = 0.0000
Esplorativo: contro Delta WDL rho = 0.083, p = 0.3468; contro la prima valutazione dei motori in partita rho = 0.220, p = 0.012

| Pwin favorita | Posizioni | Partite | Decisive | Quota [IC 95%] |
|---|---|---|---|---|
| 0.69-0.72 | 21 | 168 | 40 | 23.8% [18.0; 30.8] |
| 0.72-0.75 | 34 | 272 | 121 | 44.5% [38.7; 50.4] |
| 0.75-0.78 | 39 | 312 | 171 | 54.8% [49.3; 60.2] |
| 0.78-0.82 | 36 | 288 | 177 | 61.5% [55.7; 66.9] |

Posizioni sempre patte (8): nugget001, nugget004, nugget033, nugget087, nugget089, nugget102, nugget109, nugget113
Posizioni sempre decisive (4): nugget024, nugget026, nugget034, nugget072

#### Analisi S5 sul match C (stesso script, per confronto)

| Coppia | Decisive | Quota [IC Wilson 95%] | Vittorie della parte sfavorita | Elo [IC 95%] | Elo normalizzato [IC 95%] |
|---|---|---|---|---|---|
| ShashChess42.3 - Stockfish19 | 486/1040 | 46.7% [43.7; 49.8] | 0 | -6.0 [-13.9; +1.8] | -16 [-37; +5] |

Totale: 486/1040 decisive (46.7% [43.7; 49.8]); vittorie della parte sfavorita: 0

| Motore | Da favorito: vinte | Conversione [IC 95%] | Da favorito: perse | Da sfavorito: perse | Quota perse [IC 95%] | Da sfavorito: vinte |
|---|---|---|---|---|---|---|
| ShashChess42.3 | 234/520 | 45.0% [40.8; 49.3] | 0 | 252/520 | 48.5% [44.2; 52.8] | 0 |
| Stockfish19 | 252/520 | 48.5% [44.2; 52.8] | 0 | 234/520 | 45.0% [40.8; 49.3] | 0 |

Spearman, quota di decisive per posizione contro Pwin della parte favorita (pre-partita): rho = 0.373, p = 0.0000
Esplorativo: contro Delta WDL rho = -0.047, p = 0.5970; contro la prima valutazione dei motori in partita rho = 0.748, p = 1.7e-24

| Pwin favorita | Posizioni | Partite | Decisive | Quota [IC 95%] |
|---|---|---|---|---|
| 0.69-0.72 | 21 | 168 | 40 | 23.8% [18.0; 30.8] |
| 0.72-0.75 | 34 | 272 | 120 | 44.1% [38.3; 50.1] |
| 0.75-0.78 | 39 | 312 | 140 | 44.9% [39.4; 50.4] |
| 0.78-0.82 | 36 | 288 | 186 | 64.6% [58.9; 69.9] |

Posizioni sempre patte (25): nugget001, nugget004, nugget005, nugget013, nugget027, nugget031, nugget035, nugget041, nugget056, nugget060, nugget067, nugget071, nugget072, nugget078, nugget086, nugget089, nugget094, nugget095, nugget102, nugget105, nugget113, nugget119, nugget125, nugget127, nugget129
Posizioni sempre decisive (19): nugget007, nugget010, nugget020, nugget026, nugget030, nugget042, nugget046, nugget047, nugget050, nugget062, nugget080, nugget091, nugget096, nugget100, nugget104, nugget115, nugget117, nugget118, nugget120

#### Coerenza degli esiti per posizione (esplorativo)

Correlazione intraclasse dell'esito decisivo/patta fra le 8 partite di ogni posizione: 0,443 a 25'+10" (match C) contro 0,198 a 60"+0,6" (E4).
