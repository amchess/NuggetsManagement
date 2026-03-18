import json
import csv
from typing import List
from collections import Counter
from state_manager import NuggetRecord

def _record_to_dict(record: NuggetRecord) -> dict:
    """Helper per serializzare correttamente gli Enum e i tipi complessi."""
    return {
        "fen": record.fen,
        "status": record.status.value,
        "frequency": record.frequency,
        "last_seen_date": record.last_seen_date,
        "wdl_expectation": record.wdl_expectation,
        "delta_multipv": record.delta_multipv,
        "fase": record.fase.value if record.fase else None,
        "centro": record.centro,
        "tensione": record.tensione,
        "material_imbalance": record.material_imbalance,
        "variant_pgn": record.variant_pgn
    }

def export_jsonl(nuggets: List[NuggetRecord], filepath: str):
    """Esporta i dati in formato JSON Lines (un oggetto JSON per riga)."""
    print(f"[*] Esportazione JSONL in corso: {filepath}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        for n in nuggets:
            f.write(json.dumps(_record_to_dict(n)) + "\n")

def export_csv(nuggets: List[NuggetRecord], filepath: str):
    """Esporta i dati in formato CSV tabellare."""
    print(f"[*] Esportazione CSV in corso: {filepath}...")
    headers = [
        "FEN", "WDL", "Delta_CP", "Fase", "Centro", 
        "Tensione", "Imbalance", "Frequenza", "Data_Recente", "Variante_PGN"
    ]
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for n in nuggets:
            writer.writerow([
                n.fen,
                n.wdl_expectation,
                n.delta_multipv,
                n.fase.value if n.fase else "",
                n.centro,
                n.tensione,
                n.material_imbalance,
                n.frequency,
                n.last_seen_date,
                n.variant_pgn
            ])

def export_html_summary(nuggets: List[NuggetRecord], filepath: str):
    """Genera una dashboard HTML statica con le statistiche delle pepite."""
    print(f"[*] Generazione Dashboard HTML in corso: {filepath}...")
    
    if not nuggets:
        print("[!] Nessuna pepita trovata per generare il report HTML.")
        return

    # Calcolo Statistiche
    total_nuggets = len(nuggets)
    fasi_counter = Counter(n.fase.value for n in nuggets if n.fase)
    centri_counter = Counter(n.centro for n in nuggets if n.centro)
    
    # Ordiniamo le pepite per frequenza per trovare le "Top 10" più insospettabili
    top_frequent = sorted(nuggets, key=lambda x: x.frequency, reverse=True)[:10]

    # Generazione stringhe per le tabelle HTML
    fasi_html = "".join(f"<li><strong>{f}:</strong> {c} pepite</li>" for f, c in fasi_counter.most_common())
    centri_html = "".join(f"<li><strong>{c}:</strong> {count} pepite</li>" for c, count in centri_counter.most_common())
    
    top_html = ""
    for n in top_frequent:
        top_html += f"""
        <tr>
            <td style='font-family: monospace; font-size: 0.9em;'>{n.fen}</td>
            <td>{n.frequency}</td>
            <td>{n.wdl_expectation}</td>
            <td>{n.delta_multipv}</td>
            <td>{n.last_seen_date}</td>
        </tr>
        """

    # Template HTML con CSS inline per funzionare anche offline senza dipendenze
    html_content = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>Report Qualimetria Pepite - NuggetsManagement</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            h1, h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .stats-grid {{ display: flex; gap: 20px; margin-bottom: 30px; }}
            .stat-box {{ flex: 1; background: #ecf0f1; padding: 20px; border-radius: 8px; border-left: 5px solid #3498db; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ padding: 8px 0; border-bottom: 1px solid #ddd; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #3498db; color: white; }}
            tr:hover {{ background-color: #f5f5f5; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>♟️ Report Analisi Pepite (NuggetsManagement)</h1>
            <p>Sintesi automatica delle posizioni estratte per elevata tensione WDL.</p>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <h3>Totale Pepite Estratte</h3>
                    <p style="font-size: 2em; font-weight: bold; margin: 0; color: #e74c3c;">{total_nuggets}</p>
                </div>
                <div class="stat-box">
                    <h3>Distribuzione per Fase</h3>
                    <ul>{fasi_html}</ul>
                </div>
                <div class="stat-box">
                    <h3>Tipi di Centro</h3>
                    <ul>{centri_html}</ul>
                </div>
            </div>

            <h2>🔥 Top 10 Pepite più "Insospettabili" (Alta Frequenza)</h2>
            <table>
                <thead>
                    <tr>
                        <th>FEN</th>
                        <th>Frequenza (Occorrenze)</th>
                        <th>WDL Exp.</th>
                        <th>Delta CP (MultiPV)</th>
                        <th>Ultima Apparizione</th>
                    </tr>
                </thead>
                <tbody>
                    {top_html}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("[*] Dashboard HTML generata con successo!")