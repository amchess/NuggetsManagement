import asyncio
import csv
import chess
import chess.pgn

def build_variant_string(san_moves: list) -> str:
    """
    Costruisce una stringa PGN leggibile (es. '1. e4 e5 2. Nf3') a partire
    da una lista di mosse in notazione algebrica standard (SAN).
    È molto più veloce che ricostruire l'intero albero PGN per ogni mossa.
    """
    result = []
    for i, move in enumerate(san_moves):
        if i % 2 == 0:
            result.append(f"{(i // 2) + 1}. {move}")
        else:
            result.append(move)
    return " ".join(result)


def _formato(path: str) -> str:
    p = path.lower()
    if p.endswith(".epd"):
        return "epd"
    if p.endswith(".csv"):
        return "csv"
    return "pgn"


def iter_positions(path: str, solo_finale: bool = False):
    """
    Generatore sincrono delle posizioni da analizzare: (board, data, variante).
      - .pgn : tutte le posizioni della linea principale (dopo ogni mossa); con
               solo_finale=True soltanto la posizione finale di ogni partita/linea
               (utile per i file di aperture come Test2026.pgn);
      - .epd : una posizione per riga (opcode 'id' come variante, se presente);
      - .csv : colonna FEN (FEN completa); colonna Variante_PGN se presente
               (es. il registro di un'estrazione precedente, per la rianalisi con Lc0).
    """
    fmt = _formato(path)
    if fmt == "epd":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for riga in f:
                riga = riga.strip()
                if not riga or riga.startswith("#"):
                    continue
                board, ops = chess.Board.from_epd(riga)
                yield board, "1900.01.01", str(ops.get("id", ""))
        return
    if fmt == "csv":
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("FEN"):
                    yield chess.Board(r["FEN"]), r.get("Data") or r.get("Data_Recente") or "1900.01.01", r.get("Variante_PGN", "")
        return
    # Usiamo errors='ignore' perché i vecchi DB PGN hanno spesso caratteri invalidi negli header
    with open(path, "r", encoding="utf-8", errors="ignore") as pgn_file:
        while True:
            # Legge una singola partita dal file
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break  # Fine del file raggiunta

            # Estrae la data. Formato standard PGN: YYYY.MM.DD
            game_date = game.headers.get("Date", "1900.01.01")
            if "?" in game_date:  # Gestisce date sconosciute (es. "????.??.??")
                game_date = "1900.01.01"

            board = game.board()
            san_moves = []

            # Scorre tutte le mosse della linea principale
            for move in game.mainline_moves():
                # Salviamo la notazione SAN prima di muovere per costruire la variante
                san_moves.append(board.san(move))
                board.push(move)
                if not solo_finale:
                    yield board.copy(), game_date, build_variant_string(san_moves)
            if solo_finale and san_moves:
                yield board.copy(), game_date, build_variant_string(san_moves)


async def produce_tasks(pgn_path: str, queue: asyncio.Queue, solo_finale: bool = False):
    """
    Legge il file in streaming. Estrae le posizioni, la data e la variante,
    e le inserisce nella coda per i worker.
    """
    print(f"[PRODUCER] Inizio lettura del file: {pgn_path}")
    n = 0
    for task_payload in iter_positions(pgn_path, solo_finale):
        # .put() è bloccante (in modo asincrono). Se la coda ha raggiunto la sua maxsize,
        # il producer si ferma qui e attende che i worker la svuotino, salvando la RAM.
        await queue.put(task_payload)
        n += 1
        # Cede brevemente il controllo all'event loop per non "soffocare" i worker
        if n % 200 == 0:
            await asyncio.sleep(0)
        # Un piccolo feedback visivo ogni 10000 posizioni lette
        if n % 10000 == 0:
            print(f"[PRODUCER] Lette {n} posizioni...")

    print(f"[PRODUCER] Lettura completata! Totale posizioni: {n}")


def count_positions(pgn_path: str, solo_finale: bool = False):
    """Conta le posizioni e le FEN distinte (stessa chiave usata dalla cache), senza analizzarle."""
    totale, distinte = 0, set()
    for board, _, _ in iter_positions(pgn_path, solo_finale):
        totale += 1
        distinte.add(board.fen())
    return totale, len(distinte)
