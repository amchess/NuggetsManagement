import asyncio
import chess
import chess.engine
from state_manager import StateManager
import qualimetria

async def run_worker(worker_id: int, queue: asyncio.Queue, state: StateManager, config: dict):
    """
    Worker asincrono: gestisce un'istanza di Stockfish/ShashChess.
    Preleva posizioni dalla coda, controlla la cache e, se necessario, analizza.
    """
    engine_path = config["engine_path"]
    analysis_time = config["analysis_time"]
    wdl_tolerance = config["wdl_tolerance"]
    
    # Calcolo dei target dinamici in base alla tolleranza specificata (es. 0.03 = 3%)
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
                
            # Avvolgiamo tutta la logica di analisi in un blocco try-finally
            # per garantire che task_done() venga chiamato una e una sola volta.
            try:
                board, current_date, variant_pgn = task
                fen = board.fen()
                
                # 1. VERIFICA CACHE (Operazione O(1) in RAM, non blocca l'engine)
                status = await state.register_fen(fen, current_date)
                if status is not None:
                    # HIT: La FEN era già nota. I contatori (frequenza/data) sono già stati aggiornati.
                    continue
                    
                # 2. MISS: Posizione nuova. Eseguiamo l'Analisi in MultiPV=2
                try:
                    info = await engine.analyse(
                        board, 
                        chess.engine.Limit(time=analysis_time),
                        multipv=2,
                        options=engine_options
                    )
                    
                    # Se il motore non trova almeno 2 mosse (es. c'è una sola mossa legale), scartiamo
                    if len(info) < 2:
                        await state.update_to_not_nugget(fen)
                        continue
                        
                    # Controlliamo subito se la posizione termina con un matto forzato
                    score = info[0]["score"].white()
                    if score.is_mate():
                        await state.update_to_not_nugget(fen)
                        continue

                    # Assicuriamoci che l'engine abbia fornito il dato WDL per entrambe le linee
                    if "wdl" in info[0] and "wdl" in info[1]:
                        # Estrazione diretta dell'Expected Score (Win + Draw/2) calcolato dalla NNUE
                        win_prob_1 = info[0]["wdl"].white().expectation()
                        win_prob_2 = info[1]["wdl"].white().expectation()
                        
                        # Calcolo del Delta Win Probability
                        delta_win_prob = abs(win_prob_1 - win_prob_2)
                        
                        # Verifiche logiche in base alla tolleranza (es. +/- 0.03)
                        is_white_nugget = target_high_min <= win_prob_1 <= target_high_max
                        is_black_nugget = target_low_min <= win_prob_1 <= target_low_max
                        
                        # Il Delta non deve superare la tolleranza!
                        is_delta_valid = delta_win_prob <= wdl_tolerance
                        
                        if (is_white_nugget or is_black_nugget) and is_delta_valid:
                            # 3. È UNA PEPITA! Estraiamo le altre metriche per il salvataggio
                            fase = qualimetria.get_game_phase(board)
                            centro = qualimetria.analyze_center_type(board)
                            tensione = qualimetria.get_tension(board)
                            imbalance = qualimetria.get_material_imbalance(board)
                            
                            metrics = {
                                "win_probability": round(win_prob_1, 3),
                                "delta_win_probability": round(delta_win_prob, 3),
                                "fase": fase,
                                "centro": centro,
                                "tensione": tensione,
                                "material_imbalance": imbalance
                            }
                            
                            # 3.3 Salvataggio Globale
                            await state.update_to_nugget(fen, metrics, variant_pgn)
                            print(f"[WORKER {worker_id}] ✨ PEPITA TROVATA! WDL1: {win_prob_1:.3f} | Delta WDL: {delta_win_prob:.3f}")
                        else:
                            # Scartata dai filtri WDL
                            await state.update_to_not_nugget(fen)
                    else:
                        # Niente output WDL (caso anomalo)
                        await state.update_to_not_nugget(fen)

                except chess.engine.EngineTerminatedError:
                    print(f"[WORKER {worker_id}] ⚠️ Crash del motore (EngineTerminatedError).")
                    await state.update_to_not_nugget(fen)
                    
                except Exception as e:
                    print(f"[WORKER {worker_id}] ⚠️ Errore generico durante l'analisi: {e}")
                    await state.update_to_not_nugget(fen)
                    
            finally:
                # Segnala alla coda che questo specifico task è concluso.
                # Chiamato esattamente una volta per ogni elemento scaricato dalla coda.
                queue.task_done()
                
    finally:
        # Quando il while loop si rompe (segnale None), chiudiamo il motore pulitamente
        await engine.quit()
        print(f"[WORKER {worker_id}] Spegnimento completato.")