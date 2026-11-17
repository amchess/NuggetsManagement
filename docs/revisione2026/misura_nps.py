"""
misura_nps.py - velocita' di ricerca (NPS) dei motori nelle condizioni degli esperimenti.

Risponde a R1, commento minore 3: invece di una sola misura, ripete la misura e riporta media,
deviazione standard e intervallo di confidenza, per ogni motore e per il rapporto con il motore
di riferimento.

Protocollo:
  - per ogni ripetizione si misurano i motori a turno, in ordine alternato (ABCD, DCBA, ...),
    per non attribuire a un motore una deriva della macchina (temperatura, frequenza);
  - in ogni blocco girano --paralleli istanze dello stesso motore insieme, ciascuna con
    --threads thread: con 47 istanze x 4 thread il carico e' quello dei match;
  - ogni istanza analizza le stesse --n posizioni per --movetime millisecondi ciascuna,
    dopo ucinewgame; si registrano NPS, nodi e profondita' dell'ultima riga info.

Solo libreria standard: nessuna dipendenza da python-chess.

Uso:
  python misura_nps.py --motore Stockfish19=/percorso/sf --motore ShashChess42=/percorso/sc \
      --posizioni nuggets_top100.epd --riferimento Stockfish19 --out nps_2026
Opzioni utili: --ripetizioni 5 --n 10 --movetime 5000 --paralleli 47 --threads 4 --hash 2048
               --opzione ShashChess42:"Persisted learning"=Off  (opzioni UCI specifiche)
"""
import argparse
import csv
import json
import math
import random
import statistics
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor


def leggi_posizioni(percorso, n):
    fens = []
    with open(percorso, encoding="utf-8") as f:
        for riga in f:
            campi = riga.split()
            if len(campi) >= 4 and "/" in campi[0]:
                fens.append(" ".join(campi[:4]) + " 0 1")
            if len(fens) >= n:
                break
    if not fens:
        raise SystemExit(f"[ERRORE] nessuna posizione EPD in {percorso}")
    return fens


class Motore:
    def __init__(self, cmd, opzioni):
        self.p = subprocess.Popen([cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.manda("uci")
        dichiarate = set()
        for riga in self.attendi("uciok"):
            if riga.startswith("option name "):
                dichiarate.add(riga[len("option name "):].split(" type ")[0])
        for nome, valore in opzioni.items():
            if nome in dichiarate:
                self.manda(f"setoption name {nome} value {valore}")
        self.manda("isready")
        self.attendi("readyok")

    def manda(self, testo):
        self.p.stdin.write(testo + "\n")
        self.p.stdin.flush()

    def attendi(self, parola):
        righe = []
        while True:
            riga = self.p.stdout.readline()
            if not riga:
                raise RuntimeError("il motore ha chiuso l'output")
            riga = riga.strip()
            righe.append(riga)
            if riga.split(" ")[0] == parola:
                return righe

    def misura(self, fen, movetime):
        self.manda("ucinewgame")
        self.manda("isready")
        self.attendi("readyok")
        self.manda(f"position fen {fen}")
        self.manda(f"go movetime {movetime}")
        ultimo = {}
        for riga in self.attendi("bestmove"):
            t = riga.split()
            if t and t[0] == "info" and "nps" in t:
                for chiave in ("nps", "nodes", "depth", "time"):
                    if chiave in t:
                        try:
                            ultimo[chiave] = int(t[t.index(chiave) + 1])
                        except (ValueError, IndexError):
                            pass
        return ultimo

    def chiudi(self):
        try:
            self.manda("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def blocco(nome, cmd, opzioni, fens, movetime, paralleli):
    """Avvia `paralleli` istanze dello stesso motore e misura tutte le posizioni in contemporanea."""
    def una_istanza(i):
        m = Motore(cmd, opzioni)
        try:
            return [dict(motore=nome, istanza=i, posizione=k, **m.misura(f, movetime))
                    for k, f in enumerate(fens)]
        finally:
            m.chiudi()
    with ThreadPoolExecutor(max_workers=paralleli) as ex:
        return [r for lista in ex.map(una_istanza, range(paralleli)) for r in lista]


def ic_media(valori, livello=0.95):
    n = len(valori)
    m = statistics.fmean(valori)
    if n < 2:
        return m, float("nan"), (float("nan"), float("nan"))
    s = statistics.stdev(valori)
    # quantile t di Student approssimato (Cornish-Fisher) per evitare scipy
    z = statistics.NormalDist().inv_cdf(0.5 + livello / 2)
    gl = n - 1
    t = z + (z ** 3 + z) / (4 * gl) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * gl ** 2)
    h = t * s / math.sqrt(n)
    return m, s, (m - h, m + h)


def main():
    ap = argparse.ArgumentParser(description="Misura ripetuta degli NPS sotto carico")
    ap.add_argument("--motore", action="append", required=True, help="NOME=ESEGUIBILE (ripetibile)")
    ap.add_argument("--posizioni", required=True, help="file .epd (si usano le prime --n righe)")
    ap.add_argument("--riferimento", default=None, help="motore di riferimento per i rapporti")
    ap.add_argument("--opzione", action="append", default=[],
                    help='opzione specifica: NOME:Opzione=valore (es. ShashChess42:"Persisted learning"=Off)')
    ap.add_argument("--ripetizioni", type=int, default=5)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--movetime", type=int, default=5000, help="millisecondi per posizione")
    ap.add_argument("--paralleli", type=int, default=47)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--hash", type=int, default=2048)
    ap.add_argument("--seme", type=int, default=2026)
    ap.add_argument("--out", default="nps_2026")
    a = ap.parse_args()

    motori = dict(m.split("=", 1) for m in a.motore)
    specifiche = {nome: {} for nome in motori}
    for o in a.opzione:
        nome, resto = o.split(":", 1)
        chiave, valore = resto.split("=", 1)
        specifiche.setdefault(nome, {})[chiave.strip('"')] = valore
    fens = leggi_posizioni(a.posizioni, a.n)
    rif = a.riferimento or next(iter(motori))
    ordine = list(motori)
    random.Random(a.seme).shuffle(ordine)

    righe, inizio = [], time.time()
    for r in range(a.ripetizioni):
        turno = ordine if r % 2 == 0 else ordine[::-1]
        for nome in turno:
            opzioni = {"Threads": a.threads, "Hash": a.hash, **specifiche.get(nome, {})}
            t0 = time.time()
            ris = blocco(nome, motori[nome], opzioni, fens, a.movetime, a.paralleli)
            for x in ris:
                x["ripetizione"] = r
            righe.extend(ris)
            print(f"[*] ripetizione {r + 1}/{a.ripetizioni} {nome}: {len(ris)} misure in {time.time() - t0:.0f} s")

    with open(a.out + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ripetizione", "motore", "istanza", "posizione",
                                          "nps", "nodes", "depth", "time"], extrasaction="ignore")
        w.writeheader()
        w.writerows(righe)

    # media per ripetizione (unita' indipendente), poi media e IC fra ripetizioni
    per_rip = {}
    for x in righe:
        if "nps" in x:
            per_rip.setdefault((x["motore"], x["ripetizione"]), []).append(x)
    sintesi = {}
    for nome in motori:
        nps = [statistics.fmean(v["nps"] for v in per_rip[(nome, r)])
               for r in range(a.ripetizioni) if (nome, r) in per_rip]
        prof = [v.get("depth", 0) for r in range(a.ripetizioni) for v in per_rip.get((nome, r), [])]
        m, s, ic = ic_media(nps)
        sintesi[nome] = {"nps_medio_istanza": m, "ds_fra_ripetizioni": s, "ic95": ic,
                         "cv_percento": 100 * s / m if m else float("nan"),
                         "profondita_mediana": statistics.median(prof) if prof else None}
        if nome != rif:
            rapporti = [statistics.fmean(v["nps"] for v in per_rip[(nome, r)]) /
                        statistics.fmean(v["nps"] for v in per_rip[(rif, r)])
                        for r in range(a.ripetizioni) if (nome, r) in per_rip and (rif, r) in per_rip]
            rm, rs, ric = ic_media(rapporti)
            sintesi[nome][f"rapporto_su_{rif}"] = {"media": rm, "ds": rs, "ic95": ric}

    meta = {"posizioni": a.posizioni, "n_posizioni": len(fens), "movetime_ms": a.movetime,
            "paralleli": a.paralleli, "threads": a.threads, "hash": a.hash,
            "ripetizioni": a.ripetizioni, "durata_s": round(time.time() - inizio)}
    with open(a.out + ".json", "w", encoding="utf-8") as f:
        json.dump({"condizioni": meta, "sintesi": sintesi}, f, indent=2, ensure_ascii=False)

    righe_md = [f"# NPS sotto carico ({a.paralleli} istanze x {a.threads} thread, {a.movetime} ms per posizione, "
                f"{len(fens)} posizioni, {a.ripetizioni} ripetizioni)", "",
                "| Motore | NPS medio per istanza | DS fra ripetizioni | IC 95% | CV % | Profondita' mediana |"
                f" Rapporto su {rif} [IC 95%] |", "|---|---|---|---|---|---|---|"]
    for nome, s in sintesi.items():
        rap = s.get(f"rapporto_su_{rif}")
        rap_txt = f"{rap['media']:.3f} [{rap['ic95'][0]:.3f}; {rap['ic95'][1]:.3f}]" if rap else "1"
        righe_md.append(f"| {nome} | {s['nps_medio_istanza']:,.0f} | {s['ds_fra_ripetizioni']:,.0f} | "
                        f"[{s['ic95'][0]:,.0f}; {s['ic95'][1]:,.0f}] | {s['cv_percento']:.1f} | "
                        f"{s['profondita_mediana']} | {rap_txt} |")
    with open(a.out + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(righe_md) + "\n")
    print("\n".join(righe_md))
    print(f"[OK] Scritti {a.out}.csv, {a.out}.json e {a.out}.md")


if __name__ == "__main__":
    main()
