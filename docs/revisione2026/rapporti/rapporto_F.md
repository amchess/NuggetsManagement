# Rapporto della fase F (23 novembre 2026)

Disegno: PREREGISTRAZIONE_F.md (commit 47d6a0b). 320 posizioni nuove in quattro fasce di Pfav (0,55-0,65, 0,65-0,75,
0,75-0,85 e 0,85-0,95; 80 per fascia, una per linea di partita, escluse le posizioni del pool e le loro linee) x 1 coppia a
colori invertiti = 640 partite a 25'+10", Stockfish 19 contro ShashChess 42.3, stessi eseguibili e condizioni del match C
(4 thread, 2 GB di hash, Syzygy a 6 pezzi). Le 360 nuove candidate delle fasce esterne sono state analizzate altre due
volte (`registri/fasce_rianalisi01-02`); le posizioni scelte sono in `posizioni/fasce_320.{csv,epd,md}`.
Ipotesi primaria: pendenza nulla del punteggio di coppia di ShashChess su Pfav. Nessuna analisi intermedia, nessun arresto anticipato.

Comandi (dalla cartella docs/revisione2026, dopo `gunzip -k risultati/*/*.pgn.gz`):

```bash
F=risultati/20261122_2211_fasce_tc1500
python analisi_f.py --f $F --posizioni posizioni/fasce_320.csv --out rapporti/statistiche_f
python statistiche_match.py --pgn $F/partite.pgn --aperture $F/fasce_320.epd --a ShashChess42.3 --b Stockfish19 \
  --ancora Stockfish19 --etichetta "F: Pfav da 0,55 a 0,95, 25'+10\"" --out rapporti/statistiche_match_f
python statistiche_rr_extra.py --pgn $F/partite.pgn --aperture $F/fasce_320.epd --out rapporti/s5_f
python confronto_f_nugget.py --c risultati/20261118_2057_pool_robusto --f $F --pool posizioni/nuggets_pool_robusto.csv \
  --posizioni-f posizioni/fasce_320.csv --out rapporti/confronto_f_nugget
```

## Analisi pre-registrate (analisi_f.py)

Partite 640, coppie 320 (posizioni previste 320, partite spaiate 0).

### Ipotesi primaria (pre-registrata)

Pendenza del punteggio di coppia di ShashChess su (Pfav - 0,75)/0,1: -0.0006 (ES HC1 0.0021), z = -0.27, p = 0.787.
In Elo per 0,1 di Pfav: -0.4 [-3.2; +2.4]. Deviazione standard di Pfav: 0.111.

### S1: Elo pentanomiale ShashChess - Stockfish

| Fascia | Coppie | 0 / ½ / 1 / 1½ / 2 | Elo [IC 95%] | p |
|---|---|---|---|---|
| 0.55-0.65 | 80 | 0 / 0 / 79 / 1 / 0 | +2.2 [-2.1; +6.4] | 0.314 |
| 0.65-0.75 | 80 | 0 / 5 / 74 / 1 / 0 | -8.7 [-19.0; +1.6] | 0.097 |
| 0.75-0.85 | 80 | 0 / 6 / 64 / 10 / 0 | +8.7 [-8.2; +25.6] | 0.314 |
| 0.85-0.95 | 80 | 0 / 2 / 78 / 0 / 0 | -4.3 [-10.3; +1.6] | 0.152 |
| totale | 320 | 0 / 13 / 295 / 12 / 0 | -0.5 [-5.9; +4.8] | 0.841 |

### S2: partite decise

| Fascia | Partite | Decise | % [Wilson 95%] |
|---|---|---|---|
| 0.55-0.65 | 160 | 5 | 3.1 [1.3; 7.1] |
| 0.65-0.75 | 160 | 18 | 11.2 [7.2; 17.1] |
| 0.75-0.85 | 160 | 88 | 55.0 [47.3; 62.5] |
| 0.85-0.95 | 160 | 144 | 90.0 [84.4; 93.8] |
| totale | 640 | 255 | 39.8 [36.1; 43.7] |

Logistica sulle 640 partite (320 posizioni, errori per posizione): odds ratio per 0,1 di Pfav 8.92 [5.67; 14.02], p = 2.8e-21.

### S3: sicurezza della parte favorita

| Fascia | Partite | Vinte dalla sfavorita [Wilson 95%] | di cui SC / SF | Conversioni da favorita SC | SF |
|---|---|---|---|---|---|
| 0.55-0.65 | 160 | 0 (0.0% [0.0; 2.3]) | 0 / 0 | 3/80 (3.8%) | 2/80 (2.5%) |
| 0.65-0.75 | 160 | 0 (0.0% [0.0; 2.3]) | 0 / 0 | 7/80 (8.8%) | 11/80 (13.8%) |
| 0.75-0.85 | 160 | 0 (0.0% [0.0; 2.3]) | 0 / 0 | 46/80 (57.5%) | 42/80 (52.5%) |
| 0.85-0.95 | 160 | 0 (0.0% [0.0; 2.3]) | 0 / 0 | 71/80 (88.8%) | 73/80 (91.2%) |
| totale | 640 | 0 (0.0% [0.0; 0.6]) | 0 / 0 | 127/320 (39.7%) | 128/320 (40.0%) |

### S4 (descrittiva)

Spearman fra quota di partite decise della posizione e Delta WDL: rho = -0.08 (p = 0.18); con Pfav: rho = +0.74 (p = 5e-56). Posizioni sempre patte 180, sempre decise 115 su 320.

### Esplorativa: zona di Shashin della parte favorita

| Zona | Coppie | Elo [IC 95%] | p |
|---|---|---|---|
| Capablanca-Tal | 163 | -2.1 [-8.0; +3.8] | 0.479 |
| Low Tal | 29 | +6.0 [-25.0; +37.1] | 0.705 |
| Middle-Low Tal | 46 | +11.3 [-8.0; +30.7] | 0.250 |
| Middle Tal | 40 | -8.7 [-20.4; +3.0] | 0.147 |
| Middle-High Tal | 42 | -4.1 [-12.2; +3.9] | 0.311 |

## Match (statistiche_match.py)

Partite: 640 · posizioni: 320 · coppie a colori invertiti: 320 (partite non appaiate: 0)

Disegno incrociato (ogni coppia di motori sulle stesse posizioni): SI

### Classifica

| Motore | Partite | V-P-S | Punti | Rating BT | IC 95% |
| --- | --- | --- | --- | --- | --- |
| Stockfish19 | 640 | 128-385-127 | 320.5 | 0.0 | [0.0; 0.0] |
| ShashChess42.3 | 640 | 127-385-128 | 319.5 | -0.5 | [-6.0; 4.9] |

### Accoppiamenti (modello pentanomiale)

| A vs B | V-P-S di A | Punteggio A | Coppie 0/½/1/1½/2 | Elo A-B [IC 95%] | p | p cluster | McNemar p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ShashChess42.3 vs Stockfish19 | 127-385-128 | 49.9% | 0/13/295/12/0 | -0.5 [-5.9; +4.8] | 0.841 | 0.842 | 1.000 |

### Posizioni

Partite decisive: 255 (39.8%). Vittorie della parte favorita: 255; della parte sfavorita: 0; patte: 385.
Posizioni sempre patte: 180; sempre decisive: 115.

### Potenza (80%, alfa 0,05)

5 Elo: 741 coppie, 10 Elo: 186 coppie, 15 Elo: 83 coppie, 20 Elo: 47 coppie, 30 Elo: 21 coppie

### Esecuzione

Dal 2026-11-22 22:11:21.999000 al 2026-11-23 13:38:04.038000 (15.4 h); massimo 47 partite simultanee; durata media 64.3 min.

## Conversioni e correlazioni (statistiche_rr_extra.py)

| Coppia | Decisive | Quota [IC Wilson 95%] | Vittorie della parte sfavorita | Elo [IC 95%] | Elo normalizzato [IC 95%] |
|---|---|---|---|---|---|
| ShashChess42.3 - Stockfish19 | 255/640 | 39.8% [36.1; 43.7] | 0 | -0.5 [-5.9; +4.8] | -3 [-30; +24] |

Totale: 255/640 decisive (39.8% [36.1; 43.7]); vittorie della parte sfavorita: 0

| Motore | Da favorito: vinte | Conversione [IC 95%] | Da favorito: perse | Da sfavorito: perse | Quota perse [IC 95%] | Da sfavorito: vinte |
|---|---|---|---|---|---|---|
| ShashChess42.3 | 127/320 | 39.7% [34.5; 45.1] | 0 | 128/320 | 40.0% [34.8; 45.5] | 0 |
| Stockfish19 | 128/320 | 40.0% [34.8; 45.5] | 0 | 127/320 | 39.7% [34.5; 45.1] | 0 |

Spearman, quota di decisive per posizione contro Pwin della parte favorita (pre-partita): rho = 0.737, p = 0.0000
Esplorativo: contro Delta WDL rho = -0.075, p = 0.1791; contro la prima valutazione dei motori in partita rho = 0.805, p = 4.2e-74

Le fasce di Pfav di F sono in S2 qui sopra (la tabella per fascia di statistiche_rr_extra.py usa le fasce dei nugget, 0,69-0,82, e non e' riportata).

Posizioni sempre patte (180): fascia001, fascia002, fascia005, fascia006, fascia007, fascia009, fascia010, fascia013, fascia014, fascia018, fascia019, fascia021, fascia025, fascia026, fascia029, fascia030, fascia033, fascia034, fascia037, fascia038, fascia041, fascia042, fascia045, fascia046, fascia049, fascia051, fascia053, fascia054, fascia057, fascia059, fascia061, fascia062, fascia065, fascia066, fascia069, fascia070, fascia071, fascia073, fascia074, fascia077, fascia081, fascia082, fascia083, fascia085, fascia086, fascia089, fascia090, fascia093, fascia094, fascia095, fascia097, fascia098, fascia101, fascia102, fascia105, fascia107, fascia108, fascia109, fascia111, fascia113, fascia114, fascia117, fascia118, fascia120, fascia121, fascia122, fascia123, fascia125, fascia126, fascia127, fascia129, fascia130, fascia131, fascia133, fascia138, fascia139, fascia141, fascia142, fascia145, fascia146, fascia149, fascia150, fascia152, fascia153, fascia154, fascia157, fascia158, fascia159, fascia160, fascia161, fascia165, fascia166, fascia169, fascia170, fascia172, fascia173, fascia174, fascia177, fascia178, fascia179, fascia181, fascia182, fascia185, fascia186, fascia189, fascia190, fascia191, fascia193, fascia194, fascia195, fascia197, fascia198, fascia199, fascia201, fascia202, fascia205, fascia206, fascia209, fascia210, fascia211, fascia212, fascia213, fascia214, fascia217, fascia218, fascia220, fascia221, fascia225, fascia226, fascia229, fascia230, fascia234, fascia235, fascia237, fascia241, fascia243, fascia245, fascia246, fascia249, fascia250, fascia253, fascia254, fascia255, fascia257, fascia258, fascia261, fascia262, fascia265, fascia266, fascia269, fascia270, fascia271, fascia273, fascia274, fascia277, fascia278, fascia279, fascia281, fascia282, fascia285, fascia286, fascia287, fascia289, fascia290, fascia293, fascia294, fascia297, fascia301, fascia302, fascia303, fascia305, fascia306, fascia307, fascia309, fascia310, fascia313, fascia314, fascia315, fascia317, fascia318
Posizioni sempre decisive (115): fascia003, fascia004, fascia008, fascia012, fascia016, fascia017, fascia020, fascia022, fascia023, fascia024, fascia027, fascia028, fascia031, fascia032, fascia035, fascia036, fascia039, fascia040, fascia043, fascia044, fascia048, fascia050, fascia052, fascia055, fascia056, fascia060, fascia064, fascia067, fascia068, fascia072, fascia075, fascia076, fascia084, fascia087, fascia091, fascia092, fascia096, fascia099, fascia100, fascia104, fascia106, fascia112, fascia115, fascia116, fascia119, fascia124, fascia128, fascia132, fascia136, fascia137, fascia140, fascia144, fascia147, fascia148, fascia151, fascia155, fascia156, fascia162, fascia163, fascia164, fascia167, fascia168, fascia176, fascia180, fascia183, fascia184, fascia187, fascia188, fascia192, fascia196, fascia200, fascia203, fascia204, fascia207, fascia208, fascia215, fascia216, fascia222, fascia224, fascia227, fascia228, fascia231, fascia232, fascia236, fascia238, fascia240, fascia244, fascia247, fascia248, fascia251, fascia252, fascia256, fascia259, fascia260, fascia264, fascia267, fascia268, fascia272, fascia275, fascia276, fascia280, fascia283, fascia284, fascia288, fascia291, fascia292, fascia296, fascia300, fascia304, fascia308, fascia311, fascia312, fascia316, fascia319, fascia320

## F contro i nugget alla stessa Pfav (esplorativa, confronto_f_nugget.py)

Partite decise con Pfav fra 0.69 e 0.82, 25'+10", ShashChess 42.3 contro Stockfish 19.

| Insieme | Posizioni | Partite | Decise | Quota [Wilson 95%] | Pfav media | Delta WDL media [min; max] | Finali |
|---|---|---|---|---|---|---|---|
| C (pool) | 130 | 1040 | 486 | 46.7% [43.7; 49.8] | 0.755 | 0.030 [0.000; 0.060] | 19% |
| F, stesso intervallo | 103 | 206 | 69 | 33.5% [27.4; 40.2] | 0.757 | 0.204 [0.060; 0.517] | 34% |
| F, tutte | 320 | 640 | 255 | 39.8% [36.1; 43.7] | 0.751 | 0.181 [0.006; 0.889] | 34% |

Finali: posizioni classificate Endgame o Transition to endgame.

Regressioni logistiche (odds ratio [IC 95%], errori robusti per posizione):

- M1, F contro C a parita' di Pfav: 0.53 [0.33; 0.83], p = 0.006
- M2, finale contro il resto nelle partite di F, a parita' di Pfav: 0.36 [0.17; 0.76], p = 0.007
- M3, F contro C a parita' di Pfav e di fase: 0.57 [0.36; 0.92], p = 0.020
- M4, Delta WDL per 0,1 nelle partite di F, a parita' di Pfav: 0.99 [0.85; 1.16], p = 0.920
- M5, F contro C a parita' di Pfav, fase e Delta WDL: 1.04 [0.40; 2.70], p = 0.929; Delta WDL 0.70 [0.44; 1.12], p = 0.138. Nell'intervallo i due insiemi quasi non si sovrappongono in Delta WDL, quindi i due effetti non si separano.

## Sintesi

- Ipotesi primaria non sostenuta: -0,4 Elo per 0,1 di Pfav [-3,2; +2,4], p = 0,79. L'intervallo esclude i +25 Elo per 0,1 dell'analisi esplorativa di C. L'errore standard (1,4 Elo per 0,1) e' minore dei 3,5 previsti, perche' 295 coppie su 320 hanno fatto 1 punto.
- ShashChess - Stockfish su tutte le posizioni: -0,5 Elo [-5,9; +4,8], p = 0,84 (McNemar 12 contro 13). Nessuna fascia e nessuna zona di Shashin con una differenza significativa.
- Partite decise dal 3,1% (0,55-0,65) al 90,0% (0,85-0,95): odds ratio 8,9 per 0,1 di Pfav [5,7; 14,0]. La parte sfavorita non ha mai vinto (0 su 640, in ogni fascia); conversioni da favorita 39,7% (ShashChess) e 40,0% (Stockfish).
- Coppie informative (una sola conversione): 25 su 320 (8%), 16 delle quali fra 0,75 e 0,85.
- Delta WDL non e' associato alle partite decise: rho -0,08 (p = 0,18); odds ratio 0,99 per 0,1 a parita' di Pfav (p = 0,92).
- Esplorativa: a parita' di Pfav (0,69-0,82) le posizioni di F sono meno decisive dei nugget, 33,5% contro 46,7% (odds ratio 0,53 [0,33; 0,83]; 0,57 [0,36; 0,92] a parita' di fase). F differisce dal pool per Delta WDL, per le linee di partita e per la quota di finali (34% contro 19%); Delta WDL e insieme non si separano.
