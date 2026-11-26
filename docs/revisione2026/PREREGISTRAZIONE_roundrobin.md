# Round robin (fase D): disegno fissato prima di giocare (20 novembre 2026)

- Motori, con 4 thread e 2 GB di hash ciascuno (sha256 e bench completi in motori.txt della prova di fumo
  risultati/20261120_0002_rr_fumo_rr):
  - Stockfish 19 (sha256 a9b9f7aa..., bench 2497913);
  - ShashChess 42.3 (sha256 4bdf0907..., bench 2443546; apprendimento disattivato);
  - Reckless 0.9.0, release ufficiale avx512 (sha256 0da69d9b..., bench 3652336);
  - Triumviratus 8.1, release ufficiale avx512 (sha256 e1bb3b84..., bench 310807; NumaSpread=false, motivo in comune2026.sh).
- Posizioni: posizioni/nuggets_top100_robusto.epd, le 100 posizioni del pool robusto (130) con Delta piu' basso
  (da 0 a 0,043), una per linea di partita.
- Disegno incrociato completo: 6 match a due motori in parallelo, ciascuno su tutte le 100 posizioni a colori invertiti:
  6 coppie x 100 posizioni x 2 colori = 1.200 partite; 47 partite simultanee divise 8, 8, 8, 8, 8, 7.
- Condizioni: 25'+10", tablebase Syzygy a 6 pezzi, aggiudicazioni di comune2026.sh, motori riavviati a ogni partita,
  impostazioni di default salvo Threads, Hash, opzioni Syzygy e le eccezioni dichiarate sopra.
- Analisi (piano di revisione v2, S2 e S5), tutte secondarie e riportate con intervalli di confidenza: punteggi
  Bradley-Terry con IC 95% bootstrap sulle posizioni; Elo pentanomiale per ogni coppia di motori; partite decisive per
  coppia (IC di Wilson) e sconfitte della parte favorita. Nessuna analisi intermedia, nessun arresto anticipato.
- La coppia Stockfish-ShashChess rigioca 100 delle 130 posizioni del match C nelle stesse condizioni: non e' una
  replica indipendente e non modifica l'analisi primaria del match C.
