"""
Registro incrementale delle posizioni analizzate e criteri delle pepite.

- Registro: ogni posizione analizzata viene scritta SUBITO in un CSV (una riga per FEN),
  pepita o no. Se l'estrazione si interrompe (crash, riavvio, CTRL+C), al rilancio le FEN
  gia' presenti nel registro non vengono rianalizzate: i valori W/D/L salvati vengono
  riusati e le soglie correnti del config vengono riapplicate. Cosi' si possono anche
  cambiare le soglie (tolleranza, delta, opposite_max) senza ripetere le analisi.
- classifica(): la regola della pepita, identica a quella di engine_worker.py dopo la patch
  del 12/11/2026 (Pwin dal punto di vista del Bianco, L = 0 per le pepite a 0,75,
  W = 0 per quelle a 0,25), con la soglia del Delta separata dalla tolleranza su Pwin.

Il modulo non dipende da python-chess, quindi si puo' collaudare da solo.
"""
import csv
import os

CAMPI = [
    "FEN", "Stato", "Tratto", "Semimossa",
    "W1", "D1", "L1", "W2", "D2", "L2", "Pwin1", "Pwin2", "Delta",
    "CP1", "CP2", "Mossa1", "Mossa2",
    "Profondita1", "Profondita2", "SelDepth", "Nodi", "NPS", "Tempo", "TBHits",
    "Fase", "Centro", "Tensione", "Imbalance",
    "Data", "Variante_PGN", "Motore",
]

# Stati che non richiedono una nuova analisi alla ripresa ("Errore" invece si rianalizza)
STATI_CONCLUSI = {"Nugget", "Non nugget", "Scartata"}


def frazioni_wdl(wins, draws, losses):
    """Converte i conteggi WDL del motore (per mille) in frazioni che sommano a 1."""
    tot = wins + draws + losses
    if tot <= 0:
        raise ValueError("WDL con totale nullo")
    return wins / tot, draws / tot, losses / tot


def classifica(wdl1, wdl2, wdl_tolerance, delta_max, opposite_max):
    """
    Applica la regola della pepita alle terne (W, D, L) delle due linee migliori,
    entrambe dal punto di vista del Bianco.

    Restituisce un dizionario con: pepita (bool), tipo ('bianca', 'nera' o None),
    pwin1, pwin2 (= W + D/2) e delta (= |pwin1 - pwin2|).
    """
    w1, d1, l1 = wdl1
    w2, d2, l2 = wdl2
    pwin1 = w1 + d1 / 2.0
    pwin2 = w2 + d2 / 2.0
    delta = abs(pwin1 - pwin2)
    eps = 1e-9
    bianca = (0.75 - wdl_tolerance - eps <= pwin1 <= 0.75 + wdl_tolerance + eps) and l1 <= opposite_max + eps
    nera = (0.25 - wdl_tolerance - eps <= pwin1 <= 0.25 + wdl_tolerance + eps) and w1 <= opposite_max + eps
    delta_ok = delta <= delta_max + eps
    tipo = "bianca" if bianca else ("nera" if nera else None)
    return {"pepita": bool(tipo) and delta_ok, "tipo": tipo, "pwin1": pwin1, "pwin2": pwin2, "delta": delta}


def _num(x):
    if x is None or x == "":
        return None
    return float(x)


def wdl_da_riga(riga):
    """Restituisce ((W1, D1, L1), (W2, D2, L2)) da una riga del registro, o None se mancano."""
    vals = [_num(riga.get(k)) for k in ("W1", "D1", "L1", "W2", "D2", "L2")]
    if any(v is None for v in vals):
        return None
    return tuple(vals[:3]), tuple(vals[3:])


class Registro:
    """CSV in sola aggiunta con tutte le posizioni analizzate; riletto alla ripresa."""

    def __init__(self, path):
        self.path = path
        self.fatte = {}
        self.righe_scartate = 0
        esiste = os.path.exists(path) and os.path.getsize(path) > 0
        if esiste:
            with open(path, newline="", encoding="utf-8") as f:
                for riga in csv.DictReader(f):
                    # Una riga troncata (interruzione durante la scrittura) non ha lo Stato: si ignora
                    if not riga.get("FEN") or riga.get("Stato") not in STATI_CONCLUSI:
                        self.righe_scartate += 1
                        continue
                    self.fatte[riga["FEN"]] = riga
            # Se l'ultima riga e' stata troncata, il file non termina con un a capo: lo aggiungiamo
            with open(path, "rb") as fb:
                fb.seek(-1, os.SEEK_END)
                manca_a_capo = fb.read(1) not in (b"\n", b"\r")
        self._f = open(path, "a", newline="", encoding="utf-8")
        if esiste and manca_a_capo:
            self._f.write("\n")
        self._w = csv.DictWriter(self._f, fieldnames=CAMPI, extrasaction="ignore")
        if not esiste:
            self._w.writeheader()
            self._f.flush()

    def __len__(self):
        return len(self.fatte)

    def gia_analizzata(self, fen):
        """La riga salvata per questa FEN, oppure None se va (ri)analizzata."""
        return self.fatte.get(fen)

    def scrivi(self, riga):
        """Scrive subito su disco: un'interruzione fa perdere al massimo la riga in corso."""
        self._w.writerow(riga)
        self._f.flush()
        if riga.get("Stato") in STATI_CONCLUSI:
            self.fatte[riga["FEN"]] = riga

    def chiudi(self):
        self._f.close()
