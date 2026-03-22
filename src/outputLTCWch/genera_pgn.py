import pandas as pd

print("Caricamento dataset...")
df = pd.read_csv('nuggets.csv')

# Rimuovi eventuali duplicati esatti di FEN
df = df.drop_duplicates(subset=['FEN']).copy()

# --- NUOVO FILTRO GLOBALE: Mantiene solo le pepite più profonde (nodi foglia) ---
print("Filtraggio dell'albero delle varianti per mantenere solo le linee più profonde...")
df['Variante_PGN'] = df['Variante_PGN'].astype(str).str.strip()
df['pgn_len'] = df['Variante_PGN'].str.len()

# Ordiniamo per lunghezza decrescente: le varianti con più mosse vengono prima
df_sorted = df.sort_values(by='pgn_len', ascending=False)

keep_indices = []
kept_pgns = []

for idx, row in df_sorted.iterrows():
    current_pgn = row['Variante_PGN']
    
    # Controlliamo se questa variante (essendo più corta) è solo l'inizio di una più lunga già tenuta
    is_subset = False
    for kept in kept_pgns:
        if kept.startswith(current_pgn):
            is_subset = True
            break
            
    if not is_subset:
        keep_indices.append(idx)
        kept_pgns.append(current_pgn)

# Ora abbiamo un dataset purissimo: nessuna pepita è la prosecuzione di un'altra.
df_clean = df.loc[keep_indices].copy()
print(f"Riduzione completata: da {len(df)} a {len(df_clean)} pepite strutturalmente indipendenti.")


# --- SELEZIONE DELLE 100 PEPITE (ora peschiamo dal dataset pulito) ---
selection = []
selected_fens = set()

def add_to_selection(subset_df, limit, category_name):
    count = 0
    for _, row in subset_df.iterrows():
        if count >= limit:
            break
        if row['FEN'] not in selected_fens:
            row_dict = row.to_dict()
            row_dict['Categoria'] = category_name
            selection.append(row_dict)
            selected_fens.add(row['FEN'])
            count += 1

# 1. Top 20 Storiche (Frequenza maggiore)
freq_df = df_clean.sort_values(by='Frequenza', ascending=False)
add_to_selection(freq_df, 20, "Frequenza Storica")

# 2. Top 40 Tattiche (Delta CP più alto)
tactical_df = df_clean.sort_values(by='Delta_CP', ascending=False)
add_to_selection(tactical_df, 40, "Tattica Estrema (Alto Delta CP)")

# 3. Top 40 Posizionali (Delta CP più basso, a partire da 0.0)
positional_df = df_clean.sort_values(by='Delta_CP', ascending=True)
add_to_selection(positional_df, 40, "Dominio Posizionale (Basso Delta CP)")

# Integrazione se necessario per arrivare a 100
if len(selection) < 100:
    remaining_df = df_clean[~df_clean['FEN'].isin(selected_fens)].sort_values(by='Tensione', ascending=False)
    add_to_selection(remaining_df, 100 - len(selection), "Integrazione Qualimetrica")

print(f"Estrazione completata: {len(selection)} pepite definitive selezionate.")
print("Scrittura del file PGN in corso...")

# Generazione del file PGN finale
with open('nuggets_top100.pgn', 'w', encoding='utf-8') as f:
    for i, row in enumerate(selection, 1):
        date = row['Data_Recente'] if pd.notna(row['Data_Recente']) else "????.??.??"
        variante = row['Variante_PGN']
        
        f.write(f'[Event "Nuggets Test Suite - {row["Categoria"]}"]\n')
        f.write(f'[Site "NuggetsManagement"]\n')
        f.write(f'[Date "{date}"]\n')
        f.write(f'[Round "{i}"]\n')
        f.write(f'[White "Motore Test (Bianco)"]\n')
        f.write(f'[Black "Motore Test (Nero)"]\n')
        f.write(f'[Result "*"]\n')
        f.write(f'[Annotator "Fase: {row["Fase"]} | Centro: {row["Centro"]} | Delta CP: {row["Delta_CP"]} | WDL: {row["WDL"]}"]\n')
        f.write(f'[Target_FEN "{row["FEN"]}"]\n\n')
        f.write(f'{variante} *\n\n')

print("[OK] File 'nuggets_top100.pgn' generato con successo e ottimizzato!")