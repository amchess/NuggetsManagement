import asyncio
import json
import os
import sys
import time
from state_manager import StateManager
from pgn_producer import produce_tasks
from engine_worker import run_worker
import exporter

def load_config(config_path="config.json") -> dict:
    """Carica il file di configurazione JSON."""
    if not os.path.exists(config_path):
        print(f"[ERRORE] File di configurazione '{config_path}' non trovato.")
        sys.exit(1)
    with open(config_path, "r") as f:
        return json.load(f)

async def main():
    print("==================================================")
    print("   NuggetsManagement - Miner di Pepite WDL        ")
    print("==================================================")
    
    # 1. Caricamento configurazioni e setup cartelle
    config = load_config()
    os.makedirs(config["output_dir"], exist_ok=True)
    
    # 2. Inizializzazione Stato e Coda
    state = StateManager()
    # Una coda di 1000 elementi è perfetta. Evita che il Producer legga 
    # milioni di posizioni riempiendo la RAM prima che i Worker le analizzino.
    queue = asyncio.Queue(maxsize=1000) 
    
    concurrency = config.get("concurrency", 4)
    print(f"[*] Concorrenza: {concurrency} motori paralleli.")
    print(f"[*] Tempo per analisi: {config['analysis_time']} sec.")
    
    start_time = time.time()
    
    # 3. Avvio dei Worker (Consumatori)
    workers = []
    for i in range(concurrency):
        task = asyncio.create_task(run_worker(i, queue, state, config))
        workers.append(task)
        
    # 4. Avvio del Producer
    try:
        # Aspettiamo che il producer finisca di leggere tutto il file PGN
        await produce_tasks(config["pgn_path"], queue)
        
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
            
        await asyncio.gather(*workers)
        
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