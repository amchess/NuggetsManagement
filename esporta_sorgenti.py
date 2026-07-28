import os

# --- CONFIGURAZIONE ---
NOME_FILE_OUTPUT = "tutti_i_sorgenti_shashgui.txt"
ESTENSIONI_PERMESSE = {'.py', '.ini'} # Puoi aggiungere .txt o .json se vuoi
CARTELLE_DA_IGNORARE = {'__pycache__', '.git', 'venv', 'env', 'build', 'dist', 'localpycs', '.idea', 'images'}

def esporta_codice():
    # Prende la cartella in cui si trova questo script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    percorso_output = os.path.join(base_dir, NOME_FILE_OUTPUT)

    file_processati = 0

    with open(percorso_output, 'w', encoding='utf-8') as outfile:
        outfile.write("="*80 + "\n")
        outfile.write("   ESPORTAZIONE COMPLETA SORGENTI SHASHGUI\n")
        outfile.write("="*80 + "\n\n")

        # Esplora l'alberatura partendo dalla cartella base
        for root, dirs, files in os.walk(base_dir):
            # Filtra le directory escludendo quelle inutili (modifica la lista originale)
            dirs[:] = [d for d in dirs if d not in CARTELLE_DA_IGNORARE]

            for file in files:
                estensione = os.path.splitext(file)[1].lower()
                
                if estensione in ESTENSIONI_PERMESSE:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, base_dir)

                    # Evitiamo di inglobare lo script stesso o il file di output se avessero estensioni strane
                    if file == os.path.basename(__file__) or file == NOME_FILE_OUTPUT:
                        continue

                    # Intestazione grafica per separare i file
                    outfile.write("/" * 80 + "\n")
                    outfile.write(f"/// PERCORSO: {rel_path}\n")
                    outfile.write("/" * 80 + "\n\n")

                    try:
                        # Lettura e scrittura del contenuto
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read() + "\n\n")
                        file_processati += 1
                    except Exception as e:
                        outfile.write(f"// ERRORE DURANTE LA LETTURA DEL FILE: {e}\n\n")
                        print(f"⚠️ Errore su {rel_path}: {e}")

    print(f"✅ Esportazione completata con successo!")
    print(f"📄 Sono stati uniti {file_processati} file sorgenti.")
    print(f"📁 Il file si trova qui: {percorso_output}")

if __name__ == "__main__":
    esporta_codice()