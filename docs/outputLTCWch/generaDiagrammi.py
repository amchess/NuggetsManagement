import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse

# Uso: python generaDiagrammi.py [--csv nuggets.csv] [--label Pool] [--threshold 0.03]
# Le figure descrivono il file passato con --csv: usare --label per distinguere
# il pool completo dalla selezione Top-100 (i nomi dei file PNG includono l'etichetta).
_p = argparse.ArgumentParser(description="Nugget dataset charts")
_p.add_argument("--csv", default="nuggets.csv")
_p.add_argument("--label", default="Pool")
_p.add_argument("--threshold", type=float, default=0.03, help="Delta WDL threshold drawn in Chart 4")
args = _p.parse_args()

print(f"[*] Loading dataset: {args.csv} ...")
df = pd.read_csv(args.csv)
N = len(df)
TAG = f"{args.label}, n={N}"

# --- AUTO-FIX COLUMN NAMES ---
# This ensures the script works even if columns are 'WIN_PROBABILITY' or 'Win_Probability'
mapping = {
    'WIN_PROBABILITY': 'Win_Probability',
    'Win Probability': 'Win_Probability',
    'Delta_Win_Probability': 'Delta_Win_Probability',
    'Delta': 'Delta_Win_Probability'
}
df = df.rename(columns=mapping)

# Set global academic style
plt.style.use('ggplot')
sns.set_theme(style="whitegrid", font_scale=1.1)

# ---------------------------------------------------------
# CHART 1: Game Phase Distribution (Pie Chart)
# ---------------------------------------------------------
plt.figure(figsize=(10, 8))
logical_order = ["Opening", "Middlegame", "Transition to middlegame", "Transition to endgame", "Endgame"]
# Check if categories exist in data
available_phases = [p for p in logical_order if p in df['Fase'].unique()]
fasi_counts = df['Fase'].value_counts().reindex(available_phases).dropna()

def autopct_format(values):
    def my_format(pct):
        total = sum(values)
        val = int(round(pct * total / 100.0))
        return f'{pct:.1f}%\n({val})'
    return my_format

plt.pie(fasi_counts, labels=fasi_counts.index, autopct=autopct_format(fasi_counts), 
        startangle=140, colors=sns.color_palette("viridis", len(fasi_counts)), 
        explode=[0.05 if label == "Middlegame" else 0 for label in fasi_counts.index],
        textprops={'fontsize': 12, 'fontweight': 'bold'})

plt.title(f'Nugget Distribution by Game Phase ({TAG})', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(f'Fig1_Phase_Distribution_{args.label}.png', dpi=300)
print(f"[OK] Saved: Fig1_Phase_Distribution_{args.label}.png")

# ---------------------------------------------------------
# CHART 2: Pawn Center Structures (Bar Chart)
# ---------------------------------------------------------
plt.figure(figsize=(12, 7))
centri_counts = df['Centro'].value_counts()

# Fixed palette warning by assigning hue
ax = sns.barplot(x=centri_counts.index, y=centri_counts.values, hue=centri_counts.index, palette="magma", edgecolor='black', legend=False)

plt.title(f'Pawn Center Structures ({TAG})', fontsize=16, fontweight='bold', pad=15)
plt.xlabel('Center Type', fontsize=14)
plt.ylabel('Number of Positions', fontsize=14)

for p in ax.patches:
    ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha='center', va='center', fontsize=12, fontweight='bold', xytext=(0, 10), 
                textcoords='offset points')

# --- INIZIO MODIFICA: Risoluzione etichette sovrapposte ---
plt.xticks(rotation=45, ha='right', fontsize=12)
# --- FINE MODIFICA ---

plt.tight_layout()
plt.savefig(f'Fig2_Center_Structures_{args.label}.png', dpi=300)
print(f"[OK] Saved: Fig2_Center_Structures_{args.label}.png")

# ---------------------------------------------------------
# CHART 3: Indecision Map (Scatter Plot)
# ---------------------------------------------------------
plt.figure(figsize=(12, 8))

sns.scatterplot(data=df, x='Win_Probability', y='Delta_Win_Probability', 
                hue='Fase', style='Fase', s=100, palette='deep', alpha=0.8)

plt.axvline(x=0.25, color='gray', linestyle='--', alpha=0.5, label='Black Target (0.25)')
plt.axvline(x=0.75, color='gray', linestyle='--', alpha=0.5, label='White Target (0.75)')

plt.title(f'Indecision Map: Win Probability vs MultiPV Delta ({TAG})', fontsize=16, fontweight='bold', pad=15)
plt.xlabel('Win Probability, White point of view (W + D/2)', fontsize=14)
plt.ylabel('Delta Win Probability (Line 1 vs Line 2)', fontsize=14)
plt.legend(title='Game Phase', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.savefig(f'Fig3_Indecision_Scatter_{args.label}.png', dpi=300, bbox_inches='tight')
print(f"[OK] Saved: Fig3_Indecision_Scatter_{args.label}.png")

# ---------------------------------------------------------
# CHART 4: Mathematical Tolerance (Delta WDL Histogram)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))

sns.histplot(data=df, x='Delta_Win_Probability', bins=15, kde=True, color='indigo')

plt.title(f'Delta WDL Distribution ({TAG})', fontsize=16, fontweight='bold', pad=15)
plt.xlabel('Delta Win Probability', fontsize=14)
plt.ylabel('Number of Positions (Nuggets)', fontsize=14)

plt.axvline(x=args.threshold, color='red', linestyle=':', linewidth=2, label=f'Delta WDL = {args.threshold}')
plt.legend()

plt.tight_layout()
plt.savefig(f'Fig4_Delta_Distribution_{args.label}.png', dpi=300)
print(f"[OK] Saved: Fig4_Delta_Distribution_{args.label}.png")

print("==================================================")
print(" Nugget analysis visuals completed successfully! ")
print("==================================================")