import asyncio
import chess
import chess.engine
from chess.svg import board
from state_manager import StateManager
import qualimetria

async def run_worker(worker_id: int, queue: asyncio.Queue, state: StateManager, config: dict):
    """
    Worker asincrono: gestisce un'istanza di Stockfish.
    Preleva posizioni dalla coda, controlla la cache e, se necessario, analizza.
    """
    engine_path = config["engine_path"]
    analysis_time = config["analysis_time"]
    wdl_tolerance = config["wdl_tolerance"]
    
    # Calcolo dei target dinamici in base alla tolleranza specificata (es. 0.06 = 6%)
    target_high_min = 0.75 - wdl_tolerance
    target_high_max = 0.75 + wdl_tolerance
    target_low_min = 0.25 - wdl_tolerance
    target_low_max = 0.25 + wdl_tolerance

    try:
        # Avvia il processo del motore in background (comunicazione via pipe stdin/stdout)
        transport, engine = await chess.engine.popen_uci(engine_path)
        
        # Configurazione opzioni UCI
        engine_options = {
            "Threads": config.get("threads", 1),
            "Hash": config.get("hash", 64),
            "UCI_ShowWDL": True
        }
        if config.get("syzygy_path"):
            engine_options["SyzygyPath"] = config["syzygy_path"]
            
        await engine.configure(engine_options)
        print(f"[WORKER {worker_id}] Motore UCI avviato e configurato.")
        
        while True:
            # Preleva un task (o si sospende se la coda è vuota)
            task = await queue.get()
            
            # Segnale di terminazione (veleno) per fermare il worker
            if task is None:
                queue.task_done()
                break
                
            board, current_date, variant_pgn = task
            fen = board.fen()
            
            # 1. VERIFICA CACHE (Operazione O(1) in RAM, non blocca l'engine)
            # NOTA: Ho mantenuto il tuo metodo 'register_fen' o 'check_or_add_fen' a seconda di come l'hai chiamato in state_manager
            status = await state.register_fen(fen, current_date)
            if status is not None:
                # HIT: La FEN era già nota. I contatori (frequenza/data) sono già stati aggiornati.
                # Non sprechiamo secondi di CPU e passiamo alla prossima mossa!
                queue.task_done()
                continue
                
            # 2. MISS: Posizione nuova. Eseguiamo l'Analisi Primaria (Filtro WDL)
            try:
                info = await engine.analyse(
                    board, 
                    chess.engine.Limit(time=analysis_time)
                )
                
                # ---> LA CORREZIONE È QUI <---
                # Controlliamo subito se la posizione termina con un matto forzato
                score = info["score"].white()
                if score.is_mate():
                    await state.update_to_not_nugget(fen)
                    queue.task_done()
                    continue
                # ---> FINE CORREZIONE <---

                is_nugget = False
                wdl_exp = None
                
                # Assicuriamoci che l'engine abbia fornito il dato WDL
                if "wdl" in info:
                    wdl_exp = info["wdl"].white().expectation()
                    
                    is_high = target_high_min <= wdl_exp <= target_high_max
                    is_low = target_low_min <= wdl_exp <= target_low_max
                    
                    if is_high or is_low:
                        is_nugget = True
                        
                if not is_nugget:
                    # Non è una pepita, la scartiamo
                    await state.update_to_not_nugget(fen)
                else:
                    # 3. È UNA PEPITA! Avviamo l'analisi di Qualimetria
                    
                    # 3.1 Delta MultiPV (Cerchiamo 2 linee con un tempo ridotto o lo stesso tempo)
                    multipv_info = await engine.analyse(
                        board,
                        chess.engine.Limit(time=min(5.0, analysis_time)), # Limito la 2° analisi a max 5 secondi per risparmiare tempo
                        multipv=2
                    )
                    
                    delta_cp = 0.0
                    # Controlla che ci siano almeno due mosse legali giocabili
                    if len(multipv_info) >= 2:
                        # score() restituisce i centipawn interi (mate_score gestisce le posizioni di matto forzato)
                        score1 = multipv_info[0]["score"].pov(board.turn).score(mate_score=10000)
                        score2 = multipv_info[1]["score"].pov(board.turn).score(mate_score=10000)
                        
                        if score1 is not None and score2 is not None:
                            delta_cp = float(abs(score1 - score2))

                    # 3.2 Altre Euristiche Matematiche Sincrone
                    fase = qualimetria.get_game_phase(board)
                    centro = qualimetria.analyze_center_type(board)
                    tensione = qualimetria.get_tension(board)
                    imbalance = qualimetria.get_material_imbalance(board)
                    
                    metrics = {
                        "wdl_expectation": round(wdl_exp, 3),
                        "delta_multipv": delta_cp,
                        "fase": fase,
                        "centro": centro,
                        "tensione": tensione,
                        "material_imbalance": imbalance
                    }
                    
                    # 3.3 Salvataggio Globale
                    await state.update_to_nugget(fen, metrics, variant_pgn)
                    print(f"[WORKER {worker_id}] ✨ PEPITA TROVATA! WDL: {wdl_exp:.2f} | Fase: {fase.value} | Delta CP: {delta_cp}")

            except chess.engine.EngineTerminatedError:
                print(f"[WORKER {worker_id}] ⚠️ Crash del motore (EngineTerminatedError).")
                await state.update_to_not_nugget(fen)
                
            except Exception as e:
                print(f"[WORKER {worker_id}] ⚠️ Errore generico durante l'analisi: {e}")
                await state.update_to_not_nugget(fen)
                
            finally:
                # Segnala alla coda che questo specifico task è concluso, qualunque sia l'esito
                queue.task_done()
                
    finally:
        # Quando il while loop si rompe (segnale None), chiudiamo Stockfish pulitamente
        await engine.quit()
        print(f"[WORKER {worker_id}] Spegnimento completato.")