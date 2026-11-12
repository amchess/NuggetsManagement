import chess.pgn
import argparse
from collections import defaultdict

def get_args():
    parser = argparse.ArgumentParser(description="PGN Crosstable and Elo Estimator")
    parser.add_argument("--pgn", type=str, required=True, help="Path to the PGN file to analyze")
    parser.add_argument("--base-elo", type=float, default=3550.0, help="Base average Elo if no anchor is used (default: 3550)")
    parser.add_argument("--anchor-player", type=str, default="Stockfish18", help="Name of the player to anchor the Elo rating (e.g., 'Stockfish18')")
    parser.add_argument("--anchor-elo", type=float, default=3600.0, help="Official Elo rating of the anchor player (default: 3600)")
    return parser.parse_args()

def calculate_elos(player_scores, h2h_games, base_elo=3550.0, iterations=1000, anchor_player=None, anchor_elo=3600.0):
    """
    Iteratively calculates the Elo rating using the Bradley-Terry model.
    Uses a decaying learning rate to guarantee perfect mathematical convergence.
    Anchors a specific player to a known official Elo rating to calibrate the scale.
    """
    ratings = {p: base_elo for p in player_scores}
    lr = 10.0  # Initial learning rate
    
    for _ in range(iterations):
        new_ratings = {}
        for p1 in ratings:
            actual = player_scores[p1]
            expected = 0.0
            
            for p2 in ratings:
                if p1 != p2:
                    n = h2h_games[p1][p2]
                    if n > 0:
                        expected += n / (1.0 + 10 ** ((ratings[p2] - ratings[p1]) / 400.0))
            
            new_ratings[p1] = ratings[p1] + lr * (actual - expected)
        
        # Recenter ratings
        if anchor_player and anchor_player in new_ratings:
            # Shift everyone so that the anchor player has exactly the target Elo
            offset = anchor_elo - new_ratings[anchor_player]
        else:
            # Fallback to average centering
            avg_rating = sum(new_ratings.values()) / len(new_ratings)
            offset = base_elo - avg_rating
            
        ratings = {p: r + offset for p, r in new_ratings.items()}
        
        # Decay learning rate for smooth convergence
        lr *= 0.99
        
    return ratings

def main():
    args = get_args()
    pgn_path = args.pgn

    print(f"[*] Reading PGN file: {pgn_path} ...")

    player_scores = defaultdict(float)
    player_stats = defaultdict(lambda: {"W": 0, "D": 0, "L": 0})
    h2h_scores = defaultdict(lambda: defaultdict(float))
    h2h_games = defaultdict(lambda: defaultdict(int))

    games_count = 0

    try:
        with open(pgn_path, "r", encoding="utf-8", errors="ignore") as f:
            while True:
                headers = chess.pgn.read_headers(f)
                if headers is None:
                    break
                
                white = headers.get("White", "?")
                black = headers.get("Black", "?")
                result = headers.get("Result", "*")
                
                if result == "1-0":
                    w_score, b_score = 1.0, 0.0
                    player_stats[white]["W"] += 1
                    player_stats[black]["L"] += 1
                elif result == "0-1":
                    w_score, b_score = 0.0, 1.0
                    player_stats[white]["L"] += 1
                    player_stats[black]["W"] += 1
                elif result == "1/2-1/2":
                    w_score, b_score = 0.5, 0.5
                    player_stats[white]["D"] += 1
                    player_stats[black]["D"] += 1
                else:
                    continue
                
                player_scores[white] += w_score
                player_scores[black] += b_score
                
                h2h_scores[white][black] += w_score
                h2h_scores[black][white] += b_score
                h2h_games[white][black] += 1
                h2h_games[black][white] += 1
                
                games_count += 1

    except FileNotFoundError:
        print(f"[ERROR] File '{pgn_path}' not found.")
        return

    if games_count == 0:
        print("[!] No valid games found to analyze.")
        return

    if args.anchor_player and args.anchor_player not in player_scores:
        print(f"[ERROR] Anchor player '{args.anchor_player}' not found in the PGN. "
              f"Players: {sorted(player_scores)}. Use --anchor-player with the exact name.")
        return

    elos = calculate_elos(
        player_scores, 
        h2h_games, 
        base_elo=args.base_elo, 
        anchor_player=args.anchor_player, 
        anchor_elo=args.anchor_elo
    )

    sorted_players = sorted(player_scores.keys(), key=lambda p: (player_scores[p], elos[p]), reverse=True)
    num_players = len(sorted_players)

    print(f"[*] Successfully processed {games_count} games.")
    print("\n" + "="*105)
    print(" " * 42 + "TOURNAMENT CROSSTABLE")
    print("="*105)

    header_str = f"{'Rank':<4} | {'Engine / Player':<22} | {'Est. Elo':<8} | {'Score':<6} | {'W-D-L':<15} | "
    header_str += " | ".join([f"{i+1:^5}" for i in range(num_players)])
    print(header_str)
    print("-" * 105)

    for i, p1 in enumerate(sorted_players):
        score = player_scores[p1]
        elo = int(round(elos[p1]))
        w = player_stats[p1]["W"]
        d = player_stats[p1]["D"]
        l = player_stats[p1]["L"]
        wdl_str = f"+{w} ={d} -{l}"
        
        row_str = f"{i+1:<4} | {p1:<22} | {elo:<8} | {score:<6.1f} | {wdl_str:<15} | "
        
        cells = []
        for j, p2 in enumerate(sorted_players):
            if i == j:
                cells.append("  X  ")
            else:
                pts = h2h_scores[p1][p2]
                played = h2h_games[p1][p2]
                if played == 0:
                    cells.append("  -  ")
                else:
                    cells.append(f"{pts:>4.1f} ")
        
        row_str += " | ".join(cells)
        print(row_str)

    print("="*105 + "\n")

if __name__ == "__main__":
    main()