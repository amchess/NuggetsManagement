#!/usr/bin/env python3
"""
confronto_f_nugget.py - fase F contro i nugget alla stessa Pfav (esplorativa, non pre-registrata).

Confronta le partite decise delle posizioni di F con Pfav fra 0,69 e 0,82 (l'intervallo del pool) con quelle del
match C, giocato alla stessa cadenza (25'+10") dagli stessi motori. Tutte le regressioni sono logistiche, con
errori robusti per posizione (analisi_articolo.logit_cluster); Pfav entra come (Pfav - 0,75)/0,1.

  M1  decisa ~ F + Pfav                      (F contro C, a parita' di Pfav)
  M2  decisa ~ finale + Pfav, nelle 640 partite di F   (finale = Endgame o Transition to endgame)
  M3  decisa ~ F + Pfav + finale             (F contro C, a parita' di Pfav e di fase)
  M4  decisa ~ Pfav + Delta WDL/0,1, nelle 640 partite di F
  M5  decisa ~ F + Pfav + finale + Delta WDL/0,1   (solo per completezza: nell'intervallo Delta WDL separa
      quasi del tutto F da C, quindi i coefficienti di F e di Delta WDL non sono identificabili separatamente)

Uso (dalla cartella docs/revisione2026, dopo gunzip -k risultati/*/*.pgn.gz):
  python confronto_f_nugget.py --c risultati/20261118_2057_pool_robusto --f risultati/20261122_2211_fasce_tc1500 \
     --pool posizioni/nuggets_pool_robusto.csv --posizioni-f posizioni/fasce_320.csv --out rapporti/confronto_f_nugget
"""
import argparse, csv, json, math, os, sys, tempfile

import numpy as np
from scipy import stats as sps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statistiche_match as sm
from analisi_articolo import file_fase, logit_cluster, pgn_in_chiaro

A, B = 'ShashChess42.3', 'Stockfish19'
INTERVALLO = (0.69, 0.82)
FINALE = ('Endgame', 'Transition to endgame')


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


def partite_fase(cartella, tmp):
    pgn, epd = file_fase(cartella, 'partite*.pgn')
    mappa, meta = sm.leggi_aperture(epd)
    partite = [x for x in sm.prepara(pgn_in_chiaro(pgn, tmp), mappa) if {x['w'], x['b']} == {A, B}]
    return partite, {v: k for k, v in mappa.items()}, meta


def modello(righe, colonne):
    """colonne: lista di (nome, funzione della riga). Restituisce gli odds ratio con IC 95% e p."""
    X = [[1.0] + [f(r) for _, f in colonne] for r in righe]
    b, es, G = logit_cluster(X, [r['decisa'] for r in righe], [r['fase'] + ':' + r['ap'] for r in righe])
    out = dict(partite=len(righe), posizioni=G)
    for i, (nome, _) in enumerate(colonne, 1):
        out[nome] = dict(OR=math.exp(b[i]), inf=math.exp(b[i] - 1.96 * es[i]), sup=math.exp(b[i] + 1.96 * es[i]),
                         p=float(2 * sps.norm.sf(abs(b[i] / es[i]))))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--c', required=True, help='cartella del match C')
    ap.add_argument('--f', required=True, help='cartella della fase F')
    ap.add_argument('--pool', required=True, help='posizioni/nuggets_pool_robusto.csv (fase della partita)')
    ap.add_argument('--posizioni-f', required=True, help='posizioni/fasce_320.csv')
    ap.add_argument('--out', default='confronto_f_nugget')
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix='confronto_f_')

    with open(a.pool, encoding='utf-8-sig') as f:
        pool = {' '.join(r['FEN'].split()[:4]): r for r in csv.DictReader(f)}
    with open(a.posizioni_f, encoding='utf-8-sig') as f:
        info_f = {r['id']: r for r in csv.DictReader(f)}

    righe = []
    pc, fen_c, meta_c = partite_fase(a.c, tmp)
    for x in pc:
        md, r = meta_c[x['ap']], pool[fen_c[x['ap']]]
        righe.append(dict(fase='C', ap=x['ap'], decisa=x['r'] in ('1-0', '0-1'), pf=max(md['Pwin'], 1 - md['Pwin']),
                          delta=md['DeltaWDL'], finale=r['Fase'] in FINALE))
    pf_, _, _ = partite_fase(a.f, tmp)
    for x in pf_:
        r = info_f[x['ap']]
        righe.append(dict(fase='F', ap=x['ap'], decisa=x['r'] in ('1-0', '0-1'), pf=float(r['Pfav']),
                          delta=float(r['Delta']), finale=r['Fase'] in FINALE))

    C = [r for r in righe if r['fase'] == 'C']
    F = [r for r in righe if r['fase'] == 'F']
    Fi = [r for r in F if INTERVALLO[0] <= r['pf'] <= INTERVALLO[1]]

    def descrivi(sel):
        k, n = sum(r['decisa'] for r in sel), len(sel)
        lo, hi = wilson(k, n)
        pos = {r['ap']: r for r in sel}.values()
        return dict(partite=n, posizioni=len(pos), decise=k, quota=k / n, inf=lo, sup=hi,
                    pfav_media=float(np.mean([r['pf'] for r in pos])), delta_media=float(np.mean([r['delta'] for r in pos])),
                    delta_min=min(r['delta'] for r in pos), delta_max=max(r['delta'] for r in pos),
                    quota_finali=float(np.mean([r['finale'] for r in pos])))

    pfz = ('Pfav per 0,1', lambda r: (r['pf'] - 0.75) / 0.1)
    isF = ('F contro C', lambda r: 1.0 if r['fase'] == 'F' else 0.0)
    fin = ('finale', lambda r: 1.0 if r['finale'] else 0.0)
    dlt = ('Delta WDL per 0,1', lambda r: r['delta'] / 0.1)
    R = dict(intervallo=INTERVALLO, C=descrivi(C), F_intervallo=descrivi(Fi), F_tutte=descrivi(F),
             M1=modello(C + Fi, [isF, pfz]), M2=modello(F, [fin, pfz]), M3=modello(C + Fi, [isF, pfz, fin]),
             M4=modello(F, [pfz, dlt]), M5=modello(C + Fi, [isF, pfz, fin, dlt]))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out + '.json', 'w', encoding='utf-8') as f:
        json.dump(R, f, indent=1, ensure_ascii=False)

    def orr(m, k):
        v = R[m][k]
        return f"{v['OR']:.2f} [{v['inf']:.2f}; {v['sup']:.2f}], p = {v['p']:.3f}"

    L = ['# F contro i nugget alla stessa Pfav (esplorativa)', '',
         f'Partite decise con Pfav fra {INTERVALLO[0]:.2f} e {INTERVALLO[1]:.2f}, 25\'+10", ShashChess 42.3 contro Stockfish 19.', '',
         '| Insieme | Posizioni | Partite | Decise | Quota [Wilson 95%] | Pfav media | Delta WDL media [min; max] | Finali |',
         '|---|---|---|---|---|---|---|---|']
    for nome, k in (('C (pool)', 'C'), ('F, stesso intervallo', 'F_intervallo'), ('F, tutte', 'F_tutte')):
        d = R[k]
        L.append(f"| {nome} | {d['posizioni']} | {d['partite']} | {d['decise']} | {100 * d['quota']:.1f}% "
                 f"[{100 * d['inf']:.1f}; {100 * d['sup']:.1f}] | {d['pfav_media']:.3f} | {d['delta_media']:.3f} "
                 f"[{d['delta_min']:.3f}; {d['delta_max']:.3f}] | {100 * d['quota_finali']:.0f}% |")
    L += ['', 'Finali: posizioni classificate Endgame o Transition to endgame.', '',
          'Regressioni logistiche (odds ratio [IC 95%], errori robusti per posizione):', '',
          f"- M1, F contro C a parita' di Pfav: {orr('M1', 'F contro C')}",
          f"- M2, finale contro il resto nelle partite di F, a parita' di Pfav: {orr('M2', 'finale')}",
          f"- M3, F contro C a parita' di Pfav e di fase: {orr('M3', 'F contro C')}",
          f"- M4, Delta WDL per 0,1 nelle partite di F, a parita' di Pfav: {orr('M4', 'Delta WDL per 0,1')}",
          f"- M5, F contro C a parita' di Pfav, fase e Delta WDL: {orr('M5', 'F contro C')}; Delta WDL {orr('M5', 'Delta WDL per 0,1')}. "
          'Nell\'intervallo i due insiemi quasi non si sovrappongono in Delta WDL, quindi i due effetti non si separano.']
    with open(a.out + '.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
