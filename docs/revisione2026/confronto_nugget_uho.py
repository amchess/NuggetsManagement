#!/usr/bin/env python3
"""
confronto_nugget_uho.py - controllo UHO (fase E1, analisi S3 e S5): partite decisive sui nugget (match C) e sulle
posizioni UHO di pari Pwin (E1), stesse condizioni di gioco. Confronto grezzo (bootstrap per posizione) e corretto per
la Pwin della parte favorita (regressione logistica con errori robusti per posizione); descrizione della Pwin media di
3 analisi delle UHO (selezione + 2 rianalisi) contro quella dei nugget; ruolo del Delta WDL (esplorativo).
Uso: confronto_nugget_uho.py C.pgn nuggets_pool_robusto.epd E1.pgn uho_250.epd uho_250.csv rianalisi01.csv rianalisi02.csv OUT
"""
import collections, csv, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statistiche_match as sm

c_pgn, c_epd, u_pgn, u_epd, u_sel, r1, r2, out = sys.argv[1:9]
RNG = np.random.default_rng(20261122)

def leggi_reg(p):
    with open(p, newline='', encoding='utf-8') as f:
        return {r['Variante_PGN']: r for r in csv.DictReader(f) if r.get('Stato') in ('Nugget', 'Non nugget')}

mC, metaC = sm.leggi_aperture(c_epd); gC = sm.prepara([c_pgn], mC)
mU, metaU = sm.leggi_aperture(u_epd); gU = sm.prepara([u_pgn], mU)
regs = [leggi_reg(p) for p in (u_sel, r1, r2)]
uho3 = {}
for k in metaU:
    rr = [g[k] for g in regs if k in g]
    pw = [float(r['Pwin1']) for r in rr]; de = [float(r['Delta']) for r in rr]; ll = [float(r['L1']) for r in rr]
    uho3[k] = dict(n=len(rr), pwin=sum(pw) / len(pw), delta=sum(de) / len(de), l=sum(ll) / len(ll), pwin_sel=pw[0])

def pfav_nugget(k):
    p = metaC[k]['Pwin']; return max(p, 1 - p)

righe = []  # (cluster, uho, decisiva, pfav, delta)
for x in gC:
    righe.append((('C', x['ap']), 0, int(x['r'] != '1/2-1/2'), pfav_nugget(x['ap']), metaC[x['ap']]['DeltaWDL']))
for x in gU:
    righe.append((('U', x['ap']), 1, int(x['r'] != '1/2-1/2'), uho3[x['ap']]['pwin'], uho3[x['ap']]['delta']))

def prop(rs): return sum(r[2] for r in rs) / len(rs)
nug = [r for r in righe if r[1] == 0]; uho = [r for r in righe if r[1] == 1]
diff = prop(uho) - prop(nug)
per_cl = collections.defaultdict(list)
for r in righe: per_cl[r[0]].append(r)
clC = [k for k in per_cl if k[0] == 'C']; clU = [k for k in per_cl if k[0] == 'U']
boot = []
for _ in range(5000):
    sc = [per_cl[clC[i]] for i in RNG.integers(0, len(clC), len(clC))]
    su = [per_cl[clU[i]] for i in RNG.integers(0, len(clU), len(clU))]
    a = sum(sum(r[2] for r in g) for g in su) / sum(len(g) for g in su)
    b = sum(sum(r[2] for r in g) for g in sc) / sum(len(g) for g in sc)
    boot.append(a - b)
ic = list(np.percentile(boot, [2.5, 97.5]))

def logit_cluster(X, y, cl):
    b = np.zeros(X.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p)
        H = X.T @ (X * W[:, None]); g = X.T @ (y - p)
        step = np.linalg.solve(H, g); b += step
        if np.max(np.abs(step)) < 1e-10: break
    p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p)
    Hinv = np.linalg.inv(X.T @ (X * W[:, None]))
    gruppi = collections.defaultdict(lambda: np.zeros(X.shape[1]))
    for xi, yi, pi, c in zip(X, y, p, cl): gruppi[c] += xi * (yi - pi)
    G = len(gruppi); M = sum(np.outer(s, s) for s in gruppi.values()) * G / (G - 1)
    V = Hinv @ M @ Hinv
    return b, np.sqrt(np.diag(V))

y = np.array([r[2] for r in righe], float); cl = [r[0] for r in righe]
u = np.array([r[1] for r in righe], float); pf = (np.array([r[3] for r in righe]) - 0.75) * 10; de = np.array([r[4] for r in righe]) * 10
modelli = {}
for nome, X, etich in (('grezzo', np.column_stack([np.ones_like(y), u]), ['costante', 'UHO']),
                       ('pwin', np.column_stack([np.ones_like(y), u, pf]), ['costante', 'UHO', 'Pwin favorita (per 0,1)']),
                       ('pwin_delta', np.column_stack([np.ones_like(y), u, pf, de]), ['costante', 'UHO', 'Pwin favorita (per 0,1)', 'Delta WDL (per 0,1)'])):
    b, es = logit_cluster(X, y, cl)
    modelli[nome] = [dict(termine=t, coef=float(bi), es=float(si), OR=math.exp(bi), OR_ic=[math.exp(bi - 1.96 * si), math.exp(bi + 1.96 * si)],
                          p=float(2 * (1 - __import__('scipy.stats', fromlist=['norm']).norm.cdf(abs(bi / si))))) for t, bi, si in zip(etich, b, es)]

pn = [pfav_nugget(k) for k in metaC]; pu = [uho3[k]['pwin'] for k in metaU]; pus = [uho3[k]['pwin_sel'] for k in metaU]
dn = [metaC[k]['DeltaWDL'] for k in metaC]; du = [uho3[k]['delta'] for k in metaU]
lu = [uho3[k]['l'] for k in metaU]
desc = dict(nugget=dict(posizioni=len(pn), pwin_media=float(np.mean(pn)), pwin_mediana=float(np.median(pn)), delta_mediana=float(np.median(dn))),
            uho=dict(posizioni=len(pu), analisi=sorted(set(uho3[k]['n'] for k in metaU)), pwin_media_selezione=float(np.mean(pus)),
                     pwin_media_3=float(np.mean(pu)), pwin_mediana_3=float(np.median(pu)), delta_mediana_3=float(np.median(du)),
                     fuori_fascia_3=int(sum(abs(p - 0.75) > 0.06 for p in pu)), l_media_3=float(np.mean(lu)), l_positiva_3=int(sum(l > 0 for l in lu))))
ris = dict(decisive=dict(nugget=[sum(r[2] for r in nug), len(nug), prop(nug)], uho=[sum(r[2] for r in uho), len(uho), prop(uho)],
                         differenza=diff, ic_bootstrap=ic), modelli=modelli, descrizione=desc)
json.dump(ris, open(out + '.json', 'w'), indent=1)
L = ['# Controllo UHO (E1): nugget contro UHO di pari Pwin, stesse condizioni (25\'+10", Stockfish 19 - ShashChess 42.3)', '',
     f"- Partite decisive: nugget (match C) {ris['decisive']['nugget'][0]}/{ris['decisive']['nugget'][1]} ({100*prop(nug):.1f}%), "
     f"UHO (E1) {ris['decisive']['uho'][0]}/{ris['decisive']['uho'][1]} ({100*prop(uho):.1f}%); differenza UHO - nugget {100*diff:+.1f} punti, "
     f"IC 95% bootstrap per posizione [{100*ic[0]:+.1f}; {100*ic[1]:+.1f}]",
     f"- Pwin della parte favorita, media di 3 analisi: nugget {desc['nugget']['pwin_media']:.3f} (mediana {desc['nugget']['pwin_mediana']:.3f}); "
     f"UHO {desc['uho']['pwin_media_3']:.3f} (mediana {desc['uho']['pwin_mediana_3']:.3f}; alla selezione {desc['uho']['pwin_media_selezione']:.3f}); "
     f"UHO fuori fascia con la media di 3 analisi: {desc['uho']['fuori_fascia_3']}/{desc['uho']['posizioni']}",
     f"- L della parte favorita nelle UHO (media di 3 analisi): media {desc['uho']['l_media_3']:.4f}; posizioni con L > 0: {desc['uho']['l_positiva_3']}",
     f"- Delta WDL mediano (media di 3 analisi): nugget {desc['nugget']['delta_mediana']:.3f}, UHO {desc['uho']['delta_mediana_3']:.3f}", '',
     '| Modello (logistico, errori robusti per posizione) | Termine | OR [IC 95%] | p |', '|---|---|---|---|']
for nome, termini in modelli.items():
    for t in termini[1:]:
        L.append(f"| {nome} | {t['termine']} | {t['OR']:.2f} [{t['OR_ic'][0]:.2f}; {t['OR_ic'][1]:.2f}] | {t['p']:.4f} |")
open(out + '.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
