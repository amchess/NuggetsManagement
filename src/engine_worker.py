import asyncio
import chess
import chess.engine
from state_manager import StateManager
import qualimetria
from qualimetria import GamePhase
from registro import classifica, frazioni_wdl, wdl_da_riga


def _limite(config: dict) -> chess.engine.Limit:
    """Limite di analisi: a nodi se 'analysis_nodes' e' impostato (consigliato per Lc0), altrimenti a tempo."""
    nodi = config.get("analysis_nodes")
    if nodi:
        return chess.engine.Limit(nodes=int(nodi))
    return chess.engine.Limit(time=config["analysis_time"])


async def _avvia_motore(worker_id: int, config: dict):
    """
    Avvia e configura il motore. Le opzioni non dichiarate dal motore vengono saltate con un
    avviso, cosi' lo stesso codice funziona con Stockfish, ShashChess e Lc0 (che non ha 'Hash').
    """
    transport, engine = await chess.engine.popen_uci(config["engine_path"])
    desiderate = {
        "Threads": config.get("threads", 1),
        "Hash": config.get("hash", 64),
        "UCI_ShowWDL": True,
    }
    if config.get("syzygy_path"):
        desiderate["SyzygyPath"] = config["syzygy_path"]
    # Opzioni aggiuntive o specifiche del motore (es. WeightsFile, Backend per Lc0)
    desiderate.update(config.get("engine_options", {}))

    engine_options = {}
    for nome, valore in desiderate.items():
        if nome in engine.options:
            engine_options[nome] = valore
        elif worker_id == 0:
            print(f"[WORKER {worker_id}] Opzione '{nome}' non supportata dal motore: ignorata.")
    await engine.configure(engine_options)
    nome_motore = engine.id.get("name", str(config["engine_path"]))
    return engine, engine_options, nome_motore


def _cp(score_white) -> str:
    """Valutazione dal punto di vista del Bianco: centipawn, oppure 'M<n>' per il matto."""
    if score_white.is_mate():
        return f"M{score_white.mate()}"
    return str(score_white.score())


async def _ripristina(state: StateManager, fen: str, riga: dict, variant_pgn: str, criteri: dict):
    """
    Ripresa dopo un'interruzione: la posizione era gia' nel registro. Si riapplicano
    le soglie correnti ai valori W/D/L salvati, senza rianalizzare.
    """
    wdl = wdl_da_riga(riga)
    esito = classifica(wdl[0], wdl[1], **criteri) if wdl else None
    if esito and esito["pepita"] and not str(riga.get("CP1", "")).startswith("M"):
        metrics = {
            "win_probability": round(esito["pwin1"], 3),
            "delta_win_probability": round(esito["delta"], 3),
            "wdl_1": tuple(round(x, 3) for x in wdl[0]),
            "wdl_2": tuple(round(x, 3) for x in wdl[1]),
            "fase": GamePhase(riga["Fase"]) if riga.get("Fase") else None,
            "centro": riga.get("Centro"),
            "tensione": int(float(riga["Tensione"])) if riga.get("Tensione") else None,
            "material_imbalance": float(riga["Imbalance"]) if riga.get("Imbalance") else None,
        }
        await state.update_to_nugget(fen, metrics, riga.get("Variante_PGN") or variant_pgn)
    else:
        await state.update_to_not_nugget(fen)


async def run_worker(worker_id: int, queue: asyncio.Queue, state: StateManager, config: dict, registro=None):
    """
    Worker asincrono: gestisce un'istanza di Stockfish/ShashChess (o Lc0).
    Preleva posizioni dalla coda, controlla la cache e, se necessario, analizza.
    Ogni posizione analizzata, pepita o no, viene scritta subito nel registro (se attivo).
    """
    wdl_tolerance = config["wdl_tolerance"]
    criteri = {
        "wdl_tolerance": wdl_tolerance,
        # Soglia del Delta WDL: se assente coincide con la tolleranza su Pwin (comportamento originale)
        "delta_max": config.get("delta_max", wdl_tolerance),
        # Quota massima ammessa per il terzo esito: L per le pepite a 0.75, W per quelle a 0.25.
        # 0.0 = definizione stretta (Pwin=75% con L=0, oppure Pwin=25% con W=0).
        "opposite_max": config.get("opposite_max", 0.0),
    }
    limite = _limite(config)
    # Con True ogni posizione e' analizzata a tabella hash vuota (ucinewgame): analisi indipendenti
    nuova_partita = config.get("nuova_partita_per_posizione", True)

    engine = None
    try:
        engine, engine_options, nome_motore = await _avvia_motore(worker_id, config)
        print(f"[WORKER {worker_id}] Motore UCI avviato e configurato ({nome_motore}).")

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

                # 1b. RIPRESA: posizione analizzata in un'esecuzione precedente (registro su disco)
                if registro is not None:
                    salvata = registro.gia_analizzata(fen)
                    if salvata is not None:
                        await _ripristina(state, fen, salvata, variant_pgn, criteri)
                        continue

                riga = {
                    "FEN": fen,
                    "Tratto": "w" if board.turn == chess.WHITE else "b",
                    "Semimossa": board.ply(),
                    "Data": current_date,
                    "Variante_PGN": variant_pgn,
                    "Motore": nome_motore,
                }

                # 2. MISS: Posizione nuova. Eseguiamo l'Analisi in MultiPV=2
                try:
                    info = await engine.analyse(
                        board,
                        limite,
                        multipv=2,
                        game=(fen if nuova_partita else None),
                        options=engine_options
                    )

                    # Qualimetria calcolata per tutte le posizioni (costo trascurabile):
                    # serve per i tassi di riferimento delle strutture e delle fasi.
                    fase = qualimetria.get_game_phase(board)
                    centro = qualimetria.analyze_center_type(board)
                    tensione = qualimetria.get_tension(board)
                    imbalance = qualimetria.get_material_imbalance(board)
                    riga.update({"Fase": fase.value, "Centro": centro, "Tensione": tensione, "Imbalance": imbalance})

                    # Se il motore non trova almeno 2 mosse (es. c'è una sola mossa legale), scartiamo
                    if len(info) < 2:
                        riga["Stato"] = "Scartata"
                        await state.update_to_not_nugget(fen)
                        continue

                    # Dati di ricerca delle due linee (per la Tabella 2 e lo studio del rumore)
                    pv1, pv2 = info[0].get("pv") or [], info[1].get("pv") or []
                    riga.update({
                        "CP1": _cp(info[0]["score"].white()),
                        "CP2": _cp(info[1]["score"].white()),
                        "Mossa1": board.san(pv1[0]) if pv1 else "",
                        "Mossa2": board.san(pv2[0]) if pv2 else "",
                        "Profondita1": info[0].get("depth", ""),
                        "Profondita2": info[1].get("depth", ""),
                        "SelDepth": info[0].get("seldepth", ""),
                        "Nodi": info[0].get("nodes", ""),
                        "NPS": info[0].get("nps", ""),
                        "Tempo": info[0].get("time", ""),
                        "TBHits": info[0].get("tbhits", ""),
                    })

                    # Controlliamo subito se la posizione termina con un matto forzato
                    if info[0]["score"].white().is_mate():
                        riga["Stato"] = "Non nugget"
                        await state.update_to_not_nugget(fen)
                        continue

                    # Assicuriamoci che l'engine abbia fornito il dato WDL per entrambe le linee
                    if "wdl" in info[0] and "wdl" in info[1]:
                        # Terne (W, D, L) delle due linee, dal punto di vista del Bianco, come frazioni
                        wdl_1 = info[0]["wdl"].white()
                        wdl_2 = info[1]["wdl"].white()
                        w1, d1, l1 = frazioni_wdl(wdl_1.wins, wdl_1.draws, wdl_1.losses)
                        w2, d2, l2 = frazioni_wdl(wdl_2.wins, wdl_2.draws, wdl_2.losses)
                        esito = classifica((w1, d1, l1), (w2, d2, l2), **criteri)
                        riga.update({
                            "W1": round(w1, 3), "D1": round(d1, 3), "L1": round(l1, 3),
                            "W2": round(w2, 3), "D2": round(d2, 3), "L2": round(l2, 3),
                            "Pwin1": round(esito["pwin1"], 4), "Pwin2": round(esito["pwin2"], 4),
                            "Delta": round(esito["delta"], 4),
                        })

                        if esito["pepita"]:
                            # 3. È UNA PEPITA! Salviamo le metriche
                            metrics = {
                                "win_probability": round(esito["pwin1"], 3),
                                "delta_win_probability": round(esito["delta"], 3),
                                "wdl_1": (round(w1, 3), round(d1, 3), round(l1, 3)),
                                "wdl_2": (round(w2, 3), round(d2, 3), round(l2, 3)),
                                "fase": fase,
                                "centro": centro,
                                "tensione": tensione,
                                "material_imbalance": imbalance
                            }

                            # 3.3 Salvataggio Globale
                            await state.update_to_nugget(fen, metrics, variant_pgn)
                            riga["Stato"] = "Nugget"
                            print(f"[WORKER {worker_id}] ✨ PEPITA TROVATA! WDL1: {esito['pwin1']:.3f} | Delta WDL: {esito['delta']:.3f}")
                        else:
                            # Scartata dai filtri WDL
                            riga["Stato"] = "Non nugget"
                            await state.update_to_not_nugget(fen)
                    else:
                        # Niente output WDL (caso anomalo)
                        riga["Stato"] = "Non nugget"
                        await state.update_to_not_nugget(fen)

                except chess.engine.EngineTerminatedError:
                    # Il motore e' morto: lo riavviamo, altrimenti tutte le posizioni successive
                    # di questo worker verrebbero scartate. La posizione resta "Errore" e alla
                    # prossima esecuzione verra' rianalizzata.
                    print(f"[WORKER {worker_id}] ⚠️ Crash del motore (EngineTerminatedError): riavvio.")
                    riga["Stato"] = "Errore"
                    await state.update_to_not_nugget(fen)
                    try:
                        engine, engine_options, nome_motore = await _avvia_motore(worker_id, config)
                    except Exception as e:
                        print(f"[WORKER {worker_id}] ⚠️ Riavvio del motore fallito: {e}")
                        raise

                except Exception as e:
                    print(f"[WORKER {worker_id}] ⚠️ Errore generico durante l'analisi: {e}")
                    riga["Stato"] = "Errore"
                    await state.update_to_not_nugget(fen)

                finally:
                    if registro is not None and "Stato" in riga:
                        registro.scrivi(riga)

            finally:
                # Segnala alla coda che questo specifico task è concluso.
                # Chiamato esattamente una volta per ogni elemento scaricato dalla coda.
                queue.task_done()

    finally:
        # Quando il while loop si rompe (segnale None), chiudiamo il motore pulitamente
        if engine is not None:
            try:
                await engine.quit()
            except Exception:
                pass
        print(f"[WORKER {worker_id}] Spegnimento completato.")
