"""Rigioca la linea di partita di ogni posizione del pool (domanda 4).

Uso (dalla radice del repository):
    python3 verifiche/linee_pool.py --motore /percorso/stockfish [--evalfile rete.nnue]

Per ogni posizione del pool rigioca la Variante_PGN dalla posizione iniziale con un motore UCI
(mosse legali e FEN dopo ogni mossa) e verifica che la linea finisca nella FEN della posizione,
che nessuna posizione del pool stia sulla linea di un'altra (confronto per FEN, quindi anche per
trasposizione lungo queste linee) e che non ci siano due posizioni uguali a meno dei contatori.
Scrive rapporti/verifiche_linee_pool.json.
"""
import argparse
import csv
import json
import os

from scacchi_min import Motore, apri, k4, token_san

INIZIO = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='docs/revisione2026')
    ap.add_argument('--motore', required=True)
    ap.add_argument('--evalfile', help='rete NNUE, per i motori compilati senza rete incorporata')
    a = ap.parse_args()
    pool = list(csv.DictReader(apri(os.path.join(a.base, 'posizioni', 'nuggets_pool_robusto.csv'))))
    m = Motore(a.motore, {'EvalFile': a.evalfile} if a.evalfile else {})
    percorsi, errori = {}, []
    for r in pool:
        try:
            _, fens = m.rigioca(INIZIO, token_san(r['Variante_PGN']))
        except ValueError as e:
            errori.append(f"{r['FEN']}: {e}")
            continue
        percorsi[r['FEN']] = [k4(f) for f in fens]
        if percorsi[r['FEN']][-1] != k4(r['FEN']):
            errori.append(f"{r['FEN']}: la linea finisce altrove")
    m.chiudi()
    coppie = [(x, y) for y, p in percorsi.items() for x in percorsi if x != y and k4(x) in p[:-1]]
    out = {'posizioni': len(pool), 'linee_rigiocate': len(percorsi), 'errori': errori,
           'posizioni_uguali_a_meno_dei_contatori': len(percorsi) - len({k4(f) for f in percorsi}),
           'posizioni_sulla_linea_di_un_altra': [{'posizione': x, 'linea_di': y} for x, y in coppie]}
    dest = os.path.join(a.base, 'rapporti', 'verifiche_linee_pool.json')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    json.dump(out, open(dest, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in out.items()}, indent=1))
    print('scritto', dest)


if __name__ == '__main__':
    main()
