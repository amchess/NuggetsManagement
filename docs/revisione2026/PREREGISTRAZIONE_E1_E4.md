# Fasi E3, E4 ed E1: disegno fissato prima di giocare (21 novembre 2026)

- Motori e condizioni: Stockfish 19 contro ShashChess 42.3, stessi eseguibili e opzioni del match C e del round robin
  (sha256 in motori.txt), 4 thread, 2 GB di hash, Syzygy a 6 pezzi, 47 partite simultanee, aggiudicazioni di comune2026.sh.
- E1, controllo UHO: posizioni/uho_250.epd, 250 posizioni del libro UHO 2024 (8 mosse, fascia KomodoDragon +0,95/+1,04)
  con la stessa Pwin dei nugget secondo Stockfish 19 (una analisi a 60 s: |Pwin - 0,75| <= 0,06 e L = 0, nessun criterio
  sul Delta), estratte con seme 2026 fra le 418 idonee su 1.200 analizzate (posizioni/uho_250.md);
  250 x 2 colori = 500 partite a 25'+10".
  Analisi: S3, interazione Elo(nugget, match C) - Elo(UHO) con errore standard combinato (statistiche_match.py --confronta);
  S5, partite decisive (IC di Wilson), vittorie della parte sfavorita, decisive per fascia di Pwin (rho di Spearman).
- E4, secondo controllo di tempo: posizioni/nuggets_pool_robusto.epd, 130 posizioni x 4 cicli x 2 colori = 1.040 partite
  a 60"+0,6". Analisi: S8, Elo a 25'+10" (match C) e a 60"+0,6", interazione; S5 come sopra.
- E3, NPS sotto carico: misura_nps.py, i 4 motori del round robin (Triumviratus con NumaSpread=false), 47 istanze x 4 thread,
  5 ripetizioni in ordine alternato, 10 posizioni della Top-100 x 5 s. Analisi: S7, NPS medi e rapporto con Stockfish 19,
  IC 95% fra ripetizioni.
- Rianalisi descrittiva: le 250 posizioni UHO analizzate altre due volte a 60 s, per riportarne la Pwin media di 3 analisi
  come per i nugget; la selezione non cambia.
- Ordine di esecuzione (coda_sabato.sh): E3, E4, E1, rianalisi. Tutte analisi secondarie: nessuna analisi intermedia,
  nessun arresto anticipato.
