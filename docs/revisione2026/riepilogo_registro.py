import csv, statistics, sys
from collections import Counter
f = sys.argv[1] if len(sys.argv) > 1 else "data/outputWch2026_SF19/tutte_le_posizioni.csv"
ultimo = {}
with open(f, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        ultimo[r["FEN"]] = r          # vale l'ultima riga di ogni FEN
stati = Counter(r["Stato"] for r in ultimo.values())
print(f"FEN distinte nel registro: {len(ultimo)}  {dict(stati)}")
pep = [r for r in ultimo.values() if r["Stato"] == "Nugget"]
bianche = sum(float(r["Pwin1"]) >= 0.5 for r in pep)
top = sum(abs(float(r["Pwin1"]) - (0.75 if float(r["Pwin1"]) >= 0.5 else 0.25)) <= 0.03
          and float(r["Delta"]) <= 0.03 for r in pep)
print(f"Pepite: {len(pep)} ({bianche} a 0,75, {len(pep) - bianche} a 0,25); livello Top (+/-0,03, Delta <= 0,03): {top}")
for k, nome in (("Tempo", "tempo per posizione (s)"), ("Profondita1", "profondita'"), ("NPS", "NPS per istanza")):
    v = [float(r[k]) for r in ultimo.values() if r["Stato"] in ("Nugget", "Non nugget") and r.get(k)]
    if v:
        print(f"Mediana {nome}: {statistics.median(v):,.1f}")
