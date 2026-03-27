import chess.pgn
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse

def get_args():
    parser = argparse.ArgumentParser(description="Round Robin Tournament Graphics Generator")
    parser.add_argument("--pgn", type=str, default="RoundRobin_4engines.pgn", help="Tournament PGN file")
    return parser.parse_args()

def main():
    args = get_args()
    pgn_path = args.pgn

    print(f"[*] Reading PGN file: {pgn_path} ...")

    # List to collect data from each game
    games_data = []

    try:
        with open(pgn_path, "r", encoding="utf-8", errors="ignore") as f:
            while True:
                headers = chess.pgn.read_headers(f)
                if headers is None:
                    break
                
                white = headers.get("White", "?")
                black = headers.get("Black", "?")
                result = headers.get("Result", "*")
                ply_count = headers.get("PlyCount", "0")
                
                try:
                    ply = int(ply_count)
                except ValueError:
                    ply = 0

                if result == "1-0":
                    w_res, b_res = "Win", "Loss"
                    w_score, b_score = 1.0, 0.0
                elif result == "0-1":
                    w_res, b_res = "Loss", "Win"
                    w_score, b_score = 0.0, 1.0
                elif result == "1/2-1/2":
                    w_res, b_res = "Draw", "Draw"
                    w_score, b_score = 0.5, 0.5
                else:
                    continue

                games_data.append({"Engine": white, "Opponent": black, "Color": "White", "Result": w_res, "Score": w_score, "Ply": ply})
                games_data.append({"Engine": black, "Opponent": white, "Color": "Black", "Result": b_res, "Score": b_score, "Ply": ply})

    except FileNotFoundError:
        print(f"[ERROR] File '{pgn_path}' not found.")
        return

    df = pd.DataFrame(games_data)
    if df.empty:
        print("[!] No valid data extracted.")
        return

    print(f"[*] Processing {len(df)//2} valid games. Generating charts...")

    # Academic style settings
    plt.style.use('ggplot')
    sns.set_theme(style="whitegrid", font_scale=1.1)

    # =========================================================
    # FIGURE 1: HEAD-TO-HEAD HEATMAP (H2H)
    # =========================================================
    plt.figure(figsize=(10, 8))
    
    h2h_matrix = df.pivot_table(index='Engine', columns='Opponent', values='Score', aggfunc='sum', fill_value=0)
    
    total_scores = h2h_matrix.sum(axis=1).sort_values(ascending=False)
    h2h_matrix = h2h_matrix.loc[total_scores.index, total_scores.index]

    sns.heatmap(h2h_matrix, annot=True, fmt=".1f", cmap="YlOrRd", linewidths=.5, cbar_kws={'label': 'Points Scored'})
    plt.title("Head-to-Head Score Matrix", fontsize=16, fontweight='bold', pad=20)
    plt.ylabel("Engine (Player)")
    plt.xlabel("Opponent")
    plt.tight_layout()
    plt.savefig('Fig5_H2H_Heatmap.png', dpi=300)
    print("[OK] Saved: Fig5_H2H_Heatmap.png")

    # =========================================================
    # FIGURE 2: W-D-L DISTRIBUTION (Stacked Bar Chart)
    # =========================================================
    plt.figure(figsize=(12, 7))

    wdl_counts = df.groupby(['Engine', 'Result']).size().unstack(fill_value=0)
    wdl_counts = wdl_counts.reindex(total_scores.index)
    
    colors = {"Win": "#2ca02c", "Draw": "#7f7f7f", "Loss": "#d62728"}
    
    ax = wdl_counts[['Win', 'Draw', 'Loss']].plot(kind='bar', stacked=True, color=[colors[c] for c in ['Win', 'Draw', 'Loss']], figsize=(12, 7), edgecolor='black')
    
    plt.title("Outcome Distribution (Win, Draw, Loss)", fontsize=16, fontweight='bold', pad=15)
    plt.xlabel("")
    plt.ylabel("Number of Games")
    plt.xticks(rotation=0)
    plt.legend(title="Outcome", bbox_to_anchor=(1.05, 1), loc='upper left')
    
    for c in ax.containers:
        ax.bar_label(c, label_type='center', color='white', fontweight='bold', fontsize=10)

    plt.tight_layout()
    plt.savefig('Fig6_WDL_Distribution.png', dpi=300)
    print("[OK] Saved: Fig6_WDL_Distribution.png")

    # =========================================================
    # FIGURE 3: ADVANTAGE CONVERSION (Global Outcome Pie)
    # =========================================================
    plt.figure(figsize=(9, 9))
    
    white_results = df[df['Color'] == 'White']['Result'].value_counts()
    
    labels_map = {"Win": "White Win", "Loss": "Black Win", "Draw": "Draw"}
    white_results.index = white_results.index.map(labels_map)
    
    pie_colors = {"White Win": "#f1c40f", "Black Win": "#2c3e50", "Draw": "#95a5a6"}
    
    def autopct_format(pct):
        return f'{pct:.1f}%'

    plt.pie(white_results, labels=white_results.index, autopct=autopct_format, 
            startangle=90, colors=[pie_colors.get(x, '#333') for x in white_results.index], 
            textprops={'fontsize': 14, 'fontweight': 'bold'}, shadow=True,
            explode=[0.05 if i==0 else 0 for i in range(len(white_results))])
            
    plt.title("Global Tournament Outcome\n(Conversion Rate vs Defense)", fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig('Fig7_Conversion_Pie.png', dpi=300)
    print("[OK] Saved: Fig7_Conversion_Pie.png")

    # =========================================================
    # FIGURE 4: COMBAT DEPTH (PlyCount Boxplot)
    # =========================================================
    plt.figure(figsize=(12, 7))

    sns.boxplot(data=df, x='Engine', y='Ply', palette="Set2", order=total_scores.index)
    sns.stripplot(data=df, x='Engine', y='Ply', color=".25", alpha=0.3, size=3, order=total_scores.index)

    plt.title("Tactical Resilience: Game Length Distribution (Ply)", fontsize=16, fontweight='bold', pad=15)
    plt.xlabel("")
    plt.ylabel("Game Duration (PlyCount)")
    
    mean_ply = df['Ply'].mean()
    plt.axhline(mean_ply, color='red', linestyle='--', label=f'Global Average ({int(mean_ply)} ply)')
    plt.legend()

    plt.tight_layout()
    plt.savefig('Fig8_Game_Length_Boxplot.png', dpi=300)
    print("[OK] Saved: Fig8_Game_Length_Boxplot.png")

    print("==================================================")
    print(" Tournament visuals generation completed! ")
    print("==================================================")

if __name__ == "__main__":
    main()