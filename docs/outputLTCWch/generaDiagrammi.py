import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

print("[*] Loading dataset: nuggets.csv ...")
df = pd.read_csv('nuggets.csv')

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

plt.title('Nugget Distribution by Game Phase', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('Fig1_Phase_Distribution.png', dpi=300)
print("[OK] Saved: Fig1_Phase_Distribution.png")

# ---------------------------------------------------------
# CHART 2: Pawn Center Structures (Bar Chart)
# ---------------------------------------------------------
plt.figure(figsize=(12, 7))
centri_counts = df['Centro'].value_counts()

# Fixed palette warning by assigning hue
ax = sns.barplot(x=centri_counts.index, y=centri_counts.values, hue=centri_counts.index, palette="magma", edgecolor='black', legend=False)

plt.title('Strategic Context: Pawn Center Structures', fontsize=16, fontweight='bold', pad=15)
plt.xlabel('Center Type', fontsize=14)
plt.ylabel('Number of Positions', fontsize=14)

for p in ax.patches:
    ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha='center', va='center', fontsize=12, fontweight='bold', xytext=(0, 10), 
                textcoords='offset points')

plt.tight_layout()
plt.savefig('Fig2_Center_Structures.png', dpi=300)
print("[OK] Saved: Fig2_Center_Structures.png")

# ---------------------------------------------------------
# CHART 3: Indecision Map (Scatter Plot)
# ---------------------------------------------------------
plt.figure(figsize=(12, 8))

sns.scatterplot(data=df, x='Win_Probability', y='Delta_Win_Probability', 
                hue='Fase', style='Fase', s=100, palette='deep', alpha=0.8)

plt.axvline(x=0.25, color='gray', linestyle='--', alpha=0.5, label='Black Target (0.25)')
plt.axvline(x=0.75, color='gray', linestyle='--', alpha=0.5, label='White Target (0.75)')

plt.title('Indecision Map: Win Probability vs MultiPV Delta', fontsize=16, fontweight='bold', pad=15)
plt.xlabel('Win Probability (NNUE)', fontsize=14)
plt.ylabel('Delta Win Probability (Line 1 vs Line 2)', fontsize=14)
plt.legend(title='Game Phase', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.savefig('Fig3_Indecision_Scatter.png', dpi=300, bbox_inches='tight')
print("[OK] Saved: Fig3_Indecision_Scatter.png")

# ---------------------------------------------------------
# CHART 4: Mathematical Tolerance (Delta WDL Histogram)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))

sns.histplot(data=df, x='Delta_Win_Probability', bins=15, kde=True, color='indigo')

plt.title('Mathematical Indecision Distribution (Delta WDL)', fontsize=16, fontweight='bold', pad=15)
plt.xlabel('Delta Win Probability', fontsize=14)
plt.ylabel('Number of Positions (Nuggets)', fontsize=14)

plt.axvline(x=0.03, color='red', linestyle=':', linewidth=2, label='Selection Threshold (0.03)')
plt.legend()

plt.tight_layout()
plt.savefig('Fig4_Delta_Distribution.png', dpi=300)
print("[OK] Saved: Fig4_Delta_Distribution.png")

print("==================================================")
print(" Nugget analysis visuals completed successfully! ")
print("==================================================")