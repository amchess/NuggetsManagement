#!/usr/bin/env python3
"""
preseleziona_fasce.py - fase F (Pwin da 0,55 a 0,95): candidate delle due fasce esterne da rianalizzare.

Dal registro dell'estrazione (una analisi di 60 s per posizione) prende le posizioni concluse in cui la parte
favorita non ha probabilita' di perdere (L_fav = 0) e Pfav cade in [0,55; 0,65) o in [0,85; 0,95). Esclude le
posizioni del pool e quelle sulla stessa linea di una posizione del pool (una linea e' prefisso dell'altra).
Mescola le posizioni di ogni fascia con il seme fissato e ne tiene al piu' --n per fascia, una per linea di partita.
Le fasce centrali non servono: le 2.321 candidate hanno gia' tre analisi (posizioni/medie_3analisi.csv).

Uso (dalla radice del repository):
  python docs/revisione2026/preseleziona_fasce.py --estrazione data/outputWch2026_SF19/tutte_le_posizioni.csv \
         --pool docs/revisione2026/posizioni/nuggets_pool_robusto.csv --n 180 --seme 2026 \
         --out docs/revisione2026/posizioni/fasce_candidate.csv
"""
import argparse, csv, random, re, sys

FASCE_ESTERNE = [(0.55, 0.65), (0.85, 0.95)]
EPS = 1e-9


def mosse(variante):
    """'1. e4 e5 2. Nf3' -> ('e4', 'e5', 'Nf3')"""
    return tuple(t for t in variante.split() if not re.fullmatch(r'\d+\.(\.\.)?', t))


class Linee:
    """Insieme di linee di partita: segnala se una nuova linea e' prefisso di una gia' presa o viceversa."""
    def __init__(self):
        self.intere, self.prefissi = set(), set()

    def in_conflitto(self, t):
        if t in self.prefissi:                       # t e' prefisso (o uguale) di una linea presa
            return True
        return any(t[:k] in self.intere for k in range(len(t)))   # una linea presa e' prefisso di t

    def aggiungi(self, t):
        self.intere.add(t)
        for k in range(len(t) + 1):
            self.prefissi.add(t[:k])


def fav(pwin, w, l):
    """(Pfav, L_fav) con Pwin, W, L dal punto di vista del Bianco."""
    return (pwin, l) if pwin >= 0.5 else (1 - pwin, w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--estrazione', required=True)
    ap.add_argument('--pool', required=True)
    ap.add_argument('--n', type=int, default=180)
    ap.add_argument('--seme', type=int, default=2026)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    bloccate = Linee()
    with open(a.pool, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            bloccate.aggiungi(mosse(r['Variante_PGN']))

    per_fascia = {fz: [] for fz in FASCE_ESTERNE}
    with open(a.estrazione, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['Stato'] not in ('Nugget', 'Non nugget'):
                continue
            try:
                pw, w, l = float(r['Pwin1']), float(r['W1']), float(r['L1'])
            except ValueError:
                continue
            pf, lf = fav(pw, w, l)
            if lf > EPS:
                continue
            for lo, hi in FASCE_ESTERNE:
                if lo - EPS <= pf < hi - EPS:
                    per_fascia[(lo, hi)].append((r, pf))
                    break

    rng = random.Random(a.seme)
    campi = ['FEN', 'Data', 'Variante_PGN', 'Fascia', 'Pfav_1', 'Pwin1', 'W1', 'D1', 'L1', 'Delta', 'Fase', 'Centro']
    righe, riepilogo = [], []
    for fz in FASCE_ESTERNE:
        lista = sorted(per_fascia[fz], key=lambda x: x[0]['FEN'])      # ordine indipendente dal registro
        rng.shuffle(lista)
        prese = Linee()
        n = 0
        for r, pf in lista:
            t = mosse(r['Variante_PGN'])
            if bloccate.in_conflitto(t) or prese.in_conflitto(t):
                continue
            prese.aggiungi(t)
            righe.append({'FEN': r['FEN'], 'Data': r['Data'], 'Variante_PGN': r['Variante_PGN'], 'Fascia': f'{fz[0]:.2f}-{fz[1]:.2f}',
                          'Pfav_1': f'{pf:.4f}', 'Pwin1': r['Pwin1'], 'W1': r['W1'], 'D1': r['D1'], 'L1': r['L1'],
                          'Delta': r['Delta'], 'Fase': r['Fase'], 'Centro': r['Centro']})
            n += 1
            if n == a.n:
                break
        riepilogo.append(f'{fz[0]:.2f}-{fz[1]:.2f}: {len(lista)} posizioni idonee, {n} candidate prese')
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=campi)
        wr.writeheader()
        wr.writerows(righe)
    print('\n'.join(riepilogo))
    print(f'[OK] {len(righe)} candidate scritte in {a.out}')


if __name__ == '__main__':
    sys.exit(main())
