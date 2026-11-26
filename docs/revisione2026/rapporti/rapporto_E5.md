# Rapporto della fase E5 (22 novembre 2026)

Disegno: PREREGISTRAZIONE_B_E5.md (commit 7ca61d3). 130 posizioni del pool robusto x 1 ciclo x 2 colori = 260 partite a 60'+30",
Stockfish 19 contro ShashChess 42.3, stessi eseguibili e condizioni del match C (4 thread, 2 GB di hash, Syzygy a 6 pezzi).
Analisi pre-registrate: Elo pentanomiale, interazione con C (25'+10") e con E4 (60"+0,6"), S5. Nessuna analisi intermedia, nessun arresto anticipato.

## E5: pool robusto a 60'+30"

Partite: 260 · posizioni: 130 · coppie a colori invertiti: 130 (partite non appaiate: 0)

Disegno incrociato (ogni coppia di motori sulle stesse posizioni): SI

### Classifica

| Motore | Partite | V-P-S | Punti | Rating BT | IC 95% |
| --- | --- | --- | --- | --- | --- |
| Stockfish19 | 260 | 64-139-57 | 133.5 | 0.0 | [0.0; 0.0] |
| ShashChess42.3 | 260 | 57-139-64 | 126.5 | -9.4 | [-21.4; 4.0] |

### Accoppiamenti (modello pentanomiale)

| A vs B | V-P-S di A | Punteggio A | Coppie 0/½/1/1½/2 | Elo A-B [IC 95%] | p | p cluster | McNemar p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ShashChess42.3 vs Stockfish19 | 57-139-64 | 48.7% | 0/16/105/9/0 | -9.4 [-22.4; +3.6] | 0.158 | 0.162 | 0.230 |

### Posizioni

Partite decisive: 121 (46.5%). Vittorie della parte favorita: 121; della parte sfavorita: 0; patte: 139.
Posizioni sempre patte: 57; sempre decisive: 48.

### Potenza (80%, alfa 0,05)

5 Elo: 1795 coppie, 10 Elo: 449 coppie, 15 Elo: 200 coppie, 20 Elo: 113 coppie, 30 Elo: 51 coppie

### Interazione (pre-registrata)

Differenza Elo (ShashChess42.3 - Stockfish19) fra 'E5: pool robusto a 60'+30"' e 'C (25'+10")': -3.3 Elo, ES 7.7, z = -0.43, p = 0.666

Differenza Elo (ShashChess42.3 - Stockfish19) fra 'E5' e 'E4 (60"+0.6")': -8.4 Elo, ES 8.3, z = -1.01, p = 0.313

### Esecuzione

Dal 2026-11-22 03:24:07.670000 al 2026-11-22 21:47:37.639000 (18.4 h); massimo 47 partite simultanee; durata media 180.5 min.

## S5: partite decisive

| Coppia | Decisive | Quota [IC Wilson 95%] | Vittorie della parte sfavorita | Elo [IC 95%] | Elo normalizzato [IC 95%] |
|---|---|---|---|---|---|
| ShashChess42.3 - Stockfish19 | 121/260 | 46.5% [40.6; 52.6] | 0 | -9.4 [-22.4; +3.6] | -30 [-73; +12] |

Totale: 121/260 decisive (46.5% [40.6; 52.6]); vittorie della parte sfavorita: 0

| Motore | Da favorito: vinte | Conversione [IC 95%] | Da favorito: perse | Da sfavorito: perse | Quota perse [IC 95%] | Da sfavorito: vinte |
|---|---|---|---|---|---|---|
| ShashChess42.3 | 57/130 | 43.8% [35.6; 52.4] | 0 | 64/130 | 49.2% [40.8; 57.7] | 0 |
| Stockfish19 | 64/130 | 49.2% [40.8; 57.7] | 0 | 57/130 | 43.8% [35.6; 52.4] | 0 |

Spearman, quota di decisive per posizione contro Pwin della parte favorita (pre-partita): rho = 0.276, p = 0.0015
Esplorativo: contro Delta WDL rho = -0.081, p = 0.3615; contro la prima valutazione dei motori in partita rho = 0.577, p = 6.9e-13

| Pwin favorita | Posizioni | Partite | Decisive | Quota [IC 95%] |
|---|---|---|---|---|
| 0.69-0.72 | 21 | 42 | 13 | 31.0% [19.1; 46.0] |
| 0.72-0.75 | 34 | 68 | 31 | 45.6% [34.3; 57.3] |
| 0.75-0.78 | 39 | 78 | 30 | 38.5% [28.4; 49.6] |
| 0.78-0.82 | 36 | 72 | 47 | 65.3% [53.8; 75.2] |

Posizioni sempre patte (57): nugget004, nugget005, nugget009, nugget013, nugget014, nugget021, nugget023, nugget027, nugget028, nugget031, nugget033, nugget034, nugget035, nugget036, nugget037, nugget038, nugget039, nugget041, nugget051, nugget052, nugget053, nugget056, nugget058, nugget060, nugget064, nugget067, nugget069, nugget070, nugget071, nugget072, nugget073, nugget074, nugget076, nugget077, nugget078, nugget081, nugget082, nugget084, nugget087, nugget089, nugget092, nugget093, nugget095, nugget099, nugget102, nugget103, nugget105, nugget106, nugget112, nugget113, nugget119, nugget123, nugget124, nugget125, nugget126, nugget127, nugget129
Posizioni sempre decisive (48): nugget002, nugget003, nugget006, nugget007, nugget010, nugget011, nugget015, nugget017, nugget018, nugget019, nugget020, nugget024, nugget025, nugget026, nugget029, nugget030, nugget032, nugget042, nugget043, nugget044, nugget046, nugget047, nugget048, nugget050, nugget054, nugget062, nugget068, nugget075, nugget080, nugget083, nugget085, nugget086, nugget090, nugget096, nugget097, nugget100, nugget101, nugget104, nugget108, nugget111, nugget114, nugget115, nugget116, nugget117, nugget118, nugget120, nugget121, nugget122

## ShashChess - Stockfish per fascia di Pwin della parte favorita (esplorativa, non pre-registrata)

| Fase | 0.69-0.72 | 0.72-0.75 | 0.75-0.78 | 0.78-0.82 | Andamento per 0,1 |
|---|---|---|---|---|---|
| E5 | -24.9 [-60.1; +9.9] (21) | -15.3 [-45.2; +14.3] (34) | -0.0 [-24.7; +24.7] (39) | -4.8 [-21.2; +11.5] (36) | +32.3 [-6.6; +71.2], p = 0.104 |

## Sintesi

- Differenza ShashChess - Stockfish: -9,4 Elo [-22,4; +3,6], p = 0,16 (cluster 0,16; McNemar 9 contro 16, p = 0,23). L'intervallo (+/-13 Elo) e' piu' stretto dei +/-16 previsti.
- Interazione con C: -3,3 Elo (ES 7,7), p = 0,67; con E4: -8,4 Elo (ES 8,3), p = 0,31. Nessun effetto della cadenza fra 60"+0,6" e 60'+30".
- Partite decisive 46,5% [40,6; 52,6]; la parte sfavorita non ha mai vinto. La quota di decisive segue Pwin (rho 0,28, p = 0,002) e non Delta WDL (rho -0,08, p = 0,36).
