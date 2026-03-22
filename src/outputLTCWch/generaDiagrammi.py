import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Imposta uno stile elegante da pubblicazione accademica
sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)

# Carica il dataset
print("Caricamento dataset...")
df = pd.read_csv('nuggets.csv')

# ---------------------------------------------------------
# GRAFICO 1: Distribuzione per Fase di Gioco
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
# Ordine cronologico della partita per avere senso logico sull'asse X
fasi_order = ['Apertura', 'Mediogioco', 'Transizione Mediogioco', 'Transizione Finale', 'Finale']

ax1 = sns.countplot(data=df, x='Fase', order=fasi_order, palette="viridis")
plt.title('Distribuzione dei Picchi di Tensione (WDL 75/25) per Fase di Gioco', fontsize=14, pad=15, fontweight='bold')
plt.ylabel('Numero di Pepite Estratte', fontsize=12)
plt.xlabel('Fase della Partita', fontsize=12)

# Aggiunge i numerini esatti sopra ogni colonna
for p in ax1.patches:
    ax1.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()), 
                 ha='center', va='bottom', fontsize=11, color='black', xytext=(0, 5), textcoords='offset points')

plt.tight_layout()
plt.savefig('Fig1_Distribuzione_Fasi.png', dpi=300, bbox_inches='tight')
print("[OK] Salvato: Fig1_Distribuzione_Fasi.png")

# ---------------------------------------------------------
# GRAFICO 2: Distribuzione per Tipologia di Centro
# ---------------------------------------------------------
plt.figure(figsize=(12, 8))
# Ordina dal più frequente al meno frequente
centro_order = df['Centro'].value_counts().index

ax2 = sns.countplot(data=df, y='Centro', order=centro_order, palette="mako")
plt.title('Frequenza dei Picchi di Tensione per Struttura del Centro', fontsize=14, pad=15, fontweight='bold')
plt.xlabel('Numero di Pepite Estratte', fontsize=12)
plt.ylabel('Tipologia di Centro (Bitboard Classification)', fontsize=12)

# Aggiunge i numerini a destra di ogni barra
for p in ax2.patches:
    ax2.annotate(f'{int(p.get_width())}', (p.get_width(), p.get_y() + p.get_height() / 2.), 
                 ha='left', va='center', fontsize=11, color='black', xytext=(5, 0), textcoords='offset points')

plt.tight_layout()
plt.savefig('Fig2_Distribuzione_Centri.png', dpi=300, bbox_inches='tight')
print("[OK] Salvato: Fig2_Distribuzione_Centri.png")
print("Elaborazione grafici completata!")