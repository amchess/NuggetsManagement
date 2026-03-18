import chess
from enum import Enum

class GamePhase(Enum):
    APERTURA = "Apertura"
    MEDIOGIOCO = "Mediogioco"
    TRANSIZIONE_MEDIOGIOCO = "Transizione Mediogioco"
    TRANSIZIONE_FINALE = "Transizione Finale"
    FINALE = "Finale"

# Spostato a livello globale così può essere usato da tutte le funzioni
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
    Determina la fase della partita basata sull'algoritmo di Smirnov corretto.
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
        
    # Thresholds come da tue indicazioni
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
    Analizza il tipo di centro traducendo la logica bitboard dal C++ a python-chess.
    """
    # Estraiamo i bitboard dei pedoni per efficienza (maschere a 64 bit)
    w_pawns = int(board.pieces(chess.PAWN, chess.WHITE))
    b_pawns = int(board.pieces(chess.PAWN, chess.BLACK))
    
    # Helper per creare maschere di singole case
    def sq_bb(square: int) -> int:
        return 1 << square

    # Presenza di pedoni sulle case critiche
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
        # Verifica tensione immediata sui fianchi
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

    # 5. Centro DINAMICO (IQP e Pedoni Sospesi)
    def is_isolated(color_pawns_bb: int, square: int) -> bool:
        file_idx = chess.square_file(square)
        left_file_bb = chess.BB_FILES[file_idx - 1] if file_idx > 0 else 0
        right_file_bb = chess.BB_FILES[file_idx + 1] if file_idx < 7 else 0
        
        if left_file_bb and (color_pawns_bb & left_file_bb): return False
        if right_file_bb and (color_pawns_bb & right_file_bb): return False
        return True

    if w_d4 and is_isolated(w_pawns, chess.D4): return "Dynamic Center (Isolated Queen's Pawn)"
    if b_d5 and is_isolated(b_pawns, chess.D5): return "Dynamic Center (Isolated Queen's Pawn)"

    def has_hanging_pawns(color_pawns_bb: int) -> bool:
        # Controlliamo le colonne da B a G (indici da 1 a 6)
        for f in range(1, 7):
            current_file_bb = chess.BB_FILES[f]
            left_file_bb = chess.BB_FILES[f - 1]
            
            # Pedoni su due colonne adiacenti
            if (color_pawns_bb & current_file_bb) and (color_pawns_bb & left_file_bb):
                outer_left_bb = chess.BB_FILES[f - 2] if (f - 2) >= 0 else 0
                outer_right_bb = chess.BB_FILES[f + 1] if (f + 1) <= 7 else 0
                
                # Nessun pedone sulle colonne esterne
                if not (color_pawns_bb & outer_left_bb) and not (color_pawns_bb & outer_right_bb):
                    return True
        return False

    if has_hanging_pawns(w_pawns) or has_hanging_pawns(b_pawns):
        return "Dynamic Center (Hanging Pawns)"

    return "Dynamic Center"

def get_tension(board: chess.Board) -> int:
    """Restituisce il numero di catture legali istantaneamente possibili."""
    return len(list(board.generate_legal_captures()))

def get_material_imbalance(board: chess.Board) -> float:
    """Calcola l'asimmetria del materiale."""
    w_mat = sum(PIECE_VALUES[p.piece_type] for p in board.piece_map().values() if p.color == chess.WHITE)
    b_mat = sum(PIECE_VALUES[p.piece_type] for p in board.piece_map().values() if p.color == chess.BLACK)
    return round(abs(w_mat - b_mat), 2)