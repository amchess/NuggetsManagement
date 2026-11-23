#!/usr/bin/env python3
"""
analisi_f.py - fase F (Pfav da 0,55 a 0,95): le analisi fissate in PREREGISTRAZIONE_F.md.

Primaria: pendenza del punteggio di coppia di ShashChess (punti/2, da 0 a 1) su (Pfav - 0,75)/0,1, minimi
quadrati con errori standard HC1, test bilaterale ad alfa = 0,05; la pendenza si riporta anche in Elo per 0,1
di Pfav, convertita al punteggio del 50%.
Secondarie:
  S1  Elo pentanomiale ShashChess - Stockfish per fascia e su tutte le posizioni, con IC 95%;
  S2  quota di partite decise per fascia (Wilson) e regressione logistica delle partite decise su Pfav,
      odds ratio per 0,1 con errori robusti per posizione;
  S3  partite vinte dalla parte sfavorita, per fascia;
  S4  correlazione di Spearman fra la quota di partite decise della posizione e Delta WDL (descrittiva).
Esplorativa: ShashChess - Stockfish per zona di Shashin della parte favorita (dalla Pfav dell'oracolo).

Uso (dalla cartella docs/revisione2026):
  python analisi_f.py --f risultati/<data>_fasce_tc1500 --posizioni posizioni/fasce_320.csv \
     --out rapporti/statistiche_f
La cartella della fase contiene le partite (partite*.pgn, anche .gz) e il file .epd delle posizioni, come le
scrive match_nuggets2026.sh.
"""
import argparse, collections, csv, json, math, os, sys, tempfile

import numpy as np
from scipy import stats as sps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statistiche_match as sm
from analisi_articolo import K_ELO, file_fase, logit_cluster, pgn_in_chiaro

A, B = 'ShashChess42.3', 'Stockfish19'
FASCE = ['0.55-0.65', '0.65-0.75', '0.75-0.85', '0.85-0.95']
# zone di Shashin per probabilita' di vittoria intera (shashin_types.h); la parte favorita va da 55 a 94
ZONE = [(75, 'Capablanca-Tal'), (79, 'Low Tal'), (84, 'Middle-Low Tal'), (89, 'Middle Tal'),
        (94, 'Middle-High Tal'), (100, 'High Tal')]


def zona(pf):
    p = int(round(100 * pf))
    return next(nome for lim, nome in ZONE if p <= lim)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'),) * 2
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


def ols_hc1(y, x):
    X = np.column_stack([np.ones(len(x)), np.asarray(x, float)])
    y = np.asarray(y, float)
    n, k = X.shape
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    V = XtXi @ (X.T * e ** 2) @ X @ XtXi * n / (n - k)
    return b, np.sqrt(np.diag(V))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--f', required=True, help='cartella della fase F')
    ap.add_argument('--posizioni', required=True, help='posizioni/fasce_320.csv scritto da seleziona_fasce.py')
    ap.add_argument('--out', default='statistiche_f')
    a = ap.parse_args()

    with open(a.posizioni, encoding='utf-8-sig') as f:
        info = {r['id']: r for r in csv.DictReader(f)}
    pgn, epd = file_fase(a.f, 'partite*.pgn')
    mappa, _ = sm.leggi_aperture(epd)
    partite = sm.prepara(pgn_in_chiaro(pgn, tempfile.mkdtemp(prefix='fase_f_')), mappa)
    partite = [x for x in partite if {x['w'], x['b']} == {A, B}]
    sconosciute = sorted({x['ap'] for x in partite if x['ap'] not in info})
    if sconosciute:
        sys.exit(f'[ERRORE] posizioni delle partite assenti da {a.posizioni}: {sconosciute[:5]}')
    coppie, spaiate = sm.forma_coppie(partite)

    def pos(ap_id):
        r = info[ap_id]
        return dict(pf=float(r['Pfav']), fascia=r['Fascia'], delta=float(r['Delta']), bianco_fav=float(r['Pwin']) >= 0.5)

    R = dict(posizioni_previste=len(info), partite=len(partite), coppie=len(coppie), partite_spaiate=spaiate)

    # ---------------------------------------------------------------- primaria
    righe = []
    for c in coppie:
        s = sum(x['sw'] if x['w'] == A else 1 - x['sw'] for x in c)
        righe.append(dict(ap=c[0]['ap'], s=s, **pos(c[0]['ap'])))
    b, es = ols_hc1([r['s'] / 2 for r in righe], [(r['pf'] - 0.75) / 0.1 for r in righe])
    z = b[1] / es[1]
    R['primaria'] = dict(coppie=len(righe), intercetta=b[0], pendenza=b[1], es=es[1], z=z,
                         p=float(2 * sps.norm.sf(abs(z))), elo_per_0_1=b[1] * K_ELO,
                         elo_inf=(b[1] - 1.96 * es[1]) * K_ELO, elo_sup=(b[1] + 1.96 * es[1]) * K_ELO,
                         sd_pfav=float(np.std([r['pf'] for r in righe])))

    # ---------------------------------------------------------------- S1
    def penta(sel):
        if not sel:
            return None
        P = sm.pentanomiale([r['s'] for r in sel])
        return dict(coppie=P['coppie'], conteggi=P['conteggi'], elo=P['elo'], inf=P['elo_inf'], sup=P['elo_sup'], p=P['p'])
    R['S1'] = dict(totale=penta(righe), fasce={fz: penta([r for r in righe if r['fascia'] == fz]) for fz in FASCE})

    # ---------------------------------------------------------------- S2, S3
    giochi = []
    for x in partite:
        p = pos(x['ap'])
        dec = x['r'] != '1/2-1/2'
        vince_bianco = x['r'] == '1-0'
        fav = x['w'] if p['bianco_fav'] else x['b']
        sfav_vince = dec and (vince_bianco != p['bianco_fav'])
        fav_vince = dec and not sfav_vince
        giochi.append(dict(ap=x['ap'], dec=dec, fav=fav, fav_vince=fav_vince, sfav_vince=sfav_vince,
                           vincitore=(x['w'] if vince_bianco else x['b']) if dec else None, **p))
    S2, S3 = {}, {}
    for fz in FASCE + ['totale']:
        g = giochi if fz == 'totale' else [x for x in giochi if x['fascia'] == fz]
        n, k = len(g), sum(x['dec'] for x in g)
        lo, hi = wilson(k, n)
        S2[fz] = dict(partite=n, decise=k, quota=k / n if n else float('nan'), inf=lo, sup=hi)
        ks = sum(x['sfav_vince'] for x in g)
        lo, hi = wilson(ks, n)
        conv = {e: [sum(x['fav_vince'] for x in g if x['fav'] == e), sum(x['fav'] == e for x in g)] for e in (A, B)}
        S3[fz] = dict(partite=n, vinte_sfavorita=ks, quota=ks / n if n else float('nan'), inf=lo, sup=hi,
                      vinte_sfavorita_da={e: sum(x['sfav_vince'] and x['vincitore'] == e for x in g) for e in (A, B)},
                      conversioni_favorita=conv)
    bl, el, G = logit_cluster([[1.0, (x['pf'] - 0.75) * 10] for x in giochi], [x['dec'] for x in giochi],
                              [x['ap'] for x in giochi])
    S2['logistica'] = dict(partite=len(giochi), posizioni=G, pendenza_per_0_1=bl[1], es=el[1], OR=math.exp(bl[1]),
                           OR_inf=math.exp(bl[1] - 1.96 * el[1]), OR_sup=math.exp(bl[1] + 1.96 * el[1]),
                           p=float(2 * sps.norm.sf(abs(bl[1] / el[1]))))
    R['S2'], R['S3'] = S2, S3

    # ---------------------------------------------------------------- S4 (e Pfav, descrittiva)
    perpos = collections.defaultdict(list)
    for x in giochi:
        perpos[x['ap']].append(x)
    q = [(sum(x['dec'] for x in g) / len(g), g[0]['delta'], g[0]['pf']) for g in perpos.values()]
    rd = sps.spearmanr([v[0] for v in q], [v[1] for v in q])
    rp = sps.spearmanr([v[0] for v in q], [v[2] for v in q])
    R['S4'] = dict(posizioni=len(q), rho_delta=float(rd.statistic), p_delta=float(rd.pvalue),
                   rho_pfav=float(rp.statistic), p_pfav=float(rp.pvalue),
                   sempre_patte=sum(v[0] == 0 for v in q), sempre_decise=sum(v[0] == 1 for v in q))

    # ---------------------------------------------------------------- esplorativa: zona di Shashin
    R['esplorativa_zone'] = {}
    for _, nome in ZONE:
        sel = [r for r in righe if zona(r['pf']) == nome]
        if sel:
            R['esplorativa_zone'][nome] = penta(sel)

    with open(a.out + '.json', 'w', encoding='utf-8') as f:
        json.dump(R, f, indent=1, ensure_ascii=False, default=float)

    # ---------------------------------------------------------------- rapporto
    P = R['primaria']
    L = ['# Fase F: Pfav da 0,55 a 0,95', '',
         f"Partite {R['partite']}, coppie {R['coppie']} (posizioni previste {R['posizioni_previste']}, partite spaiate {spaiate}).", '',
         '## Ipotesi primaria (pre-registrata)', '',
         f"Pendenza del punteggio di coppia di ShashChess su (Pfav - 0,75)/0,1: {P['pendenza']:+.4f} (ES HC1 {P['es']:.4f}), "
         f"z = {P['z']:+.2f}, p = {P['p']:.3f}.",
         f"In Elo per 0,1 di Pfav: {P['elo_per_0_1']:+.1f} [{P['elo_inf']:+.1f}; {P['elo_sup']:+.1f}]. "
         f"Deviazione standard di Pfav: {P['sd_pfav']:.3f}.", '',
         '## S1: Elo pentanomiale ShashChess - Stockfish', '',
         '| Fascia | Coppie | 0 / ½ / 1 / 1½ / 2 | Elo [IC 95%] | p |', '|---|---|---|---|---|']
    for fz in FASCE + ['totale']:
        v = R['S1']['totale'] if fz == 'totale' else R['S1']['fasce'][fz]
        if v is None:
            L.append(f'| {fz} | 0 | - | - | - |')
            continue
        L.append(f"| {fz} | {v['coppie']} | {' / '.join(str(c) for c in v['conteggi'])} | "
                 f"{v['elo']:+.1f} [{v['inf']:+.1f}; {v['sup']:+.1f}] | {v['p']:.3f} |")
    L += ['', '## S2: partite decise', '', '| Fascia | Partite | Decise | % [Wilson 95%] |', '|---|---|---|---|']
    for fz in FASCE + ['totale']:
        v = S2[fz]
        if not v['partite']:
            L.append(f'| {fz} | 0 | - | - |')
            continue
        L.append(f"| {fz} | {v['partite']} | {v['decise']} | {100 * v['quota']:.1f} [{100 * v['inf']:.1f}; {100 * v['sup']:.1f}] |")
    g = S2['logistica']
    L += ['', f"Logistica sulle {g['partite']} partite ({g['posizioni']} posizioni, errori per posizione): odds ratio per 0,1 di "
          f"Pfav {g['OR']:.2f} [{g['OR_inf']:.2f}; {g['OR_sup']:.2f}], p = {g['p']:.2g}.", '',
          '## S3: sicurezza della parte favorita', '',
          '| Fascia | Partite | Vinte dalla sfavorita [Wilson 95%] | di cui SC / SF | Conversioni da favorita SC | SF |',
          '|---|---|---|---|---|---|']
    for fz in FASCE + ['totale']:
        v = S3[fz]
        if not v['partite']:
            L.append(f'| {fz} | 0 | - | - | - | - |')
            continue
        cs, cf = v['conversioni_favorita'][A], v['conversioni_favorita'][B]
        L.append(f"| {fz} | {v['partite']} | {v['vinte_sfavorita']} ({100 * v['quota']:.1f}% [{100 * v['inf']:.1f}; {100 * v['sup']:.1f}]) | "
                 f"{v['vinte_sfavorita_da'][A]} / {v['vinte_sfavorita_da'][B]} | "
                 f"{cs[0]}/{cs[1]} ({100 * cs[0] / max(cs[1], 1):.1f}%) | {cf[0]}/{cf[1]} ({100 * cf[0] / max(cf[1], 1):.1f}%) |")
    s4 = R['S4']
    L += ['', '## S4 (descrittiva)', '',
          f"Spearman fra quota di partite decise della posizione e Delta WDL: rho = {s4['rho_delta']:+.2f} (p = {s4['p_delta']:.2g}); "
          f"con Pfav: rho = {s4['rho_pfav']:+.2f} (p = {s4['p_pfav']:.2g}). Posizioni sempre patte {s4['sempre_patte']}, "
          f"sempre decise {s4['sempre_decise']} su {s4['posizioni']}.", '',
          '## Esplorativa: zona di Shashin della parte favorita', '',
          '| Zona | Coppie | Elo [IC 95%] | p |', '|---|---|---|---|']
    for nome, v in R['esplorativa_zone'].items():
        L.append(f"| {nome} | {v['coppie']} | {v['elo']:+.1f} [{v['inf']:+.1f}; {v['sup']:+.1f}] | {v['p']:.3f} |")
    with open(a.out + '.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))
    print(f'\n[OK] Scritti {a.out}.json e {a.out}.md')


if __name__ == '__main__':
    main()
