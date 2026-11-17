"""Collaudo del registro incrementale e della regola delle pepite (non richiede python-chess).
Uso: python tests/test_registro.py"""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from registro import Registro, classifica, frazioni_wdl, wdl_da_riga

CRIT = dict(wdl_tolerance=0.06, delta_max=0.06, opposite_max=0.0)

def test_classifica():
    # pepita bianca ideale: (0.5, 0.5, 0) e seconda linea vicina
    e = classifica((0.5, 0.5, 0.0), (0.48, 0.52, 0.0), **CRIT)
    assert e["pepita"] and e["tipo"] == "bianca" and abs(e["pwin1"] - 0.75) < 1e-12 and abs(e["delta"] - 0.01) < 1e-12
    # pepita nera: (0, 0.5, 0.5)
    e = classifica((0.0, 0.5, 0.5), (0.0, 0.46, 0.54), **CRIT)
    assert e["pepita"] and e["tipo"] == "nera"
    # L > 0 con opposite_max = 0: non e' pepita
    assert not classifica((0.52, 0.47, 0.01), (0.5, 0.5, 0.0), **CRIT)["pepita"]
    # ...ma lo e' con opposite_max = 0.02
    assert classifica((0.52, 0.47, 0.01), (0.5, 0.5, 0.0), wdl_tolerance=0.06, delta_max=0.06, opposite_max=0.02)["pepita"]
    # Delta oltre la soglia
    assert not classifica((0.5, 0.5, 0.0), (0.3, 0.7, 0.0), **CRIT)["pepita"]
    # delta_max separato dalla tolleranza su Pwin
    assert not classifica((0.5, 0.5, 0.0), (0.44, 0.56, 0.0), wdl_tolerance=0.06, delta_max=0.02, opposite_max=0.0)["pepita"]
    # Pwin fuori finestra (0.60)
    assert not classifica((0.2, 0.8, 0.0), (0.2, 0.8, 0.0), **CRIT)["pepita"]
    # bordi della finestra (0.69 e 0.81) inclusi
    assert classifica((0.38, 0.62, 0.0), (0.38, 0.62, 0.0), **CRIT)["pepita"]
    assert classifica((0.62, 0.38, 0.0), (0.62, 0.38, 0.0), **CRIT)["pepita"]
    assert frazioni_wdl(500, 500, 0) == (0.5, 0.5, 0.0)

def test_registro_ripresa():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "reg.csv")
    r = Registro(p)
    r.scrivi({"FEN": "f1", "Stato": "Nugget", "W1": 0.5, "D1": 0.5, "L1": 0, "W2": 0.49, "D2": 0.51, "L2": 0})
    r.scrivi({"FEN": "f2", "Stato": "Non nugget"})
    r.scrivi({"FEN": "f3", "Stato": "Errore"})          # da rianalizzare
    r.chiudi()
    # simuliamo un'interruzione a meta' riga
    with open(p, "a", encoding="utf-8") as f:
        f.write("f4,Nug")
    r2 = Registro(p)
    assert set(r2.fatte) == {"f1", "f2"}, r2.fatte.keys()
    assert r2.righe_scartate == 2
    assert r2.gia_analizzata("f3") is None and r2.gia_analizzata("f1")["Stato"] == "Nugget"
    w = wdl_da_riga(r2.gia_analizzata("f1"))
    assert w == ((0.5, 0.5, 0.0), (0.49, 0.51, 0.0))
    # nuova scrittura dopo la riga troncata: deve finire su una riga nuova
    r2.scrivi({"FEN": "f5", "Stato": "Non nugget"})
    r2.chiudi()
    r3 = Registro(p)
    assert "f5" in r3.fatte and "f1" in r3.fatte
    r3.chiudi()

if __name__ == "__main__":
    test_classifica(); test_registro_ripresa(); print("tutti i test superati")
