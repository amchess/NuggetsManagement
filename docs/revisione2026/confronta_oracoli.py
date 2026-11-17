#!/usr/bin/env python3
"""
Validazione incrociata delle pepite con un secondo oracolo (Lc0), richiesta da R1.4 e R2.3.

Due comandi:

  seleziona  dal registro di Stockfish (tutte_le_posizioni.csv) sceglie le posizioni da far
             rianalizzare a Lc0: tutte le pepite e le posizioni vicine ai bersagli 0,75 / 0,25
             (pepite e quasi-pepite servono entrambe, altrimenti il kappa non e' calcolabile).

  confronta  confronta i due registri (stesse FEN): correlazione di Pwin e di Delta WDL,
             accordo di Bland-Altman, accordo sulla mossa migliore, matrice di confusione e
             kappa di Cohen sulla classificazione "pepita", elenco delle pepite solo-Stockfish.

Richiede numpy e scipy. Esempi:
  python confronta_oracoli.py seleziona --registro ../../data/outputWch2026_SF19/tutte_le_posizioni.csv \
         --out ../../data/outputWch2026_SF19/candidati_lc0.csv --finestra 0.15
  python confronta_oracoli.py confronta --sf .../tutte_le_posizioni.csv --lc0 .../Lc0/tutte_le_posizioni.csv \
         --out confronto_oracoli
"""
import argparse
import collections
import csv
import json
import math
import sys

import numpy as np
from scipy import stats as sps

RNG = np.random.default_rng(20261116)


def leggi(path):
    with open(path, newline='', encoding='utf-8') as f:
        return [r for r in csv.DictReader(f) if r.get('Stato') in ('Nugget', 'Non nugget') and r.get('W1') not in (None, '')]


def num(r, k):
    return float(r[k])


def pepita(r, tol, delta, opp):
    """Stessa regola di src/registro.py: Pwin dal punto di vista del Bianco."""
    w1, d1, l1 = num(r, 'W1'), num(r, 'D1'), num(r, 'L1')
    w2, d2 = num(r, 'W2'), num(r, 'D2')
    p1, p2 = w1 + d1 / 2, w2 + d2 / 2
    e = 1e-9
    bianca = abs(p1 - 0.75) <= tol + e and l1 <= opp + e
    nera = abs(p1 - 0.25) <= tol + e and w1 <= opp + e
    return (bianca or nera) and abs(p1 - p2) <= delta + e


def kappa(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    po = np.mean(a == b)
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return float((po - pe) / (1 - pe)) if pe < 1 else float('nan')


def cmd_seleziona(args):
    righe = leggi(args.registro)
    scelte, altre = [], []
    for r in righe:
        p1 = num(r, 'Pwin1')
        vicina = abs(p1 - 0.75) <= args.finestra or abs(p1 - 0.25) <= args.finestra
        if r['Stato'] == 'Nugget':
            scelte.append(r)
        elif vicina:
            altre.append(r)
    if args.max and len(scelte) + len(altre) > args.max:
        k = max(0, args.max - len(scelte))
        idx = RNG.choice(len(altre), size=min(k, len(altre)), replace=False)
        altre = [altre[i] for i in sorted(idx)]
    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['FEN', 'Variante_PGN', 'Data'])
        for r in scelte + altre:
            w.writerow([r['FEN'], r.get('Variante_PGN', ''), r.get('Data', '')])
    print(f'[OK] {args.out}: {len(scelte)} pepite + {len(altre)} posizioni vicine ai bersagli (finestra ±{args.finestra})')


def cmd_confronta(args):
    sf = {r['FEN']: r for r in leggi(args.sf)}
    lc = {r['FEN']: r for r in leggi(args.lc0)}
    comuni = sorted(set(sf) & set(lc))
    if len(comuni) < 10:
        sys.exit(f'[ERRORE] Solo {len(comuni)} FEN in comune: controllare i file.')
    p_sf = np.array([num(sf[k], 'Pwin1') for k in comuni])
    p_lc = np.array([num(lc[k], 'Pwin1') for k in comuni])
    d_sf = np.array([num(sf[k], 'Delta') for k in comuni])
    d_lc = np.array([num(lc[k], 'Delta') for k in comuni])

    def rho_ic(x, y, B=2000):
        n = len(x)
        idx = RNG.integers(0, n, size=(B, n))
        v = [sps.spearmanr(x[i], y[i]).statistic for i in idx]
        return float(sps.spearmanr(x, y).statistic), float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))

    R = dict(posizioni_comuni=len(comuni), solo_sf=len(set(sf) - set(lc)), solo_lc0=len(set(lc) - set(sf)))
    R['pwin_spearman'] = rho_ic(p_sf, p_lc)
    R['pwin_pearson'] = float(np.corrcoef(p_sf, p_lc)[0, 1])
    R['delta_spearman'] = rho_ic(d_sf, d_lc)
    diff = p_lc - p_sf
    R['bland_altman_pwin'] = dict(media=float(diff.mean()), ds=float(diff.std(ddof=1)),
                                  limiti=[float(diff.mean() - 1.96 * diff.std(ddof=1)), float(diff.mean() + 1.96 * diff.std(ddof=1))])
    m1 = [sf[k].get('Mossa1') == lc[k].get('Mossa1') for k in comuni]
    m12 = [sf[k].get('Mossa1') in (lc[k].get('Mossa1'), lc[k].get('Mossa2')) for k in comuni]
    R['accordo_mossa_migliore'] = float(np.mean(m1))
    R['mossa_sf_fra_prime_due_lc0'] = float(np.mean(m12))

    livelli = {'pool': (args.tol, args.delta_pool), 'top': (args.tol_top, args.delta_top)}
    discordanti = []
    for nome, (tol, dl) in livelli.items():
        a = [pepita(sf[k], tol, dl, args.opposite_max) for k in comuni]
        b = [pepita(lc[k], tol, dl, args.opposite_max) for k in comuni]
        n11 = sum(x and y for x, y in zip(a, b))
        n10 = sum(x and not y for x, y in zip(a, b))
        n01 = sum(y and not x for x, y in zip(a, b))
        n00 = len(a) - n11 - n10 - n01
        kb = []
        A, Bv = np.array(a), np.array(b)
        for i in RNG.integers(0, len(a), size=(1000, len(a))):
            kb.append(kappa(A[i], Bv[i]))
        R[f'classificazione_{nome}'] = dict(
            soglie=dict(tolleranza_pwin=tol, delta_max=dl, opposite_max=args.opposite_max),
            entrambi=n11, solo_sf=n10, solo_lc0=n01, nessuno=n00,
            quota_pepite_sf_confermate=(n11 / (n11 + n10)) if n11 + n10 else None,
            kappa=kappa(a, b), kappa_ic=[float(np.nanpercentile(kb, 2.5)), float(np.nanpercentile(kb, 97.5))])
        if nome == 'pool':
            for k, x, y in zip(comuni, a, b):
                if x != y:
                    discordanti.append(dict(FEN=k, pepita_sf=x, pepita_lc0=y, Pwin_sf=sf[k]['Pwin1'], Pwin_lc0=lc[k]['Pwin1'],
                                            Delta_sf=sf[k]['Delta'], Delta_lc0=lc[k]['Delta'],
                                            Fase=sf[k].get('Fase', ''), Centro=sf[k].get('Centro', ''),
                                            Variante_PGN=sf[k].get('Variante_PGN', '')))
    solo_sf = [d for d in discordanti if d['pepita_sf']]
    R['solo_sf_per_fase'] = dict(collections.Counter(d['Fase'] for d in solo_sf))
    R['solo_sf_per_centro'] = dict(collections.Counter(d['Centro'] for d in solo_sf))

    with open(args.out + '.json', 'w', encoding='utf-8') as f:
        json.dump(R, f, indent=1, ensure_ascii=False)
    with open(args.out + '_discordanti.csv', 'w', newline='', encoding='utf-8') as f:
        if discordanti:
            w = csv.DictWriter(f, fieldnames=list(discordanti[0]))
            w.writeheader()
            w.writerows(discordanti)
    L = [f"# Stockfish contro Lc0 ({R['posizioni_comuni']} posizioni in comune)", '',
         f"Pwin: rho di Spearman {R['pwin_spearman'][0]:.3f} [{R['pwin_spearman'][1]:.3f}; {R['pwin_spearman'][2]:.3f}], r di Pearson {R['pwin_pearson']:.3f}.",
         f"Delta WDL: rho di Spearman {R['delta_spearman'][0]:.3f} [{R['delta_spearman'][1]:.3f}; {R['delta_spearman'][2]:.3f}].",
         f"Bland-Altman (Lc0 - Stockfish) su Pwin: media {R['bland_altman_pwin']['media']:+.3f}, limiti [{R['bland_altman_pwin']['limiti'][0]:+.3f}; {R['bland_altman_pwin']['limiti'][1]:+.3f}].",
         f"Stessa mossa migliore: {100 * R['accordo_mossa_migliore']:.1f}%; mossa di Stockfish fra le prime due di Lc0: {100 * R['mossa_sf_fra_prime_due_lc0']:.1f}%.", '']
    for nome in ('pool', 'top'):
        c = R[f'classificazione_{nome}']
        conf = f"{100 * c['quota_pepite_sf_confermate']:.1f}%" if c['quota_pepite_sf_confermate'] is not None else 'n.d.'
        L.append(f"Classificazione {nome} (Pwin ±{c['soglie']['tolleranza_pwin']}, Delta ≤ {c['soglie']['delta_max']}): "
                 f"entrambi {c['entrambi']}, solo Stockfish {c['solo_sf']}, solo Lc0 {c['solo_lc0']}, nessuno {c['nessuno']}; "
                 f"kappa {c['kappa']:.3f} [{c['kappa_ic'][0]:.3f}; {c['kappa_ic'][1]:.3f}]; pepite di Stockfish confermate: {conf}.")
    with open(args.out + '.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    print('\n'.join(L))
    print(f'\n[OK] Scritti {args.out}.json, {args.out}.md e {args.out}_discordanti.csv')


def main():
    ap = argparse.ArgumentParser(description='Validazione delle pepite con un secondo oracolo')
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('seleziona', help='sceglie le posizioni da rianalizzare con Lc0')
    s.add_argument('--registro', required=True, help='tutte_le_posizioni.csv di Stockfish')
    s.add_argument('--out', required=True, help='CSV da usare come pgn_path in config_lc0.json')
    s.add_argument('--finestra', type=float, default=0.15, help='distanza massima di Pwin dai bersagli (default 0,15)')
    s.add_argument('--max', type=int, default=0, help='numero massimo di posizioni (0 = tutte)')
    c = sub.add_parser('confronta', help='confronta i registri di Stockfish e di Lc0')
    c.add_argument('--sf', required=True)
    c.add_argument('--lc0', required=True)
    c.add_argument('--tol', type=float, default=0.06, help='tolleranza su Pwin per il pool (default 0,06)')
    c.add_argument('--delta-pool', type=float, default=0.06, help='Delta massimo per il pool (default 0,06)')
    c.add_argument('--tol-top', type=float, default=0.03, help='tolleranza su Pwin per le Top-N (default 0,03)')
    c.add_argument('--delta-top', type=float, default=0.03, help='Delta massimo per le Top-N (default 0,03)')
    c.add_argument('--opposite-max', type=float, default=0.0)
    c.add_argument('--out', default='confronto_oracoli')
    args = ap.parse_args()
    {'seleziona': cmd_seleziona, 'confronta': cmd_confronta}[args.cmd](args)


if __name__ == '__main__':
    main()
