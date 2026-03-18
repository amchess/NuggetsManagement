import chess
from state_manager import GamePhase

# Costanti per il valore dei pezzi (Algoritmo di Smirnov e Asimmetria)
PIECE_VALUES = {
    chess.KING: 0.0,
    chess.QUEEN: 9.0,
    chess.ROOK: 5.0,
    chess.BISHOP: 3.0,
    chess.KNIGHT: 3.0,
    chess.PAWN: 1.0
}

def get_game_phase(board: chess.Board) -> GamePhase:
    """
    Determina la fase della partita basata sull'algoritmo di Smirnov.
    """
    tot_mat_fase = 0.0
    num_tot_unit = 0
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            num_tot_unit += 1
            tot_mat_fase += PIECE_VALUES.get(piece.piece_type, 0.0)
            
    num_semi_move = board.ply()
    
    if num_semi_move == 0:
        phase_index = (num_tot_unit * tot_mat_fase) / 0.003
    else:
        phase_index = (num_tot_unit * tot_mat_fase) / (3 * (num_semi_move + 0.001))
        
    if 0 <= phase_index < 5:
        return GamePhase.FINALE
    elif 5 <= phase_index < 10:
        return GamePhase.TRANSIZIONE_FINALE
    elif 10 <= phase_index < 40:
        return GamePhase.MEDIOGIOCO
    elif 40 <= phase_index < 50:
        return GamePhase.TRANSIZIONE_MEDIOGIOCO
    else:
        return GamePhase.APERTURA

def analyze_center_type(board: chess.Board) -> str:
    """
    Classifica il tipo di centro usando l'algebra dei Bitboard per alte prestazioni.
    """
    w_pawns = int(board.pieces(chess.PAWN, chess.WHITE))
    b_pawns = int(board.pieces(chess.PAWN, chess.BLACK))
    
    def sq_bb(square: int) -> int:
        return 1 << square

    w_d4 = bool(w_pawns & sq_bb(chess.D4))
    w_e4 = bool(w_pawns & sq_bb(chess.E4))
    w_d5 = bool(w_pawns & sq_bb(chess.D5))
    w_e5 = bool(w_pawns & sq_bb(chess.E5))
    w_d3 = bool(w_pawns & sq_bb(chess.D3))
    w_e3 = bool(w_pawns & sq_bb(chess.E3))
    w_c3 = bool(w_pawns & sq_bb(chess.C3))
    w_f3 = bool(w_pawns & sq_bb(chess.F3))

    b_d4 = bool(b_pawns & sq_bb(chess.D4))
    b_e4 = bool(b_pawns & sq_bb(chess.E4))
    b_d5 = bool(b_pawns & sq_bb(chess.D5))
    b_e5 = bool(b_pawns & sq_bb(chess.E5))
    b_d6 = bool(b_pawns & sq_bb(chess.D6))
    b_e6 = bool(b_pawns & sq_bb(chess.E6))
    b_c6 = bool(b_pawns & sq_bb(chess.C6))
    b_f6 = bool(b_pawns & sq_bb(chess.F6))

    white_center_count = sum([w_d4, w_e4, w_d5, w_e5])
    black_center_count = sum([b_d4, b_e4, b_d5, b_e5])

    # 1. Centro APERTO
    if white_center_count == 0 and black_center_count == 0:
        return "Open Center"

    # 2. Centro CHIUSO
    closed_center = False
    if (w_d4 and b_d5) or (w_e4 and b_e5) or (w_d5 and b_d4) or (w_e5 and b_e4):
        if not ((not w_d4 and not b_d4 and not w_d5 and not b_d5) or 
                (not w_e4 and not b_e4 and not w_e5 and not b_e5)):
            closed_center = True

    if closed_center:
        if (w_d4 and w_e5 and b_d5 and b_e6) or (b_d4 and b_e5 and w_d5 and w_e3):
            return "Closed Center (French Chain)"
        if (w_e4 and w_d5 and b_e5 and b_d6) or (b_e4 and b_d5 and w_e5 and w_d3):
            return "Closed Center (King's Indian Chain)"
        return "Closed Center"

    # 3. Centro STATICO
    if (w_d4 and b_d5) and not (w_e4 or b_e4 or w_e5 or b_e5):
        w_tension = w_pawns & (chess.BB_RANK_3 | chess.BB_RANK_4)
        b_tension = b_pawns & (chess.BB_RANK_6 | chess.BB_RANK_5)
        if not w_tension and not b_tension:
            return "Static Center (d4-d5)"

    if (w_e4 and b_e5) and not (w_d4 or b_d4 or w_d5 or b_d5):
        w_tension = w_pawns & (chess.BB_RANK_3 | chess.BB_RANK_4)
        b_tension = b_pawns & (chess.BB_RANK_6 | chess.BB_RANK_5)
        if not w_tension and not b_tension:
            return "Static Center (e4-e5)"

    # 4. Centro MOBILE
    if (w_d4 and (w_e3 or w_c3)) or (w_e4 and (w_d3 or w_f3)):
        return "Mobile Center"
    if (b_d5 and (b_e6 or b_c6)) or (b_e5 and (b_d6 or b_f6)):
        return "Mobile Center"

    # 5. Centro DINAMICO
    def is_isolated(color_pawns_bb: int, square: int) -> bool:
        file_idx = chess.square_file(square)
        left_file_bb = chess.BB_FILES[file_idx - 1] if file_idx > 0 else 0
        right_file_bb = chess.BB_FILES[file_idx + 1] if file_idx < 7 else 0
        
        if left_file_bb and (color_pawns_bb & left_file_bb): return False
        if right_file_bb and (color_pawns_bb & right_file_bb): return False
        return True

    if w_d4 and is_isolated(w_pawns, chess.D4): return "Dynamic Center (Isolated Queen's Pawn