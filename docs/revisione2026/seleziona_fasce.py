#!/usr/bin/env python3
"""
seleziona_fasce.py - fase F: scelta delle posizioni, con le regole fissate in PREREGISTRAZIONE_F.md.

Posizioni idonee: tutte quelle con tre analisi di Stockfish 19 a 60 s, cioe' le 2.321 candidate
(posizioni/medie_3analisi.csv) e le 360 candidate delle fasce esterne (posizioni/fasce_candidate.csv, prima analisi
nel registro dell'estrazione piu' le due rianalisi). Sulla media delle tre analisi una posizione e' idonea per la
fascia [lo; hi) se la parte favorita non ha probabilita' di perdere (L_fav medio = 0) e lo <= Pfav < hi.
Sono escluse le posizioni del pool e quelle sulla stessa linea di una posizione del pool.

Scelta: le idonee di ogni fascia sono ordinate per FEN e mescolate con il seme; si prende a turno una posizione
per fascia, scartando quelle sulla stessa linea di una gia' presa, fino a --n per fascia (tutte, se sono meno).
L'ordine del file .epd e' quello della scelta, cosi' le fasce si alternano durante il match.

Uso (dalla radice del repository):
  python docs/revisione2026/seleziona_fasce.py \
     --estrazione data/outputWch2026_SF19/tutte_le_posizioni.csv \
     --rianalisi data/fasce2026/rianalisi01/tutte_le_posizioni.csv data/fasce2026/rianalisi02/tutte_le_posizioni.csv \
     --candidate docs/revisione2026/posizioni/fasce_candidate.csv \
     --medie docs/revisione2026/posizioni/medie_3analisi.csv \
     --pool docs/revisione2026/posizioni/nuggets_pool_robusto.csv \
     --n 80 --seme 2026 --out docs/revisione2026/posizioni/fasce_320
"""
import argparse, collections, csv, os, random, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preseleziona_fasce import Linee, mosse

FASCE = [(0.55, 0.65), (0.65, 0.75), (0.75, 0.85), (0.85, 0.95)]
EPS = 1e-9
CONCLUSI = ('Nugget', 'Non nugget')


def fen4(fen):
    return ' '.join(fen.split()[:4])


def leggi(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def nome_fascia(fz):
    return f'{fz[0]:.2f}-{fz[1]:.2f}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--estrazione', required=True)
    ap.add_argument('--rianalisi', nargs=2, required=True)
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--medie', required=True)
    ap.add_argument('--pool', required=True)
    ap.add_argument('--n', type=int, default=80)
    ap.add_argument('--seme', type=int, default=2026)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    cand = leggi(a.candidate)
    volute = {c['FEN'] for c in cand} | {fen4(c['FEN']) for c in cand}

    def indice(righe):
        d = {}
        for r in righe:
            if r.get('Stato') in CONCLUSI:
                d.setdefault(r['FEN'], r)
                d.setdefault(fen4(r['FEN']), r)
        return d

    with open(a.estrazione, encoding='utf-8-sig') as f:
        prima = indice(r for r in csv.DictReader(f) if r['FEN'] in volute or fen4(r['FEN']) in volute)
    rian = [indice(leggi(p)) for p in a.rianalisi]

    # 1. Medie di tre analisi
    posizioni, mancanti = [], 0
    for c in cand:
        an = [d.get(c['FEN']) or d.get(fen4(c['FEN'])) for d in [prima] + rian]
        if any(x is None for x in an):
            mancanti += 1
            continue
        m = {k: st.mean(float(x[k]) for x in an) for k in ('W1', 'D1', 'L1', 'Pwin1', 'Delta')}
        posizioni.append(dict(FEN=fen4(c['FEN']), Pwin=m['Pwin1'], W=m['W1'], D=m['D1'], L=m['L1'], Delta=m['Delta'],
                              DS_Pwin=st.pstdev(float(x['Pwin1']) for x in an), Fase=c['Fase'], Centro=c['Centro'],
                              Data=c['Data'], Variante_PGN=c['Variante_PGN'], Origine='fasce_candidate'))
    for r in leggi(a.medie):
        posizioni.append(dict(FEN=fen4(r['FEN']), Pwin=float(r['WIN_PROBABILITY']), W=float(r['W1']), D=float(r['D1']),
                              L=float(r['L1']), Delta=float(r['Delta_Win_Probability']), DS_Pwin=float(r['DS_Pwin']),
                              Fase=r['Fase'], Centro=r['Centro'], Data=r['Data_Recente'], Variante_PGN=r['Variante_PGN'],
                              Origine='medie_3analisi'))

    # 2. Idonee per fascia, esclusi il pool e le sue linee
    pool = leggi(a.pool)
    fen_pool = {fen4(r['FEN']) for r in pool}
    bloccate = Linee()
    for r in pool:
        bloccate.aggiungi(mosse(r['Variante_PGN']))
    idonee = {fz: [] for fz in FASCE}
    visti = set()
    for p in posizioni:
        if p['FEN'] in visti or p['FEN'] in fen_pool:
            continue
        visti.add(p['FEN'])
        pf, lf = (p['Pwin'], p['L']) if p['Pwin'] >= 0.5 else (1 - p['Pwin'], p['W'])
        if lf > EPS:
            continue
        for fz in FASCE:
            if fz[0] - EPS <= pf < fz[1] - EPS:
                if not bloccate.in_conflitto(mosse(p['Variante_PGN'])):
                    p['Pfav'], p['Fascia'] = pf, nome_fascia(fz)
                    idonee[fz].append(p)
                break

    # 3. Scelta a turno fra le fasce, una posizione per linea di partita
    rng = random.Random(a.seme)
    code = {}
    for fz in FASCE:
        lista = sorted(idonee[fz], key=lambda p: p['FEN'])
        rng.shuffle(lista)
        code[fz] = lista
    prese, scelte, pos = Linee(), [], {fz: 0 for fz in FASCE}
    conta = collections.Counter()
    while True:
        avanti = False
        for fz in FASCE:
            if conta[fz] >= a.n:
                continue
            lista = code[fz]
            while pos[fz] < len(lista):
                p = lista[pos[fz]]
                pos[fz] += 1
                t = mosse(p['Variante_PGN'])
                if prese.in_conflitto(t):
                    continue
                prese.aggiungi(t)
                scelte.append(p)
                conta[fz] += 1
                avanti = True
                break
        if not avanti:
            break

    if not scelte:
        sys.exit('[ERRORE] nessuna posizione scelta')
    with open(a.out + '.epd', 'w', encoding='utf-8') as f:
        for i, p in enumerate(scelte, 1):
            p['id'] = f'fascia{i:03d}'
            f.write(f'{p["FEN"]} id "{p["id"]}"; c0 "Pwin={p["Pwin"]:.3f} DeltaWDL={p["Delta"]:.3f}";\n')
    campi = ['id', 'FEN', 'Fascia', 'Pfav', 'Pwin', 'W', 'D', 'L', 'Delta', 'DS_Pwin', 'Fase', 'Centro', 'Data', 'Variante_PGN', 'Origine']
    with open(a.out + '.csv', 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=campi, extrasaction='ignore')
        wr.writeheader()
        for p in scelte:
            wr.writerow({k: (f'{p[k]:.4f}' if isinstance(p[k], float) else p[k]) for k in campi})

    L = ['# Fase F: posizioni scelte', '', f'Seme {a.seme}; al piu\' {a.n} posizioni per fascia. '
         f'Candidate delle fasce esterne senza tre analisi complete: {mancanti}.', '',
         '| Fascia | Idonee | Scelte | Pfav min / mediana / max | Delta WDL mediano | Bianco favorito |', '|---|---|---|---|---|---|']
    for fz in FASCE:
        s = [p for p in scelte if p['Fascia'] == nome_fascia(fz)]
        if s:
            pf = [p['Pfav'] for p in s]
            L.append(f'| {nome_fascia(fz)} | {len(idonee[fz])} | {len(s)} | {min(pf):.3f} / {st.median(pf):.3f} / {max(pf):.3f} | '
                     f'{st.median(p["Delta"] for p in s):.3f} | {sum(p["Pwin"] >= 0.5 for p in s)} |')
        else:
            L.append(f'| {nome_fascia(fz)} | {len(idonee[fz])} | 0 | - | - | - |')
    fasi = collections.Counter(p['Fase'] for p in scelte)
    L += ['', 'Fasi di gioco: ' + ', '.join(f'{k} {v}' for k, v in fasi.most_common()),
          'Origine: ' + ', '.join(f'{k} {v}' for k, v in collections.Counter(p['Origine'] for p in scelte).items())]
    with open(a.out + '.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))
    print(f'\n[OK] {len(scelte)} posizioni: {a.out}.epd, .csv, .md')


if __name__ == '__main__':
    main()
