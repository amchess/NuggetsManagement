"""Strumenti minimi per le verifiche: scacchiera da FEN, SAN di una mossa UCI, motore UCI.

Non usa librerie esterne: le mosse legali e la FEN dopo ogni mossa vengono chieste al motore
("go perft 1" e "d", comandi di Stockfish e dei motori derivati). Serve a rigiocare le linee
SAN dei registri e dei PGN fino alla posizione voluta.
"""
import gzip
import re
import subprocess

PEZZI = {'p': '', 'n': 'N', 'b': 'B', 'r': 'R', 'q': 'Q', 'k': 'K'}


def apri(path):
    """Apre un file di testo, anche compresso con gzip (.gz)."""
    if str(path).endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8-sig')
    return open(path, encoding='utf-8-sig')


def k4(fen):
    """I primi quattro campi della FEN: la posizione senza i contatori di mossa."""
    return ' '.join(fen.split()[:4])


def scacchiera(fen):
    b = {}
    for i, riga in enumerate(fen.split()[0].split('/')):
        f = 0
        for ch in riga:
            if ch.isdigit():
                f += int(ch)
            else:
                b['abcdefgh'[f] + str(8 - i)] = ch
                f += 1
    return b


def san_lite(b, uci, legali_uci):
    """SAN di una mossa UCI legale, senza i segni di scacco e matto."""
    da, a = uci[:2], uci[2:4]
    tipo = b.get(da, '?').lower()
    if tipo == 'k' and abs(ord(da[0]) - ord(a[0])) == 2:
        return 'O-O' if a[0] == 'g' else 'O-O-O'
    cattura = a in b or (tipo == 'p' and da[0] != a[0])
    promo = ('=' + uci[4].upper()) if len(uci) == 5 else ''
    if tipo == 'p':
        return (da[0] + 'x' if cattura else '') + a + promo
    altri = [m[:2] for m in legali_uci if m[2:4] == a and m[:2] != da and b.get(m[:2], '').lower() == tipo]
    dis = ''
    if altri:
        if all(o[0] != da[0] for o in altri):
            dis = da[0]
        elif all(o[1] != da[1] for o in altri):
            dis = da[1]
        else:
            dis = da
    return PEZZI[tipo] + dis + ('x' if cattura else '') + a + promo


def pulisci(san):
    return re.sub(r'[+#!?]', '', san).replace('0-0-0', 'O-O-O').replace('0-0', 'O-O')


def token_san(testo):
    """Mosse SAN di un testo PGN o di una Variante_PGN: senza commenti, numeri di mossa e risultato."""
    testo = re.sub(r'\{[^{}]*\}', ' ', testo)
    testo = re.sub(r'\d+\.(\.\.)?', ' ', testo)
    return [t for t in testo.split() if t not in ('1-0', '0-1', '1/2-1/2', '*')]


class Motore:
    """Motore UCI a riga di comando."""

    def __init__(self, cmd, opzioni=None):
        self.p = subprocess.Popen([cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.manda('uci')
        self.aspetta('uciok')
        for k, v in (opzioni or {}).items():
            self.manda(f'setoption name {k} value {v}')
        self.manda('isready')
        self.aspetta('readyok')

    def manda(self, s):
        self.p.stdin.write(s + '\n')
        self.p.stdin.flush()

    def aspetta(self, prefisso):
        righe = []
        while True:
            r = self.p.stdout.readline()
            if not r:
                raise RuntimeError('il motore si e\' fermato')
            righe.append(r.rstrip('\n'))
            if r.startswith(prefisso):
                return righe

    def posizione(self, fen, mosse):
        self.manda(f'position fen {fen} moves {" ".join(mosse)}' if mosse else f'position fen {fen}')

    def legali(self, fen, mosse):
        self.posizione(fen, mosse)
        self.manda('go perft 1')
        return [r.split(':')[0] for r in self.aspetta('Nodes searched')
                if re.match(r'^[a-h][1-8][a-h][1-8][qrbn]?: ', r)]

    def fen(self, fen, mosse):
        self.posizione(fen, mosse)
        self.manda('d')
        return next(r[5:].strip() for r in self.aspetta('Checkers') if r.startswith('Fen: '))

    def rigioca(self, fen, san):
        """Rigioca una lista di mosse SAN da fen. Restituisce (mosse UCI, FEN dopo ogni mossa)."""
        mosse, fens = [], [fen]
        for t in san:
            legali = self.legali(fen, mosse)
            b = scacchiera(fens[-1])
            m = [u for u in legali if san_lite(b, u, legali) == pulisci(t)]
            if len(m) != 1:
                raise ValueError(f'mossa {t} non risolta dopo {len(mosse)} semimosse')
            mosse.append(m[0])
            fens.append(self.fen(fen, mosse))
        return mosse, fens

    def analizza(self, fen, mosse, ms):
        """Analisi a tempo fisso: (punteggio UCI, wdl dal lato al tratto) dell'ultima riga con pv."""
        self.posizione(fen, mosse)
        self.manda(f'go movetime {ms}')
        info = [r for r in self.aspetta('bestmove') if ' pv ' in r]
        if not info:
            return None, None
        t = info[-1].split()
        score = ' '.join(t[t.index('score') + 1: t.index('score') + 3])
        wdl = [int(x) for x in t[t.index('wdl') + 1: t.index('wdl') + 4]] if 'wdl' in t else None
        return score, wdl

    def chiudi(self):
        try:
            self.manda('quit')
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()
