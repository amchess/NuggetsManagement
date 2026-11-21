# Fasi B ed E5: disegno fissato prima di eseguire (21 novembre 2026)

- B, secondo oracolo (Lc0): le 2.321 posizioni candidate (data/outputWch2026_SF19/candidati.csv, le stesse delle tre
  analisi di Stockfish) analizzate da Lc0 v0.32.1, compilato da sorgente con backend BLAS (OpenBLAS), rete
  t3-512x15x16h-distill2-swa-03477500 (sha256 baa560022c7b...), 4 thread, minibatch 32, 10.000 nodi per posizione,
  SmartPruningFactor = 0, MultiPV 2, WDL senza riscalatura, 47 istanze (config_lc0.json).
  Scelta della rete: velocita' misurata sotto carico con 4 thread: BT4-it332 3 nodi/s, BT3-768x15x24h 13, t3-512x15x16h 38;
  si usa la rete piu' veloce, l'unica che consente una ricerca di 10.000 nodi in circa 4 ore.
- Confronto con Stockfish 19 (media delle 3 analisi, posizioni/medie_3analisi.csv):
  - principali: rho di Spearman e accordo di Bland-Altman (differenza media, limiti al 95%) per la Pwin della mossa
    migliore e per il Delta WDL; accordo sulla mossa migliore;
  - classificazione: nugget secondo Lc0 = stessa fascia di Pwin (|Pwin - 0,75| <= 0,06 oppure |Pwin - 0,25| <= 0,06) e
    Delta <= 0,06, SENZA la condizione L = 0 (o W = 0). La testa di valore di Lc0 assegna qualche punto percentuale
    alla parte sfavorita anche dove il modello WDL di Stockfish da' 0 (prova della procedura su 2 posizioni, prima
    dell'analisi completa: W = 0,059 e 0,065 per la parte sfavorita), quindi la condizione non e' trasferibile fra i
    due oracoli. Si riportano il kappa di Cohen con la classificazione robusta di Stockfish, la quota di nugget di
    Stockfish confermati da Lc0 e, a parte, la distribuzione della probabilita' di vittoria della parte sfavorita;
  - secondaria (S4): risultati del match C per i nugget di consenso e per quelli solo-Stockfish.
- E5, cadenza lunga: posizioni/nuggets_pool_robusto.epd, 130 posizioni x 1 ciclo x 2 colori = 260 partite a 60'+30",
  Stockfish 19 contro ShashChess 42.3, stessi eseguibili e condizioni del match C. Analisi: Elo pentanomiale e
  interazione con il match C (25'+10") e con E4 (60"+0,6"); S5 come per le altre fasi. Potenza: IC 95% di circa
  +/-16 Elo, differenza minima rilevabile all'80% di circa 22 Elo.
- Ordine (coda_domenica.sh): B, poi E5, dopo la fine di coda_sabato.sh. Analisi secondarie: nessuna analisi
  intermedia, nessun arresto anticipato.
