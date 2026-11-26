"""Posizioni finali delle partite patte per punteggio, rianalizzate (domanda 6).

Uso (dalla radice del repository):
    python3 verifiche/patte_punteggio.py --motore /percorso/stockfish --ms 60000 --threads 4 --hash 2048 \
        [--syzygy /percorso/syzygy] [--evalfile rete.nnue] [--processi 47]

Rigioca fino all'ultima mossa ogni partita aggiudicata patta dalla regola del punteggio
("Draw by adjudication": entrambi i motori entro 0,10 pedoni per dieci mosse dopo la mossa 40),
analizza la posizione finale a tempo fisso e riporta la valutazione e la WDL. Somma poi, per fase,
le probabilita' di vittoria della parte favorita e della sfavorita: e' il numero atteso di partite
che il gioco avrebbe potuto rendere decisive. Con l'oracolo del lavoro (Stockfish 19, 60 s, 4 thread,
2 GB, Syzygy) e' la verifica definitiva; con un'analisi breve e' solo un ordine di grandezza.
Scrive rapporti/verifiche_patte_punteggio.json e .md.
"""
import argparse
import json
import os
import statistics
from concurrent.futures import ProcessPoolExecutor

from esiti_partite import leggi_epd, partite, trova_fasi
from scacchi_min import Motore, k4, token_san


def lavoro(arg):
    motore, opzioni, ms, compiti = arg
    m = Motore(motore, opzioni)
    out = []
    for fase, fen0, san, fav in compiti:
        m.manda('ucinewgame')
        mosse, fens = m.rigioca(fen0, san)
        score, wdl = m.analizza(fen0, mosse, ms)
        out.append(dict(fase=fase, fen=fens[-1], semimosse=len(mosse), score=score, wdl=wdl, fav=fav))
    m.chiudi()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='docs/revisione2026')
    ap.add_argument('--motore', required=True)
    ap.add_argument('--ms', type=int, default=60000)
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--hash', type=int, default=2048)
    ap.add_argument('--syzygy')
    ap.add_argument('--evalfile')
    ap.add_argument('--processi', type=int, default=1)
    ap.add_argument('--limite', type=int, help='solo le prime N partite (per una prova veloce)')
    a = ap.parse_args()
    opzioni = {'Threads': a.threads, 'Hash': a.hash, 'UCI_ShowWDL': 'true'}
    if a.syzygy:
        opzioni['SyzygyPath'] = a.syzygy
    if a.evalfile:
        opzioni['EvalFile'] = a.evalfile

    compiti, partite_fase, decisive_fase = [], {}, {}
    for fase, pgns, epd in trova_fasi(a.base):
        pw = leggi_epd(epd)
        partite_fase[fase] = decisive_fase[fase] = 0
        for p in pgns:
            for tag, mosse, motivo in partite(p):
                partite_fase[fase] += 1
                decisive_fase[fase] += tag.get('Result') in ('1-0', '0-1')
                if tag.get('Termination') == 'adjudication' and motivo.endswith('Draw by adjudication'):
                    v = pw.get(k4(tag['FEN']))
                    compiti.append((fase, tag['FEN'], token_san(mosse), 'w' if v is not None and v > 0.5 else 'b'))
    if a.limite:
        compiti = compiti[:a.limite]
    blocchi = [compiti[i::a.processi] for i in range(a.processi)]
    with ProcessPoolExecutor(a.processi) as ex:
        ris = [x for parte in ex.map(lavoro, [(a.motore, opzioni, a.ms, b) for b in blocchi]) for x in parte]

    def cp_bianco(r):
        s = (r['score'] or '').split()
        if len(s) < 2:
            return None
        v = 10000 * (1 if int(s[1]) > 0 else -1) if s[0] == 'mate' else int(s[1])
        return v if r['fen'].split()[1] == 'w' else -v

    attese = {f: [0.0, 0.0] for f in partite_fase}
    oltre = {'favorita_sopra_10': 0, 'sfavorita_sopra_5': 0}
    for r in ris:
        w, d, l = r['wdl']
        bianco, nero = (w, l) if r['fen'].split()[1] == 'w' else (l, w)
        fav, sfav = (bianco, nero) if r['fav'] == 'w' else (nero, bianco)
        attese[r['fase']][0] += fav / 1000
        attese[r['fase']][1] += sfav / 1000
        oltre['favorita_sopra_10'] += fav > 100
        oltre['sfavorita_sopra_5'] += sfav > 50
    val = [abs(v) for v in map(cp_bianco, ris) if v is not None]
    registro = dict(opzioni, ms=a.ms, motore=os.path.basename(a.motore))
    for k in ('EvalFile', 'SyzygyPath'):
        if k in registro:
            registro[k] = os.path.basename(str(registro[k]).rstrip('/'))
    out = {'opzioni': registro, 'patte_per_punteggio': len(ris),
           'valutazione_assoluta_mediana_cp': statistics.median(val), 'almeno_100_cp': sum(v >= 100 for v in val),
           'almeno_200_cp': sum(v >= 200 for v in val), **oltre, 'per_fase': {}}
    for f, (fa, sf) in attese.items():
        out['per_fase'][f] = {'partite': partite_fase[f], 'decisive': decisive_fase[f],
                              'vittorie_attese_favorita': round(fa, 1), 'vittorie_attese_sfavorita': round(sf, 2),
                              'quota_decisive': round(decisive_fase[f] / partite_fase[f], 4),
                              'quota_decisive_attesa': round((decisive_fase[f] + fa) / partite_fase[f], 4)}
    dest = os.path.join(a.base, 'rapporti', 'verifiche_patte_punteggio')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    json.dump(dict(out, posizioni=ris), open(dest + '.json', 'w', encoding='utf-8'), indent=1)
    righe = ['# Partite patte per punteggio: posizioni finali rianalizzate', '',
             f"Motore {out['opzioni']['motore']}, {a.ms} ms, {a.threads} thread. Partite: {len(ris)}. "
             f"Valutazione assoluta mediana {out['valutazione_assoluta_mediana_cp']} cp; almeno 1 pedone in "
             f"{out['almeno_100_cp']}, almeno 2 in {out['almeno_200_cp']}. Parte favorita oltre il 10% di vittoria in "
             f"{oltre['favorita_sopra_10']}; sfavorita oltre il 5% in {oltre['sfavorita_sopra_5']}.", '',
             '| Fase | Partite | Decisive | Vittorie attese della favorita | della sfavorita | Quota decisive | attesa |',
             '|---|---|---|---|---|---|---|']
    for f, v in out['per_fase'].items():
        righe.append(f"| {f} | {v['partite']} | {v['decisive']} | {v['vittorie_attese_favorita']} | "
                     f"{v['vittorie_attese_sfavorita']} | {100 * v['quota_decisive']:.1f}% | "
                     f"{100 * v['quota_decisive_attesa']:.1f}% |")
    open(dest + '.md', 'w', encoding='utf-8').write('\n'.join(righe) + '\n')
    print('\n'.join(righe))
    print('scritti', dest + '.json', dest + '.md')


if __name__ == '__main__':
    main()
