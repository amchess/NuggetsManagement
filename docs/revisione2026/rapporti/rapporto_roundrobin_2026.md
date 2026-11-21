# Round robin 2026 sulle Top-100 robuste

Partite: 1200 · posizioni: 100 · coppie a colori invertiti: 600 (partite non appaiate: 0)

Disegno incrociato (ogni coppia di motori sulle stesse posizioni): SI

## Classifica

| Motore | Partite | V-P-S | Punti | Rating BT | IC 95% |
| --- | --- | --- | --- | --- | --- |
| ShashChess42.3 | 600 | 158-336-106 | 326.0 | 1.3 | [-10.1; 13.2] |
| Stockfish19 | 600 | 162-325-113 | 324.5 | 0.0 | [0.0; 0.0] |
| Triumviratus8.1 | 600 | 134-351-115 | 309.5 | -13.2 | [-26.8; 0.0] |
| Reckless0.9.0 | 600 | 68-344-188 | 240.0 | -74.4 | [-89.4; -59.6] |

## Accoppiamenti (modello pentanomiale)

| A vs B | V-P-S di A | Punteggio A | Coppie 0/½/1/1½/2 | Elo A-B [IC 95%] | p | p cluster | McNemar p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Reckless0.9.0 vs ShashChess42.3 | 23-113-64 | 39.8% | 0/42/57/1/0 | -72.2 [-90.7; -54.2] | < 0.001 | < 0.001 | < 0.001 |
| Reckless0.9.0 vs Stockfish19 | 25-109-66 | 39.8% | 0/46/49/5/0 | -72.2 [-93.3; -51.7] | < 0.001 | < 0.001 | < 0.001 |
| Reckless0.9.0 vs Triumviratus8.1 | 20-122-58 | 40.5% | 0/41/56/3/0 | -66.8 [-86.3; -47.8] | < 0.001 | < 0.001 | < 0.001 |
| ShashChess42.3 vs Stockfish19 | 48-105-47 | 50.2% | 0/11/77/12/0 | +1.7 [-14.6; +18.1] | 0.835 | 0.836 | 1.000 |
| ShashChess42.3 vs Triumviratus8.1 | 46-118-36 | 52.5% | 0/11/68/21/0 | +17.4 [-1.6; +36.5] | 0.072 | 0.077 | 0.110 |
| Stockfish19 vs Triumviratus8.1 | 49-111-40 | 52.2% | 0/9/73/18/0 | +15.6 [-1.8; +33.2] | 0.079 | 0.083 | 0.122 |

## Posizioni

Partite decisive: 522 (43.5%). Vittorie della parte favorita: 522; della parte sfavorita: 0; patte: 678.
Posizioni sempre patte: 10; sempre decisive: 4.

## Esecuzione

Dal 2026-11-20 00:14:32.383000 al 2026-11-21 09:02:11.991000 (32.8 h); massimo 47 partite simultanee; durata media 68.8 min.

## Analisi pre-registrate aggiuntive (S2, S5)

| Coppia | Decisive | Quota [IC Wilson 95%] | Vittorie della parte sfavorita | Elo [IC 95%] | Elo normalizzato [IC 95%] |
|---|---|---|---|---|---|
| Reckless0.9.0 - ShashChess42.3 | 87/200 | 43.5% [36.8; 50.4] | 0 | -72.2 [-90.7; -54.2] | -197 [-245; -149] |
| Reckless0.9.0 - Stockfish19 | 91/200 | 45.5% [38.7; 52.4] | 0 | -72.2 [-93.3; -51.7] | -172 [-220; -124] |
| Reckless0.9.0 - Triumviratus8.1 | 78/200 | 39.0% [32.5; 45.9] | 0 | -66.8 [-86.3; -47.8] | -172 [-220; -124] |
| ShashChess42.3 - Stockfish19 | 95/200 | 47.5% [40.7; 54.4] | 0 | +1.7 [-14.6; +18.1] | +5 [-43; +53] |
| ShashChess42.3 - Triumviratus8.1 | 82/200 | 41.0% [34.4; 47.9] | 0 | +17.4 [-1.6; +36.5] | +44 [-4; +92] |
| Stockfish19 - Triumviratus8.1 | 89/200 | 44.5% [37.8; 51.4] | 0 | +15.6 [-1.8; +33.2] | +43 [-5; +91] |

Totale: 522/1200 decisive (43.5% [40.7; 46.3]); vittorie della parte sfavorita: 0

| Motore | Da favorito: vinte | Conversione [IC 95%] | Da favorito: perse | Da sfavorito: perse | Quota perse [IC 95%] | Da sfavorito: vinte |
|---|---|---|---|---|---|---|
| Reckless0.9.0 | 68/300 | 22.7% [18.3; 27.7] | 0 | 188/300 | 62.7% [57.1; 67.9] | 0 |
| ShashChess42.3 | 158/300 | 52.7% [47.0; 58.2] | 0 | 106/300 | 35.3% [30.1; 40.9] | 0 |
| Stockfish19 | 162/300 | 54.0% [48.3; 59.6] | 0 | 113/300 | 37.7% [32.4; 43.3] | 0 |
| Triumviratus8.1 | 134/300 | 44.7% [39.1; 50.3] | 0 | 115/300 | 38.3% [33.0; 43.9] | 0 |

Spearman, quota di decisive per posizione contro Pwin della parte favorita (pre-partita): rho = 0.422, p = 0.0000
Esplorativo: contro Delta WDL rho = -0.073, p = 0.4702; contro la prima valutazione dei motori in partita rho = 0.623, p = 4.3e-12

| Pwin favorita | Posizioni | Partite | Decisive | Quota [IC 95%] |
|---|---|---|---|---|
| 0.69-0.72 | 19 | 228 | 58 | 25.4% [20.2; 31.5] |
| 0.72-0.75 | 24 | 288 | 116 | 40.3% [34.8; 46.0] |
| 0.75-0.78 | 30 | 360 | 142 | 39.4% [34.5; 44.6] |
| 0.78-0.82 | 27 | 324 | 206 | 63.6% [58.2; 68.6] |

Posizioni sempre patte (10): nugget005, nugget023, nugget027, nugget031, nugget056, nugget067, nugget071, nugget072, nugget086, nugget089
Posizioni sempre decisive (4): nugget042, nugget046, nugget091, nugget100
