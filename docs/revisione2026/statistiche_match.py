#!/usr/bin/env python3
"""
Statistiche dei match e dei tornei giocati con cutechess-cli sulle pepite.

Calcola, per ogni coppia di motori, i risultati con tre modelli (trinomiale, pentanomiale
a coppie di partite a colori invertiti, cluster per posizione), il test di McNemar sulla
conversione della parte favorita, i rating di Bradley-Terry con intervalli bootstrap,
la verifica che il disegno sia incrociato, le proprieta' delle posizioni (parte favorita,
partite decisive) e l'analisi di potenza. Facoltativi: test d'interazione fra due insiemi
di posizioni (es. pepite contro libro di controllo) e regressione del risultato su Delta WDL.

Non richiede python-chess; richiede numpy e scipy.

Esempi:
  python statistiche_match.py --pgn match.pgn --a ShashChess42 --b Stockfish19 --out match
  python statistiche_match.py --pgn rr_*.pgn --ancora Stockfish19 --elo-ancora 3670 --out roundrobin
  python statistiche_match.py --pgn match.pgn --aperture nuggets_pool.epd --a ShashChess42 --b Stockfish19 \
         --confronta controllo_uho.pgn --out confronto
"""
import argparse
import collections
import datetime
import json
import math
import re
import statistics as st
import sys

import numpy as np
from scipy import stats as sps

RNG = np.random.default_rng(20261116)

# ------------------------------------------------------------------ lettura PGN
HEADER_RE = re.compile(r'^\[(\w+)\s+"(.*)"\]\s*$')
EVAL_RE = re.compile(r'^\s*([+-]?M?\d+(?:\.\d+)?)/(\d+)\s+([\d.]+)s')


def _tokens(text):
    """Mosse SAN e relativo commento, nell'ordine."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '{':
            j = text.index('}', i)
            if out:
                san, prev = out[-1]
                out[-1] = (san, (prev + ' | ' if prev else '') + text[i + 1:j].strip())
            i = j + 1
            continue
        if c == '(':                                   # varianti: ignorate
            depth, j = 1, i + 1
            while depth and j < n:
                depth += {'(': 1, ')': -1}.get(text[j], 0)
                j += 1
            i = j
            continue
        if c.isspace():
            i += 1
            continue
        j = i
        while j < n and not text[j].isspace() and text[j] not in '{(':
            j += 1
        tok = re.sub(r'^\d+\.(\.\.)?', '', text[i:j])
        i = j
        if tok and tok not in ('1-0', '0-1', '1/2-1/2', '*') and not tok.startswith('$'):
            out.append((tok, ''))
    return out


def leggi_pgn(path):
    partite, headers, corpo, in_mosse = [], {}, [], False

    def chiudi():
        if headers:
            t = _tokens(' '.join(corpo))
            partite.append({'h': dict(headers), 'mosse': [a for a, _ in t], 'com': [b for _, b in t], 'file': path})

    with open(path, encoding='utf-8', errors='replace') as fh:
        for riga in fh:
            m = HEADER_RE.match(riga.rstrip('\n'))
            if m:
                if in_mosse:
                    chiudi()
                    headers, corpo, in_mosse = {}, [], False
                headers[m.group(1)] = m.group(2)
            elif riga.strip():
                in_mosse = True
                corpo.append(riga.strip())
    chiudi()
    return partite


def lunghezza_libro(g):
    k = 0
    while k < len(g['com']) and g['com'][k].startswith('book'):
        k += 1
    return k


def valuta(commento):
    m = EVAL_RE.match(commento or '')
    if not m:
        return None
    raw = m.group(1)
    v = (100.0 if not raw.startswith('-') else -100.0) if 'M' in raw else float(raw)
    return v, int(m.group(2)), float(m.group(3))


def prima_valutazione_bianco(g):
    """Prima valutazione fuori libro, dal punto di vista del Bianco (None se assente)."""
    pari = chi_muove_per_primo(g) == 'w'
    for k in range(lunghezza_libro(g), len(g['mosse'])):
        e = valuta(g['com'][k])
        if e:
            bianco_muove = (k % 2 == 0) == pari
            return e[0] if bianco_muove else -e[0]
    return None


def chi_muove_per_primo(g):
    fen = g['h'].get('FEN')
    if fen and len(fen.split()) > 1:
        return fen.split()[1]
    return 'w'


def chiave_fen(fen):
    return ' '.join(fen.split()[:4])


# ------------------------------------------------------------------ aperture (facoltative)
def leggi_aperture(path):
    """
    Restituisce (mappa chiave -> id, mappa id -> metadati).
    EPD: la chiave e' la FEN (4 campi); id dall'opcode id; metadati Pwin/DeltaWDL dal c0
    scritto da genera_pgn.py. PGN: la chiave e' la sequenza di mosse della linea.
    """
    chiavi, meta = {}, {}
    if path.lower().endswith('.epd'):
        with open(path, encoding='utf-8') as f:
            for n, riga in enumerate(f, 1):
                riga = riga.strip()
                if not riga:
                    continue
                campi = riga.split()
                fen4 = ' '.join(campi[:4])
                resto = ' '.join(campi[4:])
                m = re.search(r'\bid\s+"([^"]+)"', resto)
                ident = m.group(1) if m else f'pos{n:04d}'
                md = {}
                for k, v in re.findall(r'(Pwin|DeltaWDL)=([-\d.]+)', resto):
                    md[k] = float(v)
                chiavi[fen4] = ident
                meta[ident] = md
    else:
        for n, g in enumerate(leggi_pgn(path), 1):
            ident = g['h'].get('Event', f'linea{n:04d}')
            if ident in meta:
                ident = f'{ident}#{n}'
            md = {}
            for k in ('Pwin', 'DeltaWDL'):
                if k in g['h']:
                    try:
                        md[k] = float(g['h'][k])
                    except ValueError:
                        pass
            chiavi[tuple(g['mosse'])] = ident
            meta[ident] = md
    return chiavi, meta


def chiave_apertura(g, mappa):
    """Identificativo della posizione di partenza di una partita."""
    if g['h'].get('FEN'):
        k = chiave_fen(g['h']['FEN'])
    else:
        k = tuple(g['mosse'][:lunghezza_libro(g)])
    if mappa is not None and k in mappa:
        return mappa[k]
    return k if isinstance(k, str) else ' '.join(k)


# ------------------------------------------------------------------ statistica
def elo(s):
    s = min(max(s, 1e-9), 1 - 1e-9)
    return -400.0 * math.log10(1.0 / s - 1.0)


def elo_es(s, es):
    return es * 400.0 / (math.log(10) * s * (1 - s))


def trinomiale(punti):
    n = len(punti)
    s = sum(punti) / n
    var = sum((x - s) ** 2 for x in punti) / n
    es = math.sqrt(var / n)
    z = (s - 0.5) / es if es > 0 else 0.0
    return dict(partite=n, V=sum(x == 1 for x in punti), P=sum(x == .5 for x in punti),
                S=sum(x == 0 for x in punti), punteggio=s, es=es, z=z,
                p=2 * sps.norm.sf(abs(z)), elo=elo(s), elo_inf=elo(s - 1.96 * es), elo_sup=elo(s + 1.96 * es))


def pentanomiale(coppie):
    n = len(coppie)
    per = [x / 2 for x in coppie]
    s = sum(per) / n
    var = sum((x - s) ** 2 for x in per) / n
    es = math.sqrt(var / n)
    z = (s - 0.5) / es if es > 0 else 0.0
    f = collections.Counter(coppie)
    return dict(coppie=n, conteggi=[f.get(k, 0) for k in (0, .5, 1, 1.5, 2)], punteggio=s, var_coppia=var,
                es=es, z=z, p=2 * sps.norm.sf(abs(z)), elo=elo(s), elo_es=elo_es(s, es) if es > 0 else 0.0,
                elo_inf=elo(s - 1.96 * es), elo_sup=elo(s + 1.96 * es),
                t1=(s - 0.5) / math.sqrt(2 * var) if var > 0 else 0.0)


def cluster(gruppi, B=10000):
    medie = np.array([sum(c) / len(c) for c in gruppi])
    k = len(medie)
    if k < 3:
        return None
    s = medie.mean()
    es = medie.std(ddof=1) / math.sqrt(k)
    t = (s - 0.5) / es if es > 0 else 0.0
    tc = sps.t.ppf(0.975, k - 1)
    dev = [round(sum(c) - len(c) / 2, 6) for c in gruppi]
    nz = [d for d in dev if d != 0]
    pos = sum(d > 0 for d in nz)
    somme = np.array([sum(c) for c in gruppi])
    nn = np.array([len(c) for c in gruppi])
    idx = RNG.integers(0, k, size=(B, k))
    sb = np.clip(somme[idx].sum(1) / nn[idx].sum(1), 1e-9, 1 - 1e-9)
    eb = -400 * np.log10(1 / sb - 1)
    return dict(posizioni=k, punteggio=float(s), es=float(es), t=float(t), gl=k - 1,
                p=float(2 * sps.t.sf(abs(t), k - 1)), elo=elo(s), elo_inf=elo(s - tc * es), elo_sup=elo(s + tc * es),
                migliore_A=pos, migliore_B=len(nz) - pos, pari=k - len(nz),
                p_segno=float(sps.binomtest(pos, len(nz), .5).pvalue) if nz else 1.0,
                boot_inf=float(np.percentile(eb, 2.5)), boot_sup=float(np.percentile(eb, 97.5)))


def coppie_necessarie(elo_effetto, var_coppia, alfa=0.05, potenza=0.80):
    d = 1 / (1 + 10 ** (-elo_effetto / 400)) - 0.5
    return math.ceil((sps.norm.ppf(1 - alfa / 2) + sps.norm.ppf(potenza)) ** 2 * var_coppia / d ** 2)


def bradley_terry(partite, motori, ancora=None, valore=0.0):
    ix = {e: i for i, e in enumerate(motori)}
    m = len(motori)
    n = np.zeros((m, m))
    W = np.zeros(m)
    for g in partite:
        i, j = ix[g['w']], ix[g['b']]
        s = g['sw']
        n[i, j] += 1
        n[j, i] += 1
        W[i] += s
        W[j] += 1 - s
    gam = np.ones(m)
    for _ in range(10000):
        nuovo = np.array([W[i] / sum(n[i, j] / (gam[i] + gam[j]) for j in range(m) if j != i and n[i, j] > 0)
                          if W[i] > 0 else 1e-6 for i in range(m)])
        nuovo /= nuovo[ix[ancora]] if ancora in ix else np.exp(np.mean(np.log(nuovo)))
        if np.max(np.abs(nuovo - gam)) < 1e-12:
            gam = nuovo
            break
        gam = nuovo
    r = 400 * np.log10(gam) + valore
    return {e: float(r[ix[e]]) for e in motori}


def ts(s):
    return datetime.datetime.strptime(s.replace(' UTC', ''), '%Y-%m-%dT%H:%M:%S.%f')


# ------------------------------------------------------------------ analisi
def prepara(percorsi, mappa_aperture):
    partite = []
    for p in percorsi:
        for g in leggi_pgn(p):
            r = g['h'].get('Result')
            if r not in ('1-0', '0-1', '1/2-1/2'):
                continue
            partite.append(dict(
                w=g['h']['White'], b=g['h']['Black'], r=r,
                sw={'1-0': 1.0, '0-1': 0.0, '1/2-1/2': 0.5}[r],
                ap=chiave_apertura(g, mappa_aperture),
                turno=g['h'].get('Round', ''), file=g['file'],
                inizio=g['h'].get('GameStartTime'), fine=g['h'].get('GameEndTime'),
                fe=prima_valutazione_bianco(g), g=g))
    return partite


def forma_coppie(partite):
    """Coppie di partite fra gli stessi motori, sulla stessa posizione, a colori invertiti."""
    gruppi = collections.defaultdict(list)
    for x in partite:
        gruppi[(frozenset((x['w'], x['b'])), x['ap'])].append(x)

    def ordine(x):
        t = x['turno']
        return (x['file'], int(t) if t.isdigit() else 0, x['inizio'] or '')
    coppie, spaiate = [], 0
    for _, gs in gruppi.items():
        gs = sorted(gs, key=ordine)
        aperta = []
        for x in gs:
            compagna = next((y for y in aperta if y['w'] == x['b'] and y['b'] == x['w']), None)
            if compagna:
                aperta.remove(compagna)
                coppie.append((compagna, x))
            else:
                aperta.append(x)
        spaiate += len(aperta)
    return coppie, spaiate


def analizza_coppia(A, B, partite, coppie, favorita):
    pAB = [x for x in partite if {x['w'], x['b']} == {A, B}]
    if not pAB:
        return None
    punti = [x['sw'] if x['w'] == A else 1 - x['sw'] for x in pAB]
    cp = [c for c in coppie if {c[0]['w'], c[0]['b']} == {A, B}]
    punti_coppia = [sum(x['sw'] if x['w'] == A else 1 - x['sw'] for x in c) for c in cp]
    per_ap = collections.defaultdict(list)
    for x, s in zip(pAB, punti):
        per_ap[x['ap']].append(s)
    ris = dict(trinomiale=trinomiale(punti))
    if punti_coppia:
        ris['pentanomiale'] = pentanomiale(punti_coppia)
    ris['cluster'] = cluster([per_ap[k] for k in sorted(per_ap)])
    # McNemar sulla conversione della parte favorita, dentro ciascuna coppia
    n10 = n01 = n11 = n00 = 0
    for c in cp:
        f = favorita.get(c[0]['ap'])
        if f is None:
            continue

        def vince_favorita(x):
            return (x['r'] == '1-0' and f == 1) or (x['r'] == '0-1' and f == -1)

        def fav_motore(x):
            return x['w'] if f == 1 else x['b']
        a = [x for x in c if fav_motore(x) == A]
        b = [x for x in c if fav_motore(x) == B]
        if len(a) != 1 or len(b) != 1:
            continue
        ca, cb = vince_favorita(a[0]), vince_favorita(b[0])
        n11 += ca and cb
        n00 += (not ca) and (not cb)
        n10 += ca and not cb
        n01 += cb and not ca
    ris['mcnemar'] = dict(entrambi=n11, nessuno=n00, solo_A=n10, solo_B=n01,
                          p=float(sps.binomtest(n10, n10 + n01, .5).pvalue) if n10 + n01 else 1.0)
    ris['posizioni'] = len(per_ap)
    ris['partite_per_posizione'] = dict(collections.Counter(len(v) for v in per_ap.values()))
    return ris


def regressione_delta(A, B, partite, meta):
    """Punteggio medio di A per posizione in funzione di Delta WDL e di |Pwin - bersaglio| (OLS pesata)."""
    per_ap = collections.defaultdict(list)
    for x in partite:
        if {x['w'], x['b']} == {A, B}:
            per_ap[x['ap']].append(x['sw'] if x['w'] == A else 1 - x['sw'])
    righe = [(np.mean(v), len(v), meta[k]['DeltaWDL'], abs(meta[k]['Pwin'] - (0.75 if meta[k]['Pwin'] >= 0.5 else 0.25)))
             for k, v in per_ap.items() if k in meta and 'DeltaWDL' in meta[k] and 'Pwin' in meta[k]]
    if len(righe) < 10:
        return None
    y = np.array([r[0] for r in righe])
    w = np.array([r[1] for r in righe], float)
    X = np.column_stack([np.ones(len(righe)), [r[2] for r in righe], [r[3] for r in righe]])
    Wm = np.diag(w)
    XtWX = X.T @ Wm @ X
    beta = np.linalg.solve(XtWX, X.T @ Wm @ y)
    res = y - X @ beta
    # errori standard robusti (sandwich HC1) per i pesi = numero di partite
    meat = X.T @ np.diag((w * res) ** 2) @ X
    cov = np.linalg.inv(XtWX) @ meat @ np.linalg.inv(XtWX) * len(y) / (len(y) - 3)
    es = np.sqrt(np.diag(cov))
    nomi = ['costante', 'DeltaWDL', 'distanza_Pwin']
    return {nomi[i]: dict(coeff=float(beta[i]), es=float(es[i]),
                          p=float(2 * sps.norm.sf(abs(beta[i] / es[i]))) if es[i] > 0 else None) for i in range(3)} | {'posizioni': len(righe)}


def analizza(percorsi, args, mappa, meta, etichetta):
    partite = prepara(percorsi, mappa)
    if not partite:
        sys.exit(f'[ERRORE] Nessuna partita valida in {percorsi}')
    motori = sorted({x['w'] for x in partite} | {x['b'] for x in partite})
    coppie, spaiate = forma_coppie(partite)
    R = dict(etichetta=etichetta, file=percorsi, partite=len(partite), motori=motori,
             coppie=len(coppie), partite_spaiate=spaiate)

    # parte favorita di ciascuna posizione: segno della prima valutazione media (punto di vista del Bianco)
    fe = collections.defaultdict(list)
    for x in partite:
        if x['fe'] is not None:
            fe[x['ap']].append(x['fe'])
    favorita = {k: (1 if st.mean(v) > 0 else -1) for k, v in fe.items() if v and st.mean(v) != 0}

    # classifica e tabella incrociata
    tab = {}
    for e in motori:
        pts = [x['sw'] if x['w'] == e else 1 - x['sw'] for x in partite if e in (x['w'], x['b'])]
        tab[e] = dict(partite=len(pts), V=sum(p == 1 for p in pts), P=sum(p == .5 for p in pts),
                      S=sum(p == 0 for p in pts), punti=sum(pts))
    R['classifica'] = tab

    # verifica del disegno: tutte le coppie di motori devono avere giocato le stesse posizioni
    copertura = {}
    insiemi = {}
    for i, a in enumerate(motori):
        for b in motori[i + 1:]:
            c = collections.Counter(x['ap'] for x in partite if {x['w'], x['b']} == {a, b})
            if c:
                copertura[f'{a} - {b}'] = dict(posizioni=len(c), partite=sum(c.values()),
                                               partite_per_posizione=dict(collections.Counter(c.values())))
                insiemi[(a, b)] = set(c)
    tutte = set(x['ap'] for x in partite)
    R['copertura'] = copertura
    R['disegno_incrociato'] = all(s == tutte for s in insiemi.values()) and len(insiemi) == len(motori) * (len(motori) - 1) // 2
    R['posizioni'] = len(tutte)

    # coppie di motori
    R['accoppiamenti'] = {}
    for i, a in enumerate(motori):
        for b in motori[i + 1:]:
            r = analizza_coppia(a, b, partite, coppie, favorita)
            if r:
                R['accoppiamenti'][f'{a} vs {b}'] = r

    # Bradley-Terry con bootstrap sulle posizioni
    if len(motori) >= 2:
        ancora = args.ancora if args.ancora in motori else motori[0]
        R['bt'] = bradley_terry(partite, motori, ancora, args.elo_ancora)
        per_ap = collections.defaultdict(list)
        for x in partite:
            per_ap[x['ap']].append(x)
        chiavi = sorted(per_ap)
        boot = {e: [] for e in motori}
        for _ in range(args.bootstrap):
            camp = [x for k in RNG.choice(len(chiavi), size=len(chiavi)) for x in per_ap[chiavi[k]]]
            if len({x['w'] for x in camp} | {x['b'] for x in camp}) < len(motori):
                continue
            r = bradley_terry(camp, motori, ancora, args.elo_ancora)
            for e in motori:
                boot[e].append(r[e])
        R['bt_ic'] = {e: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for e, v in boot.items() if v}
        R['bt_ancora'] = [ancora, args.elo_ancora]

    # proprieta' delle posizioni
    vf = sum(1 for x in partite if x['ap'] in favorita and ((x['r'] == '1-0' and favorita[x['ap']] == 1) or (x['r'] == '0-1' and favorita[x['ap']] == -1)))
    vs = sum(1 for x in partite if x['ap'] in favorita and ((x['r'] == '1-0' and favorita[x['ap']] == -1) or (x['r'] == '0-1' and favorita[x['ap']] == 1)))
    R['parte_favorita'] = dict(vittorie_favorita=vf, vittorie_sfavorita=vs,
                               patte=sum(x['r'] == '1/2-1/2' for x in partite),
                               posizioni_favorito_bianco=sum(v == 1 for v in favorita.values()),
                               posizioni_favorito_nero=sum(v == -1 for v in favorita.values()))
    dec = collections.Counter()
    tot = collections.Counter()
    for x in partite:
        tot[x['ap']] += 1
        dec[x['ap']] += x['r'] != '1/2-1/2'
    R['decisive'] = dict(totale=sum(dec.values()), quota=sum(dec.values()) / len(partite),
                         posizioni_tutte_patte=sum(1 for k in tot if dec[k] == 0),
                         posizioni_tutte_decisive=sum(1 for k in tot if dec[k] == tot[k]))
    medie_fe = {k: st.mean(v) for k, v in fe.items() if v}
    fasce = [(0, .8), (.8, .9), (.9, 1.0), (1.0, 1.1), (1.1, 1.2), (1.2, 99)]
    R['decisive_per_fascia_eval'] = []
    for lo, hi in fasce:
        ks = [k for k in tot if k in medie_fe and lo <= abs(medie_fe[k]) < hi]
        n = sum(tot[k] for k in ks)
        R['decisive_per_fascia_eval'].append(dict(fascia=f'{lo}-{hi}', posizioni=len(ks), partite=n,
                                                  quota=(sum(dec[k] for k in ks) / n) if n else None))
    # condizioni di esecuzione
    try:
        ev = sorted([(ts(x['inizio']), 1) for x in partite if x['inizio']] + [(ts(x['fine']), -1) for x in partite if x['fine']])
        cur = mx = 0
        for _, d in ev:
            cur += d
            mx = max(mx, cur)
        R['esecuzione'] = dict(inizio=str(ev[0][0]), fine=str(ev[-1][0]),
                               ore=(ev[-1][0] - ev[0][0]).total_seconds() / 3600, max_partite_simultanee=mx,
                               durata_media_min=st.mean((ts(x['fine']) - ts(x['inizio'])).total_seconds() / 60
                                                        for x in partite if x['inizio'] and x['fine']))
    except (ValueError, IndexError, TypeError):
        R['esecuzione'] = None
    term = collections.Counter()
    for x in partite:
        ult = x['g']['com'][-1] if x['g']['com'] else ''
        term[ult.split(',')[-1].strip() or x['g']['h'].get('Termination', '')] += 1
    R['terminazioni'] = dict(term)
    prof = collections.defaultdict(list)
    for x in partite:
        g = x['g']
        pari = chi_muove_per_primo(g) == 'w'
        for k in range(lunghezza_libro(g), len(g['mosse'])):
            e = valuta(g['com'][k])
            if e:
                bianco = (k % 2 == 0) == pari
                prof[g['h']['White'] if bianco else g['h']['Black']].append(e[1])
    R['profondita_mediana'] = {e: st.median(v) for e, v in prof.items()}

    # coppia di interesse: potenza e regressione su Delta WDL
    if args.a and args.b:
        chiave = f'{args.a} vs {args.b}' if f'{args.a} vs {args.b}' in R['accoppiamenti'] else f'{args.b} vs {args.a}'
        if chiave in R['accoppiamenti']:
            pen = R['accoppiamenti'][chiave].get('pentanomiale')
            if pen and pen['var_coppia'] > 0:
                R['potenza'] = {str(e): coppie_necessarie(e, pen['var_coppia']) for e in (5, 10, 15, 20, 30)}
            if meta:
                R['regressione_delta'] = regressione_delta(args.a, args.b, partite, meta)
    return R


def fp(p):
    """p-value leggibile."""
    return '< 0.001' if p < 0.001 else f'{p:.3f}'


def riga_md(*celle):
    return '| ' + ' | '.join(str(c) for c in celle) + ' |'


def markdown(R, conf=None):
    L = [f"# {R['etichetta']}", '', f"Partite: {R['partite']} · posizioni: {R['posizioni']} · coppie a colori invertiti: {R['coppie']} (partite non appaiate: {R['partite_spaiate']})", '']
    L.append('Disegno incrociato (ogni coppia di motori sulle stesse posizioni): ' + ('SI' if R['disegno_incrociato'] else '**NO**'))
    L += ['', '## Classifica', '', riga_md('Motore', 'Partite', 'V-P-S', 'Punti', 'Rating BT', 'IC 95%'), riga_md(*['---'] * 6)]
    for e, t in sorted(R['classifica'].items(), key=lambda kv: -kv[1]['punti']):
        bt = R.get('bt', {}).get(e)
        ic = R.get('bt_ic', {}).get(e)
        L.append(riga_md(e, t['partite'], f"{t['V']}-{t['P']}-{t['S']}", t['punti'],
                         f'{bt:.1f}' if bt is not None else '', f'[{ic[0]:.1f}; {ic[1]:.1f}]' if ic else ''))
    L += ['', '## Accoppiamenti (modello pentanomiale)', '',
          riga_md('A vs B', 'V-P-S di A', 'Punteggio A', 'Coppie 0/½/1/1½/2', 'Elo A-B [IC 95%]', 'p', 'p cluster', 'McNemar p'),
          riga_md(*['---'] * 8)]
    for k, r in R['accoppiamenti'].items():
        t, p, c = r['trinomiale'], r.get('pentanomiale'), r.get('cluster')
        L.append(riga_md(k, f"{t['V']}-{t['P']}-{t['S']}", f"{100 * t['punteggio']:.1f}%",
                         '/'.join(map(str, p['conteggi'])) if p else '',
                         f"{p['elo']:+.1f} [{p['elo_inf']:+.1f}; {p['elo_sup']:+.1f}]" if p else '',
                         fp(p['p']) if p else '', fp(c['p']) if c else '', fp(r['mcnemar']['p'])))
    pf = R['parte_favorita']
    L += ['', '## Posizioni', '',
          f"Partite decisive: {R['decisive']['totale']} ({100 * R['decisive']['quota']:.1f}%). Vittorie della parte favorita: {pf['vittorie_favorita']}; della parte sfavorita: {pf['vittorie_sfavorita']}; patte: {pf['patte']}.",
          f"Posizioni sempre patte: {R['decisive']['posizioni_tutte_patte']}; sempre decisive: {R['decisive']['posizioni_tutte_decisive']}.", '']
    if R.get('potenza'):
        L += ['## Potenza (80%, alfa 0,05)', '', ', '.join(f'{k} Elo: {v} coppie' for k, v in R['potenza'].items()), '']
    if conf:
        L += ['## Interazione', '', f"Differenza Elo ({conf['coppia']}) fra '{conf['etichetta_1']}' e '{conf['etichetta_2']}': {conf['differenza']:+.1f} Elo, ES {conf['es']:.1f}, z = {conf['z']:.2f}, p = {fp(conf['p'])}", '']
    if R.get('esecuzione'):
        e = R['esecuzione']
        L += ['## Esecuzione', '', f"Dal {e['inizio']} al {e['fine']} ({e['ore']:.1f} h); massimo {e['max_partite_simultanee']} partite simultanee; durata media {e['durata_media_min']:.1f} min.", '']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser(description='Statistiche di match e tornei cutechess sulle pepite')
    ap.add_argument('--pgn', nargs='+', required=True, help='uno o piu file PGN prodotti da cutechess-cli')
    ap.add_argument('--aperture', help='file delle posizioni di partenza (.epd di genera_pgn.py oppure .pgn di linee)')
    ap.add_argument('--a', help='primo motore della coppia di interesse (nome come nel PGN)')
    ap.add_argument('--b', help='secondo motore della coppia di interesse')
    ap.add_argument('--ancora', help='motore di riferimento per i rating (nome come nel PGN)')
    ap.add_argument('--elo-ancora', type=float, default=0.0, help='rating assegnato al motore di riferimento (default 0)')
    ap.add_argument('--confronta', nargs='+', help='PGN di un secondo insieme di posizioni (es. controllo) per il test d interazione')
    ap.add_argument('--bootstrap', type=int, default=2000, help='repliche bootstrap (default 2000)')
    ap.add_argument('--etichetta', default='Esperimento', help='titolo del rapporto')
    ap.add_argument('--out', default='statistiche', help='prefisso dei file di output (.json e .md)')
    args = ap.parse_args()

    mappa, meta = (None, {})
    if args.aperture:
        mappa, meta = leggi_aperture(args.aperture)
    R = analizza(args.pgn, args, mappa, meta, args.etichetta)
    if args.a and args.b:
        for n in (args.a, args.b):
            if n not in R['motori']:
                sys.exit(f"[ERRORE] Motore '{n}' non trovato. Motori nel PGN: {R['motori']}")

    conf = None
    if args.confronta:
        if not (args.a and args.b):
            sys.exit('[ERRORE] --confronta richiede --a e --b')
        R2 = analizza(args.confronta, args, None, {}, 'confronto')
        k1 = next(k for k in R['accoppiamenti'] if set(k.split(' vs ')) == {args.a, args.b})
        k2 = next(k for k in R2['accoppiamenti'] if set(k.split(' vs ')) == {args.a, args.b})
        p1, p2 = R['accoppiamenti'][k1]['pentanomiale'], R2['accoppiamenti'][k2]['pentanomiale']
        segno1 = 1 if k1.startswith(args.a) else -1
        segno2 = 1 if k2.startswith(args.a) else -1
        d = segno1 * p1['elo'] - segno2 * p2['elo']
        es = math.hypot(p1['elo_es'], p2['elo_es'])
        z = d / es
        conf = dict(coppia=f'{args.a} - {args.b}', etichetta_1=args.etichetta, etichetta_2='confronto',
                    elo_1=segno1 * p1['elo'], elo_2=segno2 * p2['elo'], differenza=d, es=es, z=z,
                    p=float(2 * sps.norm.sf(abs(z))))
        R['confronto'] = dict(risultati=R2, interazione=conf)

    with open(args.out + '.json', 'w', encoding='utf-8') as f:
        json.dump(R, f, indent=1, ensure_ascii=False, default=float)
    with open(args.out + '.md', 'w', encoding='utf-8') as f:
        f.write(markdown(R, conf))
    print(markdown(R, conf))
    print(f'\n[OK] Scritti {args.out}.json e {args.out}.md')


if __name__ == '__main__':
    main()
