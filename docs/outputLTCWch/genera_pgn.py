"""
Selezione delle Top-N pepite da nuggets.csv e scrittura di:
  - nuggets_top100.pgn  (linea completa fino alla pepita, nessun troncamento)
  - nuggets_top100.epd  (posizione finale: libro di aperture per i tornei)
  - nuggets_top100.csv  (le righe scelte, per i diagrammi della selezione)

Regola (dichiarata e riproducibile):
  1. |Pwin - bersaglio| <= --pwin-tol  (bersaglio 0.75 oppure 0.25)
  2. Delta WDL <= --delta-tol
  3. se il CSV contiene le colonne W1/L1: L1 <= --opposite-max per le pepite a 0.75,
     W1 <= --opposite-max per quelle a 0.25
  4. ordinamento per Delta WDL crescente, poi per distanza di Pwin dal bersaglio
  5. una sola pepita per linea di partita: si scarta una posizione se la sua linea
     e' il prefisso (per mosse intere) di una gia' scelta, o viceversa

Uso:  python genera_pgn.py [--csv nuggets.csv] [--n 100]
"""
import argparse
import re
import pandas as pd


def get_args():
    p = argparse.ArgumentParser(description="Selezione Top-N pepite")
    p.add_argument("--csv", default="nuggets.csv")
    p.add_argument("--n", type=int, default=100)
    p.add_argument("--pwin-tol", type=float, default=0.03)
    p.add_argument("--delta-tol", type=float, default=0.03)
    p.add_argument("--opposite-max", type=float, default=0.0)
    p.add_argument("--out", default="nuggets_top100")
    return p.parse_args()


def moves(variant: str) -> tuple:
    """Lista di mosse senza numeri di mossa: confronto per mosse intere, non per caratteri."""
    return tuple(t for t in re.sub(r"\d+\.", " ", str(variant)).split())


def related(a: tuple, b: tuple) -> bool:
    """True se una linea e' il prefisso dell'altra (stessa partita o stessa variante)."""
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def main():
    args = get_args()
    df = pd.read_csv(args.csv).drop_duplicates(subset=["FEN"]).copy()
    df = df.rename(columns={"WIN_PROBABILITY": "Pwin", "Delta_Win_Probability": "Delta"})
    for col in ("Pwin", "Delta"):
        if col not in df.columns:
            raise SystemExit(f"[ERRORE] Colonna mancante nel CSV: {col}")
    print(f"[*] Pepite candidate nel CSV: {len(df)}")

    df["Target"] = df["Pwin"].apply(lambda p: 0.75 if p >= 0.5 else 0.25)
    df["Dist"] = (df["Pwin"] - df["Target"]).abs().round(3)

    df = df[(df["Dist"] <= args.pwin_tol + 1e-9) & (df["Delta"] <= args.delta_tol + 1e-9)]
    print(f"[*] Dopo le tolleranze (Pwin ±{args.pwin_tol}, Delta ≤ {args.delta_tol}): {len(df)}")

    if {"W1", "L1"}.issubset(df.columns):
        ok_high = (df["Target"] == 0.75) & (df["L1"] <= args.opposite_max + 1e-9)
        ok_low = (df["Target"] == 0.25) & (df["W1"] <= args.opposite_max + 1e-9)
        df = df[ok_high | ok_low]
        print(f"[*] Dopo la condizione L=0 / W=0 (max {args.opposite_max}): {len(df)}")
    else:
        print("[!] Colonne W1/L1 assenti: condizione L=0 / W=0 NON verificata (CSV di vecchio formato).")

    df = df.sort_values(by=["Delta", "Dist", "FEN"], kind="mergesort")

    selection, chosen_lines = [], []
    for _, row in df.iterrows():
        line = moves(row["Variante_PGN"])
        if any(related(line, c) for c in chosen_lines):
            continue
        selection.append(row)
        chosen_lines.append(line)
        if len(selection) >= args.n:
            break

    print(f"[*] Pepite selezionate (una per linea): {len(selection)}")
    if len(selection) < args.n:
        print(f"[!] Meno di {args.n} pepite soddisfano la regola: allargare le tolleranze o il database.")

    with open(args.out + ".pgn", "w", encoding="utf-8") as fp, \
         open(args.out + ".epd", "w", encoding="utf-8") as fe:
        for i, row in enumerate(selection, 1):
            date = str(row["Data_Recente"])
            if date.startswith("1900") or date == "nan":
                date = "????.??.??"          # data ignota: mai una data fittizia
            fp.write('[Event "Nuggets Top-N"]\n[Site "NuggetsManagement"]\n')
            fp.write(f'[Date "{date}"]\n[Round "{i}"]\n[White "?"]\n[Black "?"]\n[Result "*"]\n')
            fp.write(f'[NuggetFEN "{row["FEN"]}"]\n')
            fp.write(f'[Pwin "{row["Pwin"]:.3f}"]\n[DeltaWDL "{row["Delta"]:.3f}"]\n')
            if {"W1", "D1", "L1"}.issubset(row.index):
                fp.write(f'[WDL "{row["W1"]:.3f} {row["D1"]:.3f} {row["L1"]:.3f}"]\n')
            fp.write(f'[Phase "{row["Fase"]}"]\n[Centre "{row["Centro"]}"]\n\n')
            fp.write(f'{str(row["Variante_PGN"]).strip()} *\n\n')
            epd = " ".join(str(row["FEN"]).split()[:4])
            fe.write(f'{epd} id "nugget{i:03d}"; c0 "Pwin={row["Pwin"]:.3f} DeltaWDL={row["Delta"]:.3f}";\n')

    # CSV della selezione: serve a generaDiagrammi.py --csv <out>.csv --label Top100
    pd.DataFrame(selection).rename(
        columns={"Pwin": "WIN_PROBABILITY", "Delta": "Delta_Win_Probability"}
    ).drop(columns=["Target", "Dist"]).to_csv(args.out + ".csv", index=False)

    print(f"[OK] Scritti {args.out}.pgn, {args.out}.epd e {args.out}.csv")


if __name__ == "__main__":
    main()
