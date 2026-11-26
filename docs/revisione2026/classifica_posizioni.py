import csv, sys
from collections import Counter
f = sys.argv[1] if len(sys.argv) > 1 else "data/outputTest2026_SF19/tutte_le_posizioni.csv"
out = f.replace("tutte_le_posizioni.csv", "classificazione.csv")
EPS = 1e-9
ultimo = {}
with open(f, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        ultimo[r["FEN"]] = r                      # vale l'ultima riga di ogni FEN
righe = []
for i, r in enumerate(ultimo.values(), 1):
    if not r.get("W1"):
        esito = "esclusa"
        motivi = "matto" if str(r.get("CP1", "")).startswith("M") else r["Stato"]
    else:
        p1, d = float(r["Pwin1"]), float(r["Delta"])
        t = 0.75 if p1 >= 0.5 else 0.25
        opp = float(r["L1"]) if t == 0.75 else float(r["W1"])
        dist, m = abs(p1 - t), []
        if dist > 0.06 + EPS: m.append("Pwin fuori da +/-0,06")
        if d > 0.06 + EPS: m.append("Delta > 0,06")
        if opp > EPS: m.append("perdita possibile")
        esito = "no" if m else ("top" if dist <= 0.03 + EPS and d <= 0.03 + EPS else "pool")
        motivi = "; ".join(m)
    righe.append(dict(n=i, esito=esito, motivi=motivi, Pwin1=r.get("Pwin1"), Delta=r.get("Delta"),
                      W1=r.get("W1"), D1=r.get("D1"), L1=r.get("L1"), Mossa1=r.get("Mossa1"),
                      Mossa2=r.get("Mossa2"), Profondita1=r.get("Profondita1"),
                      Variante_PGN=r.get("Variante_PGN"), FEN=r["FEN"]))
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(righe[0]))
    w.writeheader(); w.writerows(righe)
c = Counter(x["esito"] for x in righe)
print(f"Posizioni: {len(righe)}; nel pool: {c['pool'] + c['top']} (di cui al livello Top: {c['top']}); "
      f"non pepite: {c['no']}; escluse: {c['esclusa']}")
print("Motivi:", dict(Counter(m for x in righe for m in x["motivi"].split("; ") if m)))
for x in righe:
    print(f"{x['n']:>3} {x['esito']:<7} Pwin {x['Pwin1'] or '-':>6}  Delta {x['Delta'] or '-':>6}  "
          f"{x['Mossa1'] or '':>6} / {x['Mossa2'] or '':<6} {x['motivi']:<40} {str(x['Variante_PGN'])[:45]}")
print(f"[OK] Dettaglio in {out}")
