"""Verifiche sui registri dell'oracolo e sulla scelta del pool (domande 1, 3 e 4).

Uso (dalla radice del repository):
    python3 verifiche/registri.py                      # con i percorsi del commit finale
    python3 verifiche/registri.py --base docs/revisione2026

Legge il registro della prima analisi, le due rianalisi dei 2.321 candidati, le medie delle tre
analisi e il pool, e verifica:
  1. come sono mediate le tre analisi (per rango delle linee MultiPV) e quante volte la seconda
     linea ha una Pwin piu' alta della prima;
  2. che i candidati siano tutte e sole le posizioni con |Pfav - 0,75| <= 0,10 e comprendano le 287
     pepite della prima analisi; gli stati della prima analisi (scartate, matti);
  3. che la regola di genera_pgn.py (Delta crescente, una posizione per linea) riproduca il pool,
     e se la posizione tenuta venga prima o dopo quella scartata.
Scrive rapporti/verifiche_registri.json.
"""
import argparse
import csv
import json
import os
import re
from collections import Counter

from scacchi_min import apri, k4

EPS = 1e-9


def pfav(p):
    return p if p > 0.5 else 1 - p


def pwin(r, k):
    return float(r[f'W{k}']) + float(r[f'D{k}']) / 2


def classifica(p1, delta, w1, l1, tol=0.06):
    """Regola della pepita (Definizione 1), come pepita() in pool_robusto.py."""
    t = 0.75 if p1 >= 0.5 else 0.25
    lato = l1 if t == 0.75 else w1
    return abs(p1 - t) <= tol + EPS and delta <= tol + EPS and lato <= EPS


def moves(variant):
    """Come moves() in docs/outputLTCWch/genera_pgn.py."""
    return tuple(t for t in re.sub(r"\d+\.", " ", str(variant)).split())


def related(a, b):
    """Come related() in genera_pgn.py: una linea e' il prefisso dell'altra."""
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='docs/revisione2026')
    a = ap.parse_args()
    reg = os.path.join(a.base, 'registri')
    pos = os.path.join(a.base, 'posizioni')
    out = {}

    prima = list(csv.DictReader(apri(os.path.join(reg, 'estrazione_tutte_le_posizioni.csv.gz'))))
    medie = list(csv.DictReader(apri(os.path.join(pos, 'medie_3analisi.csv'))))
    pool = list(csv.DictReader(apri(os.path.join(pos, 'nuggets_pool_robusto.csv'))))
    cand = {r['FEN'] for r in medie}

    # --- domanda 3: stati della prima analisi e candidati
    stati = Counter(r['Stato'] for r in prima)
    senza_wdl = [r for r in prima if r['Stato'] == 'Non nugget' and r['Pwin1'] == '']
    matti = sum(r['CP1'].lstrip('-').startswith('M') for r in senza_wdl)
    banda = {r['FEN'] for r in prima if r['Pwin1'] != '' and abs(pfav(float(r['Pwin1'])) - 0.75) <= 0.10 + EPS}
    pepite = {r['FEN'] for r in prima if r['Stato'] == 'Nugget'}
    k4c = Counter(k4(r['FEN']) for r in prima)
    out['prima_analisi'] = {
        'righe': len(prima), 'stati': dict(stati),
        'non_pepite_senza_wdl': len(senza_wdl), 'di_cui_matto_nella_prima_linea': matti,
        'stesse_posizioni_con_contatori_diversi': {'gruppi': sum(v > 1 for v in k4c.values()),
                                                   'righe_in_piu': sum(v - 1 for v in k4c.values() if v > 1)},
    }
    out['candidati'] = {
        'banda_0_10': len(banda), 'candidati_rianalizzati': len(cand), 'insiemi_uguali': banda == cand,
        'pepite_prima_analisi': len(pepite), 'pepite_fra_i_candidati': len(pepite & cand),
        'max_distanza_pepite_da_0_75': round(max(abs(pfav(float(r['Pwin1'])) - 0.75)
                                                 for r in prima if r['Stato'] == 'Nugget'), 4),
    }

    # --- domanda 1: linee invertite (seconda linea con Pwin piu' alta per il lato al tratto)
    def invertite(righe):
        n = inv = prof = 0
        for r in righe:
            if r['FEN'] not in cand or r.get('W1', '') == '':
                continue
            n += 1
            g = pwin(r, 1) - pwin(r, 2)
            if r['FEN'].split()[1] == 'b':
                g = -g
            if g < -EPS:
                inv += 1
                prof += r['Profondita1'] != r['Profondita2']
        return {'analisi': n, 'seconda_linea_migliore': inv, 'di_cui_profondita_diverse': prof}

    ana = {'prima': invertite(prima)}
    for k in ('01', '02'):
        ana['rianalisi' + k] = invertite(csv.DictReader(apri(os.path.join(reg, f'rumore_run{k}.csv.gz'))))
    tot_n = sum(v['analisi'] for v in ana.values())
    tot_i = sum(v['seconda_linea_migliore'] for v in ana.values())
    out['linee_invertite'] = dict(ana, totale={'analisi': tot_n, 'seconda_linea_migliore': tot_i,
                                               'quota': round(tot_i / tot_n, 4)})

    # media dei Delta (codice, Definizione 2) contro Delta delle medie
    diverse = robuste = robuste_alt = 0
    for r in medie:
        p1 = float(r['WIN_PROBABILITY'])
        p2 = pwin(r, 2)
        d = float(r['Delta_Win_Probability'])
        diverse += d - abs(p1 - p2) > 0.0015
        robuste += classifica(p1, d, float(r['W1']), float(r['L1']))
        robuste_alt += classifica(p1, abs(p1 - p2), float(r['W1']), float(r['L1']))
    out['media_dei_delta'] = {'posizioni_con_media_dei_delta_diversa': diverse,
                              'pepite_robuste_media_dei_delta': robuste,
                              'pepite_robuste_delta_delle_medie': robuste_alt,
                              'mossa_migliore_stabile_candidati': sum(int(r['Mossa_stabile']) for r in medie)}

    # --- domanda 4: una posizione per linea, come genera_pgn.py
    rob = []
    for r in medie:
        p1 = float(r['WIN_PROBABILITY'])
        d = float(r['Delta_Win_Probability'])
        if classifica(p1, d, float(r['W1']), float(r['L1'])):
            dist = round(abs(p1 - (0.75 if p1 >= 0.5 else 0.25)), 3)
            rob.append((d, dist, r['FEN'], r))
    rob.sort(key=lambda x: (x[0], x[1], x[2]))
    scelte, linee, scartate = [], [], []
    for d, dist, fen, r in rob:
        lin = moves(r['Variante_PGN'])
        rel = [i for i, c in enumerate(linee) if related(lin, c)]
        if rel:
            scartate.append((lin, linee[rel[0]]))
            continue
        scelte.append(r)
        linee.append(lin)
    pool_fen = {r['FEN'] for r in pool}
    out['deduplicazione'] = {
        'pepite_robuste': len(rob), 'scelte': len(scelte),
        'uguale_al_pool': {r['FEN'] for r in scelte} == pool_fen,
        'scartate': len(scartate),
        'tenuta_dopo_la_scartata': sum(len(s) < len(k) for s, k in scartate),
        'tenuta_prima_della_scartata': sum(len(s) > len(k) for s, k in scartate),
        'top100_primi_100': [r['FEN'] for r in scelte[:100]] != [],
        'mossa_migliore_stabile_pool': sum(int(r['Mossa_stabile']) for r in medie if r['FEN'] in pool_fen),
        'stesse_posizioni_nel_pool': len(pool_fen) - len({k4(f) for f in pool_fen}),
    }
    top = os.path.join(pos, 'nuggets_top100_robusto.csv')
    if os.path.exists(top):
        t = {r['FEN'] for r in csv.DictReader(apri(top))}
        out['deduplicazione']['top100_primi_100'] = t == {r['FEN'] for r in scelte[:100]}

    dest = os.path.join(a.base, 'rapporti', 'verifiche_registri.json')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    json.dump(out, open(dest, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    print('scritto', dest)


if __name__ == '__main__':
    main()
