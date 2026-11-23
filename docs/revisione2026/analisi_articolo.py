#!/usr/bin/env python3
"""
analisi_articolo.py - analisi dell'articolo non contenute negli altri script.

  1. ShashChess - Stockfish per fascia di Pwin della parte favorita (Tabella 5 dell'articolo,
     esplorativa): Elo pentanomiale per fascia e pendenza del punteggio di coppia su Pwin, con
     errori robusti per posizione, convertita in Elo a punteggio 50%.
  2. Regressione logistica comune delle partite decisive su Pwin (Figura 4): un'intercetta per
     fase (C, E1, E4) e una pendenza comune, errori robusti per posizione. Per le UHO la Pwin e'
     la media delle 3 analisi (--uho-registri), per i nugget quella del file .epd (gia' media di 3).
  3. Composizione per fase di gioco e struttura del centro di candidate, nugget robusti, pool e
     Top-100 (Sezione 4).

Le cartelle di fase sono quelle scritte da match_nuggets2026.sh / roundrobin_nuggets2026.sh
(partite*.pgn piu' il file .epd delle posizioni). Uso, dalla cartella docs/revisione2026:

  python analisi_articolo.py \
     --c  risultati/20261118_2057_pool_robusto \
     --d  risultati/20261120_0014_rr_top100_robusto \
     --e1 risultati/20261121_1156_controllo_uho \
     --e4 risultati/20261121_1045_pool_tc60 \
     [--e5 risultati/<data>_pool_tc3600] \
     --uho-registri posizioni/uho_250.csv registri/uho_rianalisi01.csv registri/uho_rianalisi02.csv \
     --posizioni posizioni --out rapporti/analisi_articolo

I file .pgn e .csv possono essere anche compressi (.gz).
"""
import argparse, collections, csv, glob, gzip, io, json, math, os, sys

import numpy as np
from scipy import stats as sps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statistiche_match as sm

A, B = 'ShashChess42.3', 'Stockfish19'
FASCE = [(0.69, 0.72), (0.72, 0.75), (0.75, 0.78), (0.78, 0.82)]
EPS = 1e-9
K_ELO = 400 / math.log(10) / 0.25   # punti di punteggio -> Elo, vicino al 50%


def apri(p):
    return io.TextIOWrapper(gzip.open(p), encoding='utf-8-sig') if p.endswith('.gz') else open(p, encoding='utf-8-sig')


def pgn_in_chiaro(paths, tmp):
    """statistiche_match legge file di testo: decomprime gli eventuali .pgn.gz in una cartella temporanea."""
    out = []
    for p in paths:
        if p.endswith('.gz'):
            q = os.path.join(tmp, os.path.basename(p)[:-3])
            with gzip.open(p, 'rb') as f, open(q, 'wb') as g:
                g.write(f.read())
            out.append(q)
        else:
            out.append(p)
    return out


def file_fase(cartella, schema_pgn):
    pgn = sorted(glob.glob(os.path.join(cartella, schema_pgn)) + glob.glob(os.path.join(cartella, schema_pgn + '.gz')))
    epd = sorted(glob.glob(os.path.join(cartella, '*.epd')))
    if not pgn or len(epd) != 1:
        sys.exit(f'[ERRORE] {cartella}: servono partite ({schema_pgn}) e un solo file .epd')
    return pgn, epd[0]


def coppie_sc_sf(cartella, schema_pgn, nome, tmp):
    pgn, epd = file_fase(cartella, schema_pgn)
    mappa, meta = sm.leggi_aperture(epd)
    partite = sm.prepara(pgn_in_chiaro(pgn, tmp), mappa)
    coppie, _ = sm.forma_coppie(partite)
    righe = []
    for c in coppie:
        if {c[0]['w'], c[0]['b']} != {A, B}:
            continue
        pw = meta[c[0]['ap']]['Pwin']
        righe.append(dict(ap=c[0]['ap'], pf=max(pw, 1 - pw), s=sum(x['sw'] if x['w'] == A else 1 - x['sw'] for x in c), esp=nome))
    return righe, partite, meta


def ols_cluster(y, X, cl):
    X = np.asarray(X, float); y = np.asarray(y, float)
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    gruppi = collections.defaultdict(list)
    for i, g in enumerate(cl):
        gruppi[g].append(i)
    meat = sum(np.outer(X[ix].T @ e[ix], X[ix].T @ e[ix]) for ix in gruppi.values())
    G = len(gruppi)
    return b, np.sqrt(np.diag(XtXi @ meat @ XtXi * G / (G - 1)))


def logit_cluster(X, y, cl, it=60):
    X = np.asarray(X, float); y = np.asarray(y, float)
    b = np.zeros(X.shape[1])
    for _ in range(it):
        mu = 1 / (1 + np.exp(-X @ b))
        b = b + np.linalg.solve(X.T @ (X * (mu * (1 - mu))[:, None]), X.T @ (y - mu))
    mu = 1 / (1 + np.exp(-X @ b))
    Hi = np.linalg.inv(X.T @ (X * (mu * (1 - mu))[:, None]))
    gruppi = collections.defaultdict(list)
    for i, g in enumerate(cl):
        gruppi[g].append(i)
    meat = sum(np.outer(X[ix].T @ (y[ix] - mu[ix]), X[ix].T @ (y[ix] - mu[ix])) for ix in gruppi.values())
    G = len(gruppi)
    return b, np.sqrt(np.diag(Hi @ meat @ Hi * G / (G - 1))), G


def uho_media3(paths):
    regs = []
    for p in paths:
        with apri(p) as f:
            regs.append({r['Variante_PGN']: float(r['Pwin1']) for r in csv.DictReader(f) if r['Stato'] in ('Nugget', 'Non nugget')})
    return {k: float(np.mean([r[k] for r in regs if k in r])) for k in regs[0]}


def composizione(cartella):
    def leggi(n):
        with apri(os.path.join(cartella, n)) as f:
            return list(csv.DictReader(f))

    def robusto(r):
        p, d = float(r['WIN_PROBABILITY']), float(r['Delta_Win_Probability'])
        if abs(p - 0.75) <= 0.06 + EPS:
            return float(r['L1']) <= EPS and d <= 0.06 + EPS
        if abs(p - 0.25) <= 0.06 + EPS:
            return float(r['W1']) <= EPS and d <= 0.06 + EPS
        return False
    cand = leggi('medie_3analisi.csv')
    insiemi = dict(candidate=cand, robusti=[r for r in cand if robusto(r)],
                   pool=leggi('nuggets_pool_robusto.csv'), top100=leggi('nuggets_top100_robusto.csv'))
    out = {}
    for nome, rs in insiemi.items():
        n = len(rs)
        out[nome] = dict(posizioni=n,
                         fase={k: [v, round(100 * v / n, 1)] for k, v in collections.Counter(r['Fase'] for r in rs).most_common()},
                         centro={k: [v, round(100 * v / n, 1)] for k, v in collections.Counter(r['Centro'] for r in rs).most_common()},
                         analisi_pepita=dict(collections.Counter(r['Pepita_in'] for r in rs)),
                         mossa_stabile=sum(r['Mossa_stabile'] == '1' for r in rs))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ('c', 'd', 'e1', 'e4'):
        ap.add_argument('--' + k, required=True, help=f'cartella della fase {k.upper()}')
    ap.add_argument('--e5', help='cartella della fase E5 (facoltativa)')
    ap.add_argument('--uho-registri', nargs=3, required=True, help='tre registri delle analisi delle UHO (selezione + 2 rianalisi)')
    ap.add_argument('--posizioni', required=True, help='cartella posizioni/ (medie_3analisi.csv, nuggets_pool_robusto.csv, nuggets_top100_robusto.csv)')
    ap.add_argument('--out', default='analisi_articolo')
    args = ap.parse_args()

    import tempfile
    tmp = tempfile.mkdtemp(prefix='articolo_')
    fasi = [('C', args.c, 'partite*.pgn'), ('D', args.d, 'partite_Stockfish19_ShashChess42.3.pgn'),
            ('E4', args.e4, 'partite*.pgn'), ('E1', args.e1, 'partite*.pgn')]
    if args.e5:
        fasi.append(('E5', args.e5, 'partite*.pgn'))

    R = dict(per_fascia={}, logistica=None, composizione=None)
    dati = {}
    for nome, cart, schema in fasi:
        righe, partite, meta = coppie_sc_sf(cart, schema, nome, tmp)
        dati[nome] = (partite, meta)
        F = []
        for lo, hi in FASCE:
            sel = [r for r in righe if lo <= r['pf'] < hi]
            if not sel:
                continue
            P = sm.pentanomiale([r['s'] for r in sel])
            F.append(dict(fascia=f'{lo:.2f}-{hi:.2f}', posizioni=len({r['ap'] for r in sel}), coppie=len(sel),
                          elo=P['elo'], inf=P['elo_inf'], sup=P['elo_sup'], p=P['p']))
        b, es = ols_cluster([r['s'] / 2 for r in righe], [[1.0, (r['pf'] - 0.75) / 0.1] for r in righe], [r['ap'] for r in righe])
        R['per_fascia'][nome] = dict(coppie=len(righe), fasce=F,
                                     andamento=dict(elo_per_0_1=b[1] * K_ELO, inf=(b[1] - 1.96 * es[1]) * K_ELO,
                                                    sup=(b[1] + 1.96 * es[1]) * K_ELO, p=float(2 * sps.norm.sf(abs(b[1] / es[1])))))

    # logistica comune delle partite decisive (C, E1, E4)
    m3 = uho_media3(args.uho_registri)
    X, y, cl = [], [], []
    for i, nome in enumerate(('C', 'E1', 'E4')):
        partite, meta = dati[nome]
        for x in partite:
            if nome == 'E1':
                p = m3[x['ap']]
            else:
                pw = meta[x['ap']]['Pwin']
                p = max(pw, 1 - pw)
            X.append([i == 0, i == 1, i == 2, (p - 0.75) * 10]); y.append(x['r'] != '1/2-1/2'); cl.append((nome, x['ap']))
    b, es, G = logit_cluster(X, y, cl)
    R['logistica'] = dict(partite=len(y), posizioni=G, intercette=dict(C=b[0], E1=b[1], E4=b[2]), pendenza_per_0_1=b[3], es=es[3],
                          OR=math.exp(b[3]), OR_inf=math.exp(b[3] - 1.96 * es[3]), OR_sup=math.exp(b[3] + 1.96 * es[3]),
                          p=float(2 * sps.norm.sf(abs(b[3] / es[3]))))
    R['composizione'] = composizione(args.posizioni)

    with open(args.out + '.json', 'w', encoding='utf-8') as f:
        json.dump(R, f, indent=1, ensure_ascii=False, default=float)
    L = ['# Analisi dell\'articolo', '', '## ShashChess - Stockfish per fascia di Pwin della parte favorita (esplorativa)', '',
         '| Fase | ' + ' | '.join(f'{lo:.2f}-{hi:.2f}' for lo, hi in FASCE) + ' | Andamento per 0,1 |',
         '|---|' + '---|' * (len(FASCE) + 1)]
    for nome, v in R['per_fascia'].items():
        celle = {f['fascia']: f"{f['elo']:+.1f} [{f['inf']:+.1f}; {f['sup']:+.1f}] ({f['coppie']})" for f in v['fasce']}
        a = v['andamento']
        L.append(f'| {nome} | ' + ' | '.join(celle.get(f'{lo:.2f}-{hi:.2f}', '-') for lo, hi in FASCE)
                 + f" | {a['elo_per_0_1']:+.1f} [{a['inf']:+.1f}; {a['sup']:+.1f}], p = {a['p']:.3f} |")
    g = R['logistica']
    L += ['', '## Partite decisive e Pwin (C, E1, E4)', '',
          f"Partite {g['partite']}, posizioni {g['posizioni']}; odds ratio per 0,1 di Pwin: {g['OR']:.2f} "
          f"[{g['OR_inf']:.2f}; {g['OR_sup']:.2f}], p = {g['p']:.2g}", '', '## Composizione (Sezione 4)', '']
    for nome, v in R['composizione'].items():
        fasi_txt = ', '.join(f'{k} {c[0]} ({c[1]}%)' for k, c in v['fase'].items())
        centro_txt = ', '.join(f'{k} {c[0]} ({c[1]}%)' for k, c in v['centro'].items())
        L += [f"- {nome} ({v['posizioni']}): {fasi_txt}", f"  - centro: {centro_txt}",
              f"  - analisi singole che la classificano pepita: {v['analisi_pepita']}; mossa migliore stabile: {v['mossa_stabile']}"]
    with open(args.out + '.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))
    print(f'\n[OK] Scritti {args.out}.json e {args.out}.md')


if __name__ == '__main__':
    main()
