# Match confermativo (fase C): disegno fissato prima di giocare (18 novembre 2026)

- Motori: ShashChess 42.3 (sha256 4bdf0907..., bench 2443546) contro Stockfish 19 (sha256 a9b9f7aa..., bench 2497913).
- Posizioni: posizioni/nuggets_pool_robusto.epd, 130 posizioni: pepite sulla media di tre analisi di Stockfish 19
  a 60 s (Pwin +/-0,06, Delta <= 0,06, nessuna probabilita' di perdere per chi e' in vantaggio), una per linea di partita.
- Partite: ogni posizione due volte a colori invertiti per ciclo, 4 cicli: 520 coppie, 1.040 partite
  (almeno 460 coppie per rilevare 14 Elo con potenza dell'80%).
- Condizioni: 25'+10", 4 thread e 2 GB di hash per motore, 47 partite simultanee, tablebase Syzygy,
  aggiudicazioni di comune2026.sh, motori riavviati a ogni partita, apprendimento di ShashChess disattivato.
- Analisi primaria: differenza Elo ShashChess - Stockfish con modello pentanomiale, IC 95%, test bilaterale
  con alfa = 0,05; robustezza con cluster per posizione. Nessuna analisi intermedia, nessun arresto anticipato.
