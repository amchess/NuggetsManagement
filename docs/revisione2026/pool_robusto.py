"""
pool_robusto.py - classificazione delle pepite sulla media di piu' analisi ripetute.

Una singola analisi di Stockfish (60 s, 4 thread) misura Pwin e Delta WDL con un errore
dell'ordine di 0,04 (fase A3): abbastanza da far entrare o uscire una posizione dalle finestre
di selezione. Questo script legge K registri (tutte_le_posizioni.csv) prodotti con la stessa
configurazione - per esempio l'estrazione e le due ripetizioni della fase A3 - e per ogni
posizione presente in tutti calcola:

  - la media di W, D, L delle due mosse migliori e quindi Pwin medio;
  - il Delta medio (media dei Delta delle singole analisi);
  - le deviazioni standard fra le analisi, le mosse migliori trovate e quante volte la
    posizione e' risultata pepita nelle singole analisi.

Il risultato e' un CSV nel formato di nuggets.csv: genera_pgn.py lo legge direttamente, quindi
la selezione (tolleranze, L=0 / W=0, una posizione per linea, ordinamento per Delta) resta la
stessa, ma applicata alle medie invece che a una sola analisi.

Uso:
  python docs/revisione2026/pool_robusto.py \
      --registri data/outputWch2026_SF19/tutte_le_posizioni.csv \
                 data/rumore/run01/tutte_le_posizioni.csv data/rumore/run02/tutte_le_posizioni.csv \
      --out data/outputWch2026_SF19/medie_3analisi.csv
"""
import argparse
import csv
import statistics

EPS = 1e-9
COLONNE = ["FEN", "WIN_PROBABILITY", "Delta_Win_Probability", "Fase", "Centro", "Tensione", "Imbalance",
           "Frequenza", "Data_Recente", "Variante_PGN", "W1", "D1", "L1", "W2", "D2", "L2",
           "N_analisi", "DS_Pwin", "DS_Delta", "Mosse_migliori", "Mossa_stabile", "Pepita_in"]


def leggi(path):
    """Ultima riga conclusa (con WDL) di ogni FEN."""
    righe = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("Stato") in ("Nugget", "Non nugget") and r.get("W1"):
                righe[r["FEN"]] = r
    return righe


def pepita(p1, delta, w1, l1, tol, dmax, opp):
    t = 0.75 if p1 >= 0.5 else 0.25
    lato = l1 if t == 0.75 else w1
    return abs(p1 - t) <= tol + EPS and delta <= dmax + EPS and lato <= opp + EPS


def main():
    ap = argparse.ArgumentParser(description="Pepite sulla media di analisi ripetute")
    ap.add_argument("--registri", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tol", type=float, default=0.06, help="tolleranza su Pwin per il conteggio Pepita_in")
    ap.add_argument("--delta-max", type=float, default=0.06)
    ap.add_argument("--opposite-max", type=float, default=0.0)
    a = ap.parse_args()

    regs = [leggi(p) for p in a.registri]
    comuni = set(regs[0]).intersection(*regs[1:])
    k = len(regs)
    print(f"[*] Registri: {k}; posizioni presenti in tutti: {len(comuni)}")

    out = []
    for fen in (f for f in regs[0] if f in comuni):          # ordine del primo registro
        rr = [r[fen] for r in regs]
        val = {c: [float(r[c]) for r in rr] for c in ("W1", "D1", "L1", "W2", "D2", "L2")}
        p1 = [w + d / 2 for w, d in zip(val["W1"], val["D1"])]
        p2 = [w + d / 2 for w, d in zip(val["W2"], val["D2"])]
        delta = [abs(x - y) for x, y in zip(p1, p2)]
        medie = {c: statistics.fmean(v) for c, v in val.items()}
        p_media = medie["W1"] + medie["D1"] / 2
        mosse = [r.get("Mossa1", "") for r in rr]
        singole = sum(pepita(p, d, w, l, a.tol, a.delta_max, a.opposite_max)
                      for p, d, w, l in zip(p1, delta, val["W1"], val["L1"]))
        base = rr[0]
        out.append({
            "FEN": fen,
            "WIN_PROBABILITY": round(p_media, 4),
            "Delta_Win_Probability": round(statistics.fmean(delta), 4),
            "Fase": base.get("Fase", ""), "Centro": base.get("Centro", ""),
            "Tensione": base.get("Tensione", ""), "Imbalance": base.get("Imbalance", ""),
            "Frequenza": 1, "Data_Recente": base.get("Data", ""), "Variante_PGN": base.get("Variante_PGN", ""),
            **{c: round(v, 4) for c, v in medie.items()},
            "N_analisi": k,
            "DS_Pwin": round(statistics.stdev(p1), 4) if k > 1 else 0.0,
            "DS_Delta": round(statistics.stdev(delta), 4) if k > 1 else 0.0,
            "Mosse_migliori": "/".join(mosse),
            "Mossa_stabile": int(len(set(mosse)) == 1),
            "Pepita_in": singole,
        })

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNE)
        w.writeheader()
        w.writerows(out)

    pool = [r for r in out if pepita(r["WIN_PROBABILITY"], r["Delta_Win_Probability"], r["W1"], r["L1"],
                                    a.tol, a.delta_max, a.opposite_max)]
    print(f"[*] Pepite sulla media (Pwin ±{a.tol}, Delta ≤ {a.delta_max}, lato perdente ≤ {a.opposite_max}): "
          f"{len(pool)} ({sum(r['WIN_PROBABILITY'] >= 0.5 for r in pool)} a 0,75, "
          f"{sum(r['WIN_PROBABILITY'] < 0.5 for r in pool)} a 0,25)")
    for n in range(k, -1, -1):
        print(f"    di cui pepita in {n} analisi singole su {k}: {sum(r['Pepita_in'] == n for r in pool)}")
    print(f"[*] Mossa migliore diversa fra le analisi: {sum(1 - r['Mossa_stabile'] for r in out)} posizioni su "
          f"{len(out)}; fra le pepite sulla media: {sum(1 - r['Mossa_stabile'] for r in pool)}")
    print(f"[OK] Scritto {a.out}: si seleziona con genera_pgn.py come nuggets.csv")


if __name__ == "__main__":
    main()
