#!/usr/bin/env python3
"""
Controllo UHO (fase E1): sceglie le posizioni UHO con la stessa probabilita' di vittoria dei nugget.

Legge il registro del miner (tutte_le_posizioni.csv) dell'analisi di Stockfish 19 a 60 s sulle posizioni
UHO candidate (posizioni/uho_screening_1200.epd) e tiene quelle con Pwin1 entro 0,75 +/- tolleranza e
L1 = 0, cioe' lo stesso criterio dei nugget "bianchi", ma SENZA il criterio di indecisione (Delta).
Poi estrae N posizioni con un seme fisso.

Uscite:
  <prefisso>.epd  posizioni per cutechess-cli, nello stesso formato dei nugget (id e c0 con Pwin e DeltaWDL)
  <prefisso>.csv  righe del registro delle posizioni scelte
  <prefisso>.md   riepilogo: conteggi, distribuzione del Delta, seme

Uso:
  python docs/revisione2026/seleziona_uho.py data/outputUHO2024_SF19/tutte_le_posizioni.csv \
      --uscita docs/revisione2026/posizioni/uho_250
"""
import argparse
import csv
import random
import statistics
import sys

EPS = 1e-9


def quartili(valori):
    v = sorted(valori)
    if len(v) < 4:
        return (min(v), statistics.median(v), max(v)) if v else (float("nan"),) * 3
    q = statistics.quantiles(v, n=4, method="inclusive")
    return q[0], q[1], q[2]


def main():
    ap = argparse.ArgumentParser(description="Sceglie le posizioni UHO per il controllo E1")
    ap.add_argument("registro", help="tutte_le_posizioni.csv dell'analisi delle posizioni UHO")
    ap.add_argument("--n", type=int, default=250, help="posizioni da estrarre (default 250)")
    ap.add_argument("--seme", type=int, default=2026, help="seme dell'estrazione (default 2026)")
    ap.add_argument("--tolleranza", type=float, default=0.06, help="tolleranza su Pwin1 attorno a 0,75 (default 0,06)")
    ap.add_argument("--delta-nugget", type=float, default=0.06, help="soglia del Delta dei nugget, solo per il riepilogo")
    ap.add_argument("--uscita", default="uho_250", help="prefisso dei file di uscita")
    a = ap.parse_args()

    # Ultima riga per FEN, come in riepilogo_registro.py (le righe "Errore" vengono superate dalla rianalisi)
    ultime = {}
    with open(a.registro, newline="", encoding="utf-8") as f:
        lettore = csv.DictReader(f)
        campi = lettore.fieldnames
        for r in lettore:
            ultime[r["FEN"]] = r
    stati = {}
    for r in ultime.values():
        stati[r["Stato"]] = stati.get(r["Stato"], 0) + 1
    analizzate = [r for r in ultime.values() if r["Stato"] in ("Nugget", "Non nugget")]

    def in_fascia(r):
        return abs(float(r["Pwin1"]) - 0.75) <= a.tolleranza + EPS and float(r["L1"]) <= EPS

    idonee = sorted((r for r in analizzate if in_fascia(r)), key=lambda r: r["Variante_PGN"])
    if len(idonee) < a.n:
        sys.exit(f"[ERRORE] solo {len(idonee)} posizioni idonee su {len(analizzate)} analizzate: "
                 f"ne servono {a.n}; analizzare altre posizioni UHO")

    scelte = sorted(random.Random(a.seme).sample(idonee, a.n), key=lambda r: r["Variante_PGN"])

    with open(a.uscita + ".epd", "w", encoding="utf-8", newline="\n") as f:
        for r in scelte:
            fen4 = " ".join(r["FEN"].split()[:4])
            f.write(f'{fen4} id "{r["Variante_PGN"]}"; c0 "Pwin={float(r["Pwin1"]):.3f} DeltaWDL={float(r["Delta"]):.3f}";\n')
    with open(a.uscita + ".csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        w.writerows(scelte)

    d_idonee = [float(r["Delta"]) for r in idonee]
    d_scelte = [float(r["Delta"]) for r in scelte]
    p_scelte = [float(r["Pwin1"]) for r in scelte]
    pepite_idonee = sum(d <= a.delta_nugget + EPS for d in d_idonee)
    pepite_scelte = sum(d <= a.delta_nugget + EPS for d in d_scelte)
    q_i, q_s = quartili(d_idonee), quartili(d_scelte)
    righe = [
        "# Controllo UHO (fase E1): posizioni scelte",
        "",
        f"- Registro: {a.registro}",
        f"- Stati (ultima riga per FEN): " + ", ".join(f"{k} {v}" for k, v in sorted(stati.items())),
        f"- Analizzate: {len(analizzate)}",
        f"- Idonee (|Pwin1 - 0,75| <= {a.tolleranza:.2f} e L1 = 0, nessun criterio sul Delta): {len(idonee)} "
        f"({100 * len(idonee) / len(analizzate):.1f}% delle analizzate)",
        f"- Fra le idonee, con Delta <= {a.delta_nugget:.2f} (sarebbero nugget): {pepite_idonee} "
        f"({100 * pepite_idonee / len(idonee):.1f}%)",
        f"- Delta delle idonee: Q1 {q_i[0]:.3f}, mediana {q_i[1]:.3f}, Q3 {q_i[2]:.3f}",
        f"- Estratte: {a.n} con random.Random({a.seme}).sample, idonee ordinate per id",
        f"- Delta delle estratte: Q1 {q_s[0]:.3f}, mediana {q_s[1]:.3f}, Q3 {q_s[2]:.3f}; "
        f"con Delta <= {a.delta_nugget:.2f}: {pepite_scelte} ({100 * pepite_scelte / a.n:.1f}%)",
        f"- Pwin1 delle estratte: media {statistics.mean(p_scelte):.3f}, mediana {statistics.median(p_scelte):.3f}",
        f"- File: {a.uscita}.epd, {a.uscita}.csv",
    ]
    with open(a.uscita + ".md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(righe) + "\n")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
