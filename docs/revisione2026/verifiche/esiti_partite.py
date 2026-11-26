"""Esiti delle partite di tutte le fasi (domande 5 e 6).

Uso (dalla radice del repository):
    python3 verifiche/esiti_partite.py [--base docs/revisione2026]

Per ogni cartella di fase in risultati/ (C, D, E4, E5, E1, F) legge i PGN (anche .gz) e il file .epd
della fase, da cui prende la Pwin prima della partita (campo c0 "Pwin=..."): la parte favorita e' il
Bianco se Pwin > 0,5. Conta partite, decisive, vittorie della parte favorita e della sfavorita, partite
per posizione e il modo in cui ogni partita e' finita (tag Termination e ultimo commento di
cutechess-cli). Calcola poi il limite superiore unilaterale al 95% sul tasso di vittoria della parte
sfavorita (zero eventi): partite indipendenti, posizioni come unita', e per illustrazione con una
correlazione intraclasse data. Scrive rapporti/verifiche_esiti.json e .md.
"""
import argparse
import glob
import json
import os
import re
from collections import Counter

from scacchi_min import apri, k4

FASI = [('C', '_pool_robusto'), ('D', '_rr_top100_robusto'), ('E4', '_pool_tc60'),
        ('E5', '_pool_tc3600'), ('E1', '_controllo_uho'), ('F', '_fasce_tc1500')]


def trova_fasi(base):
    """[(nome, [pgn], epd)] per le fasi che hanno partite."""
    out = []
    for nome, suff in FASI:
        dirs = sorted(glob.glob(os.path.join(base, 'risultati', '*' + suff)))
        if not dirs:
            print(f'[AVVISO] cartella della fase {nome} non trovata')
            continue
        d = dirs[-1]
        pgn = sorted(glob.glob(os.path.join(d, 'partite.pgn*'))) or sorted(glob.glob(os.path.join(d, 'partite_*.pgn*')))
        epd = [e for e in sorted(glob.glob(os.path.join(d, '*.epd'))) if 'Pwin=' in apri(e).read()]
        out.append((nome, pgn, epd[0] if epd else None))
    return out


def leggi_epd(path):
    out = {}
    for riga in apri(path):
        if riga.strip():
            m = re.search(r'Pwin=([0-9.]+)', riga)
            out[k4(riga)] = float(m.group(1)) if m else None
    return out


def partite(path):
    """(tag, testo delle mosse, motivo della fine) per ogni partita del PGN."""
    testo = apri(path).read()
    for blocco in re.split(r'\n(?=\[Event )', testo):
        if not blocco.strip():
            continue
        tag = dict(re.findall(r'^\[(\w+) "([^"]*)"\]', blocco, re.M))
        mosse = blocco[blocco.rfind(']') + 1:]
        com = re.findall(r'\{([^{}]*)\}', mosse)
        ultimo = com[-1] if com else ''
        motivo = ultimo.split(', ')[-1].strip() if ', ' in ultimo else ultimo.strip()
        yield tag, mosse, motivo


def fine(tag, motivo):
    r, m = tag.get('Result'), motivo.lower()
    if 'syzygy' in m:
        return 'tablebase, vittoria' if r in ('1-0', '0-1') else 'tablebase, patta'
    if tag.get('Termination') == 'adjudication':
        if 'maximal game length' in m:
            return 'limite di 200 mosse'
        return 'regola dei 10 pedoni' if r in ('1-0', '0-1') else 'patta per punteggio'
    if 'mates' in m:
        return 'matto'
    if 'repetition' in m:
        return 'ripetizione'
    if 'stalemate' in m:
        return 'stallo'
    if 'fifty' in m:
        return '50 mosse'
    if 'insufficient' in m:
        return 'materiale insufficiente'
    return 'altro: ' + motivo


def limite(n):
    """Limite superiore unilaterale al 95% con zero eventi su n prove indipendenti."""
    return 1 - 0.05 ** (1 / n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='docs/revisione2026')
    ap.add_argument('--icc', type=float, nargs='*', default=[0.20, 0.44])
    a = ap.parse_args()
    ris, per_pos_tot = {}, Counter()
    for nome, pgns, epd in trova_fasi(a.base):
        pw = leggi_epd(epd)
        c = Counter()
        tipi = Counter()
        per_pos = Counter()
        for p in pgns:
            for tag, mosse, motivo in partite(p):
                c['partite'] += 1
                f = k4(tag.get('FEN', ''))
                per_pos[f] += 1
                tipi[fine(tag, motivo)] += 1
                v = pw.get(f)
                if v is None:
                    c['senza_pwin'] += 1
                r = tag.get('Result')
                if r in ('1-0', '0-1'):
                    c['decisive'] += 1
                    if v is not None:
                        fav = 'w' if v > 0.5 else 'b'
                        c['vittorie_favorita' if (r == '1-0') == (fav == 'w') else 'vittorie_sfavorita'] += 1
        per_pos_tot.update(per_pos)
        ris[nome] = dict(c, posizioni=len(per_pos), partite_per_posizione=dict(Counter(per_pos.values())),
                         fine=dict(tipi.most_common()),
                         aggiudicate=sum(v for k, v in tipi.items()
                                         if k.startswith(('tablebase', 'regola', 'patta per', 'limite'))))
    tot = {k: sum(v.get(k, 0) for v in ris.values())
           for k in ('partite', 'decisive', 'vittorie_favorita', 'vittorie_sfavorita', 'aggiudicate')}
    n, k = tot['partite'], len(per_pos_tot)
    limiti = {'partite_indipendenti': limite(n), 'posizioni_come_unita': limite(k)}
    for icc in a.icc:
        neff = sum(m / (1 + (m - 1) * icc) for m in per_pos_tot.values())
        limiti[f'icc_{icc}'] = {'n_effettivo': round(neff), 'limite': limite(neff)}
    out = {'fasi': ris, 'totale': dict(tot, posizioni_distinte=k,
                                        partite_per_posizione=dict(Counter(per_pos_tot.values()))),
           'limite_superiore_95_vittoria_sfavorita': limiti}
    dest = os.path.join(a.base, 'rapporti', 'verifiche_esiti')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    json.dump(out, open(dest + '.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    righe = ['# Esiti delle partite di tutte le fasi', '',
             '| Fase | Partite | Posizioni | Decisive | Vinte dalla sfavorita | 10 pedoni | Patta per punteggio '
             '| Tablebase vittoria / patta | 200 mosse | Finite giocando |', '|---|---|---|---|---|---|---|---|---|---|']
    for nome, v in ris.items():
        f = v['fine']
        giocate = v['partite'] - v['aggiudicate']
        righe.append(f"| {nome} | {v['partite']} | {v['posizioni']} | {v.get('decisive', 0)} | "
                     f"{v.get('vittorie_sfavorita', 0)} | {f.get('regola dei 10 pedoni', 0)} | "
                     f"{f.get('patta per punteggio', 0)} | {f.get('tablebase, vittoria', 0)} / "
                     f"{f.get('tablebase, patta', 0)} | {f.get('limite di 200 mosse', 0)} | {giocate} |")
    righe += ['', f"Totale: {n} partite su {k} posizioni distinte; decisive {tot['decisive']}; "
                  f"vittorie della parte sfavorita {tot['vittorie_sfavorita']}; aggiudicate {tot['aggiudicate']} "
                  f"({100 * tot['aggiudicate'] / n:.1f}%).", '',
              'Limite superiore unilaterale al 95% sul tasso di vittoria della parte sfavorita: '
              f"{100 * limiti['partite_indipendenti']:.3f}% per partita con partite indipendenti, "
              f"{100 * limiti['posizioni_come_unita']:.2f}% con le {k} posizioni come unita'."]
    for icc in a.icc:
        L = limiti[f'icc_{icc}']
        righe.append(f"Con correlazione intraclasse {icc}: n effettivo {L['n_effettivo']}, limite {100 * L['limite']:.2f}%.")
    open(dest + '.md', 'w', encoding='utf-8').write('\n'.join(righe) + '\n')
    print('\n'.join(righe))
    print('scritti', dest + '.json', dest + '.md')


if __name__ == '__main__':
    main()
