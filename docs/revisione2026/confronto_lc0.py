#!/usr/bin/env python3
"""
confronto_lc0.py - fase B, confronto pre-registrato (PREREGISTRAZIONE_B_E5.md) fra Stockfish 19 (media di 3 analisi,
posizioni/medie_3analisi.csv) e Lc0 (registro tutte_le_posizioni.csv) sulle 2.321 posizioni candidate:
rho di Spearman e Bland-Altman per Pwin e Delta, accordo sulla mossa migliore, classificazione nugget (Lc0 senza la
condizione L = 0), kappa di Cohen, quota di nugget confermati, probabilita' di vittoria della parte sfavorita secondo
Lc0; secondaria S4: risultati del match C per nugget di consenso e solo-Stockfish.
Uso: confronto_lc0.py medie_3analisi.csv lc0/tutte_le_posizioni.csv C.pgn nuggets_pool_robusto.epd OUT
"""
import collections, csv, json, math, os, sys
import numpy as np
from scipy import stats as sps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statistiche_match as sm

f_sf, f_lc0, c_pgn, c_epd, out = sys.argv[1:6]
EPS, TOL, DMAX = 1e-9, 0.06, 0.06
sf = {r['FEN']: r for r in csv.DictReader(open(f_sf, encoding='utf-8-sig'))}
lc = {r['FEN']: r for r in csv.DictReader(open(f_lc0, encoding='utf-8')) if r.get('W1') not in (None, '')}
fen = sorted(set(sf) & set(lc))
f = lambda r, k: float(r[k])
ps, pl = np.array([f(sf[x], 'WIN_PROBABILITY') for x in fen]), np.array([f(lc[x], 'Pwin1') for x in fen])
ds, dl = np.array([f(sf[x], 'Delta_Win_Probability') for x in fen]), np.array([f(lc[x], 'Delta') for x in fen])

def ba(a, b):
    d = b - a; m, s = float(d.mean()), float(d.std(ddof=1)); return dict(media=m, ds=s, lim=[m - 1.96 * s, m + 1.96 * s])

def fascia(p):  # +1 favorito il Bianco, -1 il Nero, 0 fuori fascia
    return 1 if abs(p - 0.75) <= TOL + EPS else (-1 if abs(p - 0.25) <= TOL + EPS else 0)

def sf_nugget(r, con_l=True):
    p, d = f(r, 'WIN_PROBABILITY'), f(r, 'Delta_Win_Probability'); s = fascia(p)
    if s == 0 or d > DMAX + EPS: return False
    if not con_l: return True
    return (f(r, 'L1') <= EPS) if s == 1 else (f(r, 'W1') <= EPS)

def lc_nugget(r):
    return fascia(f(r, 'Pwin1')) != 0 and f(r, 'Delta') <= DMAX + EPS

def kappa(a, b):
    a, b = np.array(a, bool), np.array(b, bool); n = len(a); po = float((a == b).mean())
    pe = float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())); return dict(kappa=(po - pe) / (1 - pe), accordo=po,
        tabella=dict(entrambi=int((a & b).sum()), solo_sf=int((a & ~b).sum()), solo_lc0=int((~a & b).sum()), nessuno=int((~a & ~b).sum())))

def kappa_ic(a, b, rng=np.random.default_rng(20261122), B=2000):
    a, b = np.array(a, bool), np.array(b, bool); k = []
    for _ in range(B):
        i = rng.integers(0, len(a), len(a)); k.append(kappa(a[i], b[i])['kappa'])
    return list(np.percentile(k, [2.5, 97.5]))

mossa = [lc[x]['Mossa1'] in set(sf[x]['Mosse_migliori'].split('/')) for x in fen]
stabile = [sf[x]['Mossa_stabile'] == '1' for x in fen]
sfn = [sf_nugget(sf[x]) for x in fen]; sfn_nol = [sf_nugget(sf[x], False) for x in fen]; lcn = [lc_nugget(lc[x]) for x in fen]
banda_sf = [fascia(f(sf[x], 'WIN_PROBABILITY')) != 0 for x in fen]; banda_lc = [fascia(f(lc[x], 'Pwin1')) != 0 for x in fen]

def sfavorita_lc0(x):  # probabilita' di vittoria della parte sfavorita (per Stockfish) secondo Lc0
    s = 1 if f(sf[x], 'WIN_PROBABILITY') > 0.5 else -1; return f(lc[x], 'L1') if s == 1 else f(lc[x], 'W1')
sv_nug = [sfavorita_lc0(x) for x, n in zip(fen, sfn) if n]; sv_all = [sfavorita_lc0(x) for x in fen]

R = dict(posizioni=len(fen), nodi_mediani=float(np.median([f(lc[x], 'Nodi') for x in fen])),
         pwin=dict(spearman=list(sps.spearmanr(ps, pl)), pearson=list(sps.pearsonr(ps, pl)), bland_altman=ba(ps, pl)),
         delta=dict(spearman=list(sps.spearmanr(ds, dl)), bland_altman=ba(ds, dl), mediana_sf=float(np.median(ds)), mediana_lc0=float(np.median(dl))),
         mossa=dict(accordo=float(np.mean(mossa)), accordo_mossa_stabile=float(np.mean([m for m, s in zip(mossa, stabile) if s])), n_stabile=int(sum(stabile))),
         nugget_preregistrato=dict(**kappa(sfn, lcn), kappa_ic=kappa_ic(sfn, lcn), nugget_sf=int(sum(sfn)), nugget_lc0=int(sum(lcn))),
         nugget_senza_L=dict(**kappa(sfn_nol, lcn), kappa_ic=kappa_ic(sfn_nol, lcn), nugget_sf=int(sum(sfn_nol))),
         fascia_pwin=dict(**kappa(banda_sf, banda_lc), in_fascia_sf=int(sum(banda_sf)), in_fascia_lc0=int(sum(banda_lc))),
         sfavorita_lc0=dict(nugget_sf=dict(n=len(sv_nug), mediana=float(np.median(sv_nug)), q1=float(np.percentile(sv_nug, 25)), q3=float(np.percentile(sv_nug, 75)), zero=int(sum(v <= EPS for v in sv_nug))),
                            tutte=dict(mediana=float(np.median(sv_all)), q1=float(np.percentile(sv_all, 25)), q3=float(np.percentile(sv_all, 75)))))
R['nugget_preregistrato']['confermati'] = R['nugget_preregistrato']['tabella']['entrambi'] / max(1, R['nugget_preregistrato']['nugget_sf'])

# S4: match C per nugget di consenso e solo-Stockfish
mappa, meta = sm.leggi_aperture(c_epd); g = sm.prepara([c_pgn], mappa)
fen_id = {}
for line in open(c_epd, encoding='utf-8'):
    if '/' in line.split(' ')[0]:
        parti = line.split(); k = line.split('id "')[1].split('"')[0]; fen_id[k] = ' '.join(parti[:4])
fen4 = {' '.join(x.split()[:4]): x for x in fen}
cons = {k: lc_nugget(lc[fen4[v]]) for k, v in fen_id.items() if v in fen4}
coppie, _ = sm.forma_coppie(g)
s4 = {}
for nome, sel in (('consenso', True), ('solo_stockfish', False)):
    ks = {k for k, v in cons.items() if v == sel}
    gg = [x for x in g if x['ap'] in ks]; dec = sum(x['r'] != '1/2-1/2' for x in gg)
    pc = [sum(x['sw'] if x['w'] == 'ShashChess42.3' else 1 - x['sw'] for x in c) for c in coppie if c[0]['ap'] in ks]
    pen = sm.pentanomiale(pc) if pc else None
    s4[nome] = dict(posizioni=len(ks), partite=len(gg), decisive=dec, quota=dec / len(gg) if gg else None,
                    elo_sc_sf=pen['elo'] if pen else None, elo_ic=[pen['elo_inf'], pen['elo_sup']] if pen else None)
R['s4_match_c'] = s4; R['s4_match_c']['mappate'] = len(cons)
json.dump(R, open(out + '.json', 'w'), indent=1, default=float)

p, d, m, n1, n2, fp = R['pwin'], R['delta'], R['mossa'], R['nugget_preregistrato'], R['nugget_senza_L'], R['fascia_pwin']
sv = R['sfavorita_lc0']
L = ['# Fase B: Lc0 (t3-512x15x16h, 10.000 nodi) contro Stockfish 19 (media di 3 analisi)', '',
     f"- Posizioni: {R['posizioni']}; nodi mediani per posizione: {R['nodi_mediani']:.0f}",
     f"- Pwin della mossa migliore: rho di Spearman {p['spearman'][0]:.3f} (r di Pearson {p['pearson'][0]:.3f}); Bland-Altman Lc0 - Stockfish: "
     f"media {p['bland_altman']['media']:+.3f}, limiti al 95% [{p['bland_altman']['lim'][0]:+.3f}; {p['bland_altman']['lim'][1]:+.3f}]",
     f"- Delta WDL: rho di Spearman {d['spearman'][0]:.3f} (p = {d['spearman'][1]:.2g}); mediana Stockfish {d['mediana_sf']:.3f}, Lc0 {d['mediana_lc0']:.3f}; "
     f"Bland-Altman media {d['bland_altman']['media']:+.3f}, limiti [{d['bland_altman']['lim'][0]:+.3f}; {d['bland_altman']['lim'][1]:+.3f}]",
     f"- Mossa migliore di Lc0 fra le migliori delle 3 analisi di Stockfish: {100*m['accordo']:.1f}% (posizioni con mossa stabile per Stockfish, {m['n_stabile']}: {100*m['accordo_mossa_stabile']:.1f}%)",
     f"- Fascia di Pwin (0,75 o 0,25 +/- 0,06): Stockfish {fp['in_fascia_sf']}, Lc0 {fp['in_fascia_lc0']}, entrambi {fp['tabella']['entrambi']}; kappa {fp['kappa']:.3f}",
     f"- Nugget (pre-registrato; Stockfish con L = 0, Lc0 senza): Stockfish {n1['nugget_sf']}, Lc0 {n1['nugget_lc0']}, entrambi {n1['tabella']['entrambi']} "
     f"(confermati {100*n1['confermati']:.1f}%); kappa {n1['kappa']:.3f} [IC 95% {n1['kappa_ic'][0]:.3f}; {n1['kappa_ic'][1]:.3f}]",
     f"- Nugget con lo stesso criterio per i due oracoli (fascia + Delta, senza L): Stockfish {n2['nugget_sf']}, entrambi {n2['tabella']['entrambi']}; kappa {n2['kappa']:.3f} [{n2['kappa_ic'][0]:.3f}; {n2['kappa_ic'][1]:.3f}]",
     f"- Probabilita' di vittoria della parte sfavorita secondo Lc0: nei {sv['nugget_sf']['n']} nugget di Stockfish mediana {sv['nugget_sf']['mediana']:.3f} "
     f"(Q1 {sv['nugget_sf']['q1']:.3f}, Q3 {sv['nugget_sf']['q3']:.3f}; zero in {sv['nugget_sf']['zero']}); in tutte le candidate mediana {sv['tutte']['mediana']:.3f}",
     f"- S4, match C ({R['s4_match_c']['mappate']} posizioni del pool): nugget di consenso {s4['consenso']['posizioni']} posizioni, decisive "
     f"{s4['consenso']['decisive']}/{s4['consenso']['partite']} ({100*(s4['consenso']['quota'] or 0):.1f}%), ShashChess - Stockfish "
     f"{s4['consenso']['elo_sc_sf']:+.1f} [{s4['consenso']['elo_ic'][0]:+.1f}; {s4['consenso']['elo_ic'][1]:+.1f}]; solo-Stockfish {s4['solo_stockfish']['posizioni']} posizioni, decisive "
     f"{s4['solo_stockfish']['decisive']}/{s4['solo_stockfish']['partite']} ({100*(s4['solo_stockfish']['quota'] or 0):.1f}%), ShashChess - Stockfish "
     f"{s4['solo_stockfish']['elo_sc_sf']:+.1f} [{s4['solo_stockfish']['elo_ic'][0]:+.1f}; {s4['solo_stockfish']['elo_ic'][1]:+.1f}]"]
open(out + '.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
