import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from state_manager import StateManager
from pgn_producer import produce_tasks, count_positions
from engine_worker import run_worker
from registro import Registro
import exporter

def load_config(config_path="config.json") -> dict:
    """Carica il file di configurazione JSON."""
    if not os.path.exists(config_path):
        print(f"[ERRORE] File di configurazione '{config_path}' non trovato.")
        sys.exit(1)
    with open(config_path, "r") as f:
        return json.load(f)

def get_args():
    p = argparse.ArgumentParser(description="NuggetsManagement - Miner di Pepite WDL")
    p.add_argument("--config", default="config.json", help="file di configurazione (default: config.json)")
    p.add_argument("--conta", action="store_true",
                   help="conta soltanto le posizioni da analizzare e stima la durata, senza avviare i motori")
    p.add_argument("--output-dir", default=None,
                   help="cartella di output (sostituisce output_dir del config; utile per le analisi ripetute)")
    return p.parse_args()

async def main():
    args = get_args()
    print("==================================================")
    print("   NuggetsManagement - Miner di Pepite WDL        ")
    print("==================================================")

    # 1. Caricamento configurazioni e setup cartelle
    config = load_config(args.config)
    if args.output_dir:
        config["output_dir"] = args.output_dir
    solo_finale = config.get("solo_posizione_finale", False)
    concurrency = config.get("concurrency", 4)

    if args.conta:
        totale, distinte = count_positions(config["pgn_path"], solo_finale)
        print(f"[*] Posizioni lette: {totale}; FEN distinte da analizzare: {distinte}")
        if config.get("analysis_nodes"):
            print(f"[*] Limite a nodi ({config['analysis_nodes']}): misurare i nodi al secondo per stimare la durata.")
        else:
            ore = distinte * config["analysis_time"] / concurrency / 3600
            print(f"[*] Stima: {distinte} x {config['analysis_time']} s / {concurrency} istanze = {ore:.1f} ore")
        return

    os.makedirs(config["output_dir"], exist_ok=True)

    # Registro incrementale di tutte le posizioni (ripresa automatica dopo un'interruzione)
    registro = None
    if config.get("registro", True):
        registro_path = os.path.join(config["output_dir"], config.get("registro_csv", "tutte_le_posizioni.csv"))
        registro = Registro(registro_path)
        print(f"[*] Registro: {registro_path} ({len(registro)} posizioni gia' analizzate"
              + (f", {registro.righe_scartate} righe incomplete ignorate" if registro.righe_scartate else "") + ")")

    # Metadati dell'esecuzione: servono per la Tabella 2 del paper
    meta_path = os.path.join(config["output_dir"], "metadati_esecuzione.json")
    meta = {"avvio": datetime.now().isoformat(timespec="seconds"), "config": config,
            "host": os.uname().nodename if hasattr(os, "uname") else ""}

    # 2. Inizializzazione Stato e Coda
    state = StateManager()
    # Una coda di 1000 elementi è perfetta. Evita che il Producer legga
    # milioni di posizioni riempiendo la RAM prima che i Worker le analizzino.
    queue = asyncio.Queue(maxsize=1000)

    print(f"[*] Concorrenza: {concurrency} motori paralleli x {config.get('threads', 1)} thread.")
    if config.get("analysis_nodes"):
        print(f"[*] Limite per analisi: {config['analysis_nodes']} nodi.")
    else:
        print(f"[*] Tempo per analisi: {config['analysis_time']} sec.")

    start_time = time.time()

    # 3. Avvio dei Worker (Consumatori)
    workers = []
    for i in range(concurrency):
        task = asyncio.create_task(run_worker(i, queue, state, config, registro))
        workers.append(task)

    # 4. Avvio del Producer
    try:
        # Aspettiamo che il producer finisca di leggere tutto il file
        await produce_tasks(config["pgn_path"], queue, solo_finale)

        print("[*] Producer terminato. Attesa svuotamento della coda...")
        # Aspettiamo che i worker processino tutto quello che è rimasto in coda
        await queue.join()

    except KeyboardInterrupt:
        print("\n[!] Interruzione manuale (CTRL+C) rilevata. Spegnimento grazioso in corso...")

    finally:
        # 5. Spegnimento Grazioso dei Worker (Poison Pill)
        print("[*] Invio segnale di spegnimento ai motori...")
        for _ in range(concurrency):
            await queue.put(None)

        # return_exceptions=True: se un worker e' caduto, l'export avviene comunque
        esiti = await asyncio.gather(*workers, return_exceptions=True)
        for i, e in enumerate(esiti):
            if isinstance(e, BaseException):
                print(f"[!] Il worker {i} si e' interrotto con errore: {e!r}")
        if registro is not None:
            registro.chiudi()

        # 6. Esportazione Finale
        print("\n==================================================")
        print("   Analisi Completata. Generazione Output...      ")
        print("==================================================")

        all_nuggets = state.get_all_nuggets()

        jsonl_path = os.path.join(config["output_dir"], "nuggets.jsonl")
        csv_path = os.path.join(config["output_dir"], "nuggets.csv")
        html_path = os.path.join(config["output_dir"], "dashboard.html")

        exporter.export_jsonl(all_nuggets, jsonl_path)
        exporter.export_csv(all_nuggets, csv_path)
        exporter.export_html_summary(all_nuggets, html_path)

        elapsed = time.time() - start_time
        meta.update({"fine": datetime.now().isoformat(timespec="seconds"),
                     "durata_secondi": round(elapsed, 1), "pepite": len(all_nuggets)})
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print(f"\n[FINE] Trovate {len(all_nuggets)} pepite uniche.")
        print(f"[FINE] Tempo totale: {elapsed:.2f} secondi.")

if __name__ == "__main__":
    # Su Windows, per evitare errori con asyncio e subprocessi
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass # Già gestito internamente
