#!/usr/bin/env python3
"""
statistiche_rr_extra.py - analisi pre-registrate del round robin non coperte da statistiche_match.py (S2, S5):
Elo normalizzato per coppia, partite decisive per coppia (IC di Wilson), vittorie della parte sfavorita,
conversione per motore, decisive per fascia di Pwin della parte favorita (rho di Spearman).
La parte favorita e' quella indicata dalla Pwin pre-partita del file delle posizioni (c0 "Pwin=...").

Uso (da docs/revisione2026):
  python statistiche_rr_extra.py --pgn $R/<cartella_rr>/partite_*.pgn --aperture posizioni/nuggets_top100_robusto.epd \
      --out rapporti/statistiche_rr_extra
Richiede statistiche_match.py nella stessa cartella (numpy e scipy).
"""
import argparse, collections, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statistiche_match as sm
from scipy import stats as sps

_ap = argparse.ArgumentParser(description='Analisi aggiuntive del round robin (S2, S5)')
_ap.add_argument('--pgn', nargs='+', required=True, help='PGN delle sei coppie (partite_*.pgn)')
_ap.add_argument('--aperture', required=True, help='file .epd delle posizioni con c0 "Pwin=... DeltaWDL=..."')
_ap.add_argument('--out', default='statistiche_rr_extra', help='prefisso dei file di output (.json e .md)')
_args = _ap.parse_args()
pgn, epd = _args.pgn, _args.aperture
mappa, meta = sm.leggi_aperture(epd)
partite = sm.prepara(pgn, mappa)
NT = 800 / math.log(10)

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h

def fav(ap):  # +1 favorito il Bianco, -1 il Nero, dalla Pwin pre-partita (media delle 3 analisi)
    return 1 if meta[ap]['Pwin'] > 0.5 else -1

out = {}
motori = sorted({x['w'] for x in partite} | {x['b'] for x in partite})
coppie, spaiate = sm.forma_coppie(partite)
righe = []
for i, a in enumerate(motori):
    for b in motori[i + 1:]:
        g = [x for x in partite if {x['w'], x['b']} == {a, b}]
        dec = sum(x['r'] != '1/2-1/2' for x in g)
        perse_fav = sum((x['r'] == '1-0' and fav(x['ap']) == -1) or (x['r'] == '0-1' and fav(x['ap']) == 1) for x in g)
        cp = [c for c in coppie if {c[0]['w'], c[0]['b']} == {a, b}]
        pc = [sum(x['sw'] if x['w'] == a else 1 - x['sw'] for x in c) for c in cp]
        pen = sm.pentanomiale(pc)
        nelo = pen['t1'] * NT; es = NT / math.sqrt(2 * len(pc))
        p, lo, hi = wilson(dec, len(g))
        righe.append(dict(coppia=f'{a} - {b}', partite=len(g), decisive=dec, quota=p, ic=[lo, hi],
                          vittorie_sfavorita=perse_fav, nelo=nelo, nelo_ic=[nelo - 1.96 * es, nelo + 1.96 * es],
                          elo=pen['elo'], elo_ic=[pen['elo_inf'], pen['elo_sup']]))
out['coppie'] = righe

conv = {}
for e in motori:
    fv = [x for x in partite if (x['w'] == e and fav(x['ap']) == 1) or (x['b'] == e and fav(x['ap']) == -1)]
    sf = [x for x in partite if e in (x['w'], x['b']) and x not in fv]
    vinte = sum((x['r'] == '1-0' and x['w'] == e) or (x['r'] == '0-1' and x['b'] == e) for x in fv)
    perse = sum((x['r'] == '1-0' and x['b'] == e) or (x['r'] == '0-1' and x['w'] == e) for x in sf)
    vinte_sf = sum((x['r'] == '1-0' and x['w'] == e) or (x['r'] == '0-1' and x['b'] == e) for x in sf)
    perse_fv = sum((x['r'] == '1-0' and x['b'] == e) or (x['r'] == '0-1' and x['w'] == e) for x in fv)
    conv[e] = dict(da_favorito=len(fv), convertite=vinte, conv=wilson(vinte, len(fv)), perse_da_favorito=perse_fv,
                   da_sfavorito=len(sf), perse=perse, perse_q=wilson(perse, len(sf)), vinte_da_sfavorito=vinte_sf)
out['conversione'] = conv

tot = collections.Counter(); dec = collections.Counter(); fe = collections.defaultdict(list)
for x in partite:
    tot[x['ap']] += 1; dec[x['ap']] += x['r'] != '1/2-1/2'
    if x['fe'] is not None: fe[x['ap']].append(abs(x['fe']))
aps = sorted(tot)
q = [dec[k] / tot[k] for k in aps]
pfav = [max(meta[k]['Pwin'], 1 - meta[k]['Pwin']) for k in aps]
dwdl = [meta[k]['DeltaWDL'] for k in aps]
ev = [sum(fe[k]) / len(fe[k]) for k in aps]
out['spearman'] = dict(
    pwin_favorita=list(sps.spearmanr(pfav, q)), delta_wdl=list(sps.spearmanr(dwdl, q)), eval_motori=list(sps.spearmanr(ev, q)))
fasce = [(0.69, 0.72), (0.72, 0.75), (0.75, 0.78), (0.78, 0.82)]
out['per_fascia_pwin'] = []
for lo, hi in fasce:
    ks = [k for k, p in zip(aps, pfav) if lo <= p < hi]
    n = sum(tot[k] for k in ks); d = sum(dec[k] for k in ks)
    out['per_fascia_pwin'].append(dict(fascia=f'{lo:.2f}-{hi:.2f}', posizioni=len(ks), partite=n, decisive=d,
                                       quota=d / n if n else None, ic=list(wilson(d, n)[1:]) if n else None))
out['sempre_patte'] = [k for k in aps if dec[k] == 0]
out['sempre_decisive'] = [k for k in aps if dec[k] == tot[k]]
d_all = sum(dec.values()); n_all = sum(tot.values())
out['totale'] = dict(partite=n_all, decisive=d_all, quota=wilson(d_all, n_all),
                     vittorie_sfavorita=sum(r['vittorie_sfavorita'] for r in righe))
json.dump(out, open(_args.out + '.json', 'w'), indent=1, default=float)

L = ['| Coppia | Decisive | Quota [IC Wilson 95%] | Vittorie della parte sfavorita | Elo [IC 95%] | Elo normalizzato [IC 95%] |', '|---|---|---|---|---|---|']
for r in righe:
    L.append(f"| {r['coppia']} | {r['decisive']}/{r['partite']} | {100*r['quota']:.1f}% [{100*r['ic'][0]:.1f}; {100*r['ic'][1]:.1f}] | {r['vittorie_sfavorita']} | {r['elo']:+.1f} [{r['elo_ic'][0]:+.1f}; {r['elo_ic'][1]:+.1f}] | {r['nelo']:+.0f} [{r['nelo_ic'][0]:+.0f}; {r['nelo_ic'][1]:+.0f}] |")
t = out['totale']
L += ['', f"Totale: {t['decisive']}/{t['partite']} decisive ({100*t['quota'][0]:.1f}% [{100*t['quota'][1]:.1f}; {100*t['quota'][2]:.1f}]); vittorie della parte sfavorita: {t['vittorie_sfavorita']}", '',
      '| Motore | Da favorito: vinte | Conversione [IC 95%] | Da favorito: perse | Da sfavorito: perse | Quota perse [IC 95%] | Da sfavorito: vinte |', '|---|---|---|---|---|---|---|']
for e, c in conv.items():
    L.append(f"| {e} | {c['convertite']}/{c['da_favorito']} | {100*c['conv'][0]:.1f}% [{100*c['conv'][1]:.1f}; {100*c['conv'][2]:.1f}] | {c['perse_da_favorito']} | {c['perse']}/{c['da_sfavorito']} | {100*c['perse_q'][0]:.1f}% [{100*c['perse_q'][1]:.1f}; {100*c['perse_q'][2]:.1f}] | {c['vinte_da_sfavorito']} |")
s = out['spearman']
L += ['', f"Spearman, quota di decisive per posizione contro Pwin della parte favorita (pre-partita): rho = {s['pwin_favorita'][0]:.3f}, p = {s['pwin_favorita'][1]:.4f}",
      f"Esplorativo: contro Delta WDL rho = {s['delta_wdl'][0]:.3f}, p = {s['delta_wdl'][1]:.4f}; contro la prima valutazione dei motori in partita rho = {s['eval_motori'][0]:.3f}, p = {s['eval_motori'][1]:.2g}", '',
      '| Pwin favorita | Posizioni | Partite | Decisive | Quota [IC 95%] |', '|---|---|---|---|---|']
for f in out['per_fascia_pwin']:
    L.append(f"| {f['fascia']} | {f['posizioni']} | {f['partite']} | {f['decisive']} | " + (f"{100*f['quota']:.1f}% [{100*f['ic'][0]:.1f}; {100*f['ic'][1]:.1f}]" if f['partite'] else '-') + ' |')
L += ['', f"Posizioni sempre patte ({len(out['sempre_patte'])}): {', '.join(out['sempre_patte'])}", f"Posizioni sempre decisive ({len(out['sempre_decisive'])}): {', '.join(out['sempre_decisive'])}"]
open(_args.out + '.md', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
