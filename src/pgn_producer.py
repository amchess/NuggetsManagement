import asyncio
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

async def produce_tasks(pgn_path: str, queue: asyncio.Queue):
    """
    Legge il file PGN in streaming. Estrae le posizioni, la data e la variante,
    e le inserisce nella coda per i worker.
    """
    print(f"[PRODUCER] Inizio lettura del file: {pgn_path}")
    
    # Usiamo errors='ignore' perché i vecchi DB PGN hanno spesso caratteri invalidi negli header
    with open(pgn_path, "r", encoding="utf-8", errors="ignore") as pgn_file:
        games_processed = 0
        
        while True:
            # Legge una singola partita dal file
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break  # Fine del file raggiunta
            
            games_processed += 1
            
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
                
                board_copy = board.copy()
                variant_str = build_variant_string(san_moves)
                
                # Crea il pacchetto dati
                task_payload = (board_copy, game_date, variant_str)
                
                # .put() è bloccante (in modo asincrono). Se la coda ha raggiunto la sua maxsize,
                # il producer si ferma qui e attende che i worker la svuotino, salvando la RAM.
                await queue.put(task_payload)
            
            # Cede brevemente il controllo all'event loop per non "soffocare" i worker
            # durante il parsing massivo
            await asyncio.sleep(0)
            
            # Un piccolo feedback visivo ogni 1000 partite lette
            if games_processed % 1000 == 0:
                print(f"[PRODUCER] Lette {games_processed} partite dal PGN...")

    print(f"[PRODUCER] Lettura completata! Totale partite: {games_processed}")