"""
stabilita_registri.py - ripetibilita' delle misure WDL fra analisi ripetute delle stesse posizioni.

Serve a giustificare le soglie (R1, commento minore 1): se la variabilita' di Pwin e di Delta WDL
fra due analisi identiche e' confrontabile con la soglia, la classificazione "nugget" dipende dal
caso. Si confrontano K registri (tutte_le_posizioni.csv) prodotti dal miner con la stessa
configurazione (config_rumore.json, una cartella per ripetizione).

Uscite: per ogni livello (pool, top) la quota di posizioni classificate sempre allo stesso modo,
la deviazione standard entro posizione di Pwin e di Delta, la quota di posizioni in cui cambia la
mossa migliore, e la soglia minima di Delta compatibile con il rumore misurato.

Uso:
  python stabilita_registri.py --registri data/rumore/run0*/tutte_le_posizioni.csv --out stabilita_2026
"""
import argparse
import csv
import json

import numpy as np

EPS = 1e-9


def leggi(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {r["FEN"]: r for r in csv.DictReader(f)
                if r.get("Stato") in ("Nugget", "Non nugget") and r.get("W1") not in (None, "")}


def misure(r):
    w1, d1, l1 = (float(r[k]) for k in ("W1", "D1", "L1"))
    w2, d2 = float(r["W2"]), float(r["D2"])
    p1, p2 = w1 + d1 / 2, w2 + d2 / 2
    return p1, abs(p1 - p2), w1, l1, r.get("Mossa1", "")


def pepita(p1, delta, w1, l1, tol, dmax, opp):
    bianca = abs(p1 - 0.75) <= tol + EPS and l1 <= opp + EPS
    nera = abs(p1 - 0.25) <= tol + EPS and w1 <= opp + EPS
    return (bianca or nera) and delta <= dmax + EPS


def main():
    ap = argparse.ArgumentParser(description="Ripetibilita' delle misure WDL fra registri")
    ap.add_argument("--registri", nargs="+", required=True, help="almeno due tutte_le_posizioni.csv")
    ap.add_argument("--tol", type=float, default=0.06)
    ap.add_argument("--delta-pool", type=float, default=0.06)
    ap.add_argument("--tol-top", type=float, default=0.03)
    ap.add_argument("--delta-top", type=float, default=0.03)
    ap.add_argument("--opposite-max", type=float, default=0.0)
    ap.add_argument("--out", default="stabilita_2026")
    a = ap.parse_args()
    if len(a.registri) < 2:
        raise SystemExit("[ERRORE] servono almeno due registri")

    regs = [leggi(p) for p in a.registri]
    comuni = sorted(set.intersection(*(set(r) for r in regs)))
    if not comuni:
        raise SystemExit("[ERRORE] nessuna posizione comune ai registri")
    k = len(regs)
    P = np.array([[misure(r[f])[0] for r in regs] for f in comuni])
    D = np.array([[misure(r[f])[1] for r in regs] for f in comuni])
    W = np.array([[misure(r[f])[2] for r in regs] for f in comuni])
    L = np.array([[misure(r[f])[3] for r in regs] for f in comuni])
    M = [[misure(r[f])[4] for r in regs] for f in comuni]

    ds_p = P.std(axis=1, ddof=1)
    ds_d = D.std(axis=1, ddof=1)
    cambio_mossa = np.mean([len(set(m)) > 1 for m in M])
    ris = {"registri": a.registri, "ripetizioni": k, "posizioni_comuni": len(comuni),
           "ds_entro_posizione": {
               "Pwin_media": float(ds_p.mean()), "Pwin_p95": float(np.percentile(ds_p, 95)),
               "Delta_media": float(ds_d.mean()), "Delta_mediana": float(np.median(ds_d)),
               "Delta_p95": float(np.percentile(ds_d, 95))},
           "quota_cambio_mossa_migliore": float(cambio_mossa),
           "livelli": {}}
    for nome, tol, dmax in (("pool", a.tol, a.delta_pool), ("top", a.tol_top, a.delta_top)):
        C = np.array([[pepita(P[i, j], D[i, j], W[i, j], L[i, j], tol, dmax, a.opposite_max)
                       for j in range(k)] for i in range(len(comuni))])
        mai, sempre = ~C.any(axis=1), C.all(axis=1)
        almeno_una = C.any(axis=1)
        ris["livelli"][nome] = {
            "tolleranza_Pwin": tol, "delta_max": dmax,
            "pepite_per_ripetizione": [int(x) for x in C.sum(axis=0)],
            "pepita_in_tutte": int(sempre.sum()), "pepita_in_almeno_una": int(almeno_una.sum()),
            "classificazione_stabile": float(np.mean(sempre | mai)),
            "conferma_fra_le_pepite": float(sempre.sum() / almeno_una.sum()) if almeno_una.any() else None}
    # soglia di Delta sotto la quale la classificazione e' dominata dal rumore:
    # due volte la DS entro posizione (95° percentile) della differenza fra due analisi
    ris["delta_minimo_consigliato"] = float(2 * np.percentile(ds_d, 95))

    with open(a.out + ".json", "w", encoding="utf-8") as f:
        json.dump(ris, f, indent=2, ensure_ascii=False)
    e = ris["ds_entro_posizione"]
    md = [f"# Ripetibilita' delle misure WDL ({k} analisi ripetute, {len(comuni)} posizioni comuni)", "",
          f"DS entro posizione di Pwin: media {e['Pwin_media']:.4f}, 95° percentile {e['Pwin_p95']:.4f}.",
          f"DS entro posizione di Delta WDL: media {e['Delta_media']:.4f}, mediana {e['Delta_mediana']:.4f}, "
          f"95° percentile {e['Delta_p95']:.4f}.",
          f"Posizioni in cui cambia la mossa migliore fra le ripetizioni: {100 * cambio_mossa:.1f}%.",
          f"Soglia minima di Delta consigliata (2 x DS al 95° percentile): {ris['delta_minimo_consigliato']:.3f}.", ""]
    for nome, v in ris["livelli"].items():
        conf = v["conferma_fra_le_pepite"]
        md.append(f"Livello {nome} (Pwin ±{v['tolleranza_Pwin']}, Delta ≤ {v['delta_max']}): pepite per ripetizione "
                  f"{v['pepite_per_ripetizione']}; pepita in tutte {v['pepita_in_tutte']}, in almeno una "
                  f"{v['pepita_in_almeno_una']}; classificazione stabile {100 * v['classificazione_stabile']:.1f}%; "
                  f"conferma fra le pepite {100 * conf:.1f}%." if conf is not None else
                  f"Livello {nome}: nessuna pepita.")
    with open(a.out + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"[OK] Scritti {a.out}.json e {a.out}.md")


if __name__ == "__main__":
    main()
