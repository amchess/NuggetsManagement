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
    Analizza il tipo di centro traducendo ESATTAMENTE la logica corretta dal C++ 
    (pawns_element.cpp) a python-chess.
    """
    w_pawns = int(board.pieces(chess.PAWN, chess.WHITE))
    b_pawns = int(board.pieces(chess.PAWN, chess.BLACK))
    
    def sq_bb(square: int) -> int:
        return 1 << square

    # Variabili booleane di presenza pedoni
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

    # Conta i pedoni centrali per colore
    white_center_count = sum([w_d4, w_e4, w_d5, w_e5])
    black_center_count = sum([b_d4, b_e4, b_d5, b_e5])

    # 1. Centro APERTO: nessun pedone sulle 4 case centrali
    if white_center_count == 0 and black_center_count == 0:
        return "Open Center"

    # Preparazione per verifiche di tensione (come nel C++)
    FileDBB = chess.BB_FILES[3]
    FileEBB = chess.BB_FILES[4]
    
    w_center_pawns = w_pawns & (FileDBB | FileEBB)
    b_center_pawns = b_pawns & (FileDBB | FileEBB)

    # Funzione helper per calcolare gli attacchi dei pedoni
    def pawn_attacks_bb(pawns: int, color: chess.Color) -> int:
        attacks = 0
        if color == chess.WHITE:
            attacks |= (pawns << 7) & ~chess.BB_FILE_H
            attacks |= (pawns << 9) & ~chess.BB_FILE_A
        else:
            attacks |= (pawns >> 7) & ~chess.BB_FILE_A
            attacks |= (pawns >> 9) & ~chess.BB_FILE_H
        return attacks & 0xFFFFFFFFFFFFFFFF

    w_center_attacks = pawn_attacks_bb(w_center_pawns, chess.WHITE)
    b_center_attacks = pawn_attacks_bb(b_center_pawns, chess.BLACK)

    # C'è tensione se i pedoni centrali possono catturarsi a vicenda
    central_tension = bool((w_center_attacks & b_center_pawns) or (b_center_attacks & w_center_pawns))

    closed_center = False

    # 2. Centro CHIUSO (Codice corretto da C++: tensione annulla la chiusura)
    if not central_tension:
        # Verifichiamo la presenza di almeno un blocco frontale
        if (w_d4 and b_d5) or (w_e4 and b_e5) or (w_d5 and b_d6) or (w_e5 and b_e6):
            # Un vero centro chiuso richiede pedoni su entrambe le colonne centrali per entrambi i colori
            if (w_center_pawns & FileDBB) and (w_center_pawns & FileEBB) and \
               (b_center_pawns & FileDBB) and (b_center_pawns & FileEBB):
                closed_center = True

    if closed_center:
        if (w_d4 and w_e5 and b_d5 and b_e6) or (b_d4 and b_e5 and w_d5 and w_e3):
            return "Closed Center (French Chain)"
        if (w_e4 and w_d5 and b_e5 and b_d6) or (b_e4 and b_d5 and w_e5 and w_d3):
            return "Closed Center (King's Indian Chain)"
        return "Closed Center"

    # 3. Centro STATICO: pedoni centrali fissi su colonne opposte (Correzione bug tensioni)
    Rank3BB = chess.BB_RANKS[2]
    Rank4BB = chess.BB_RANKS[3]
    Rank5BB = chess.BB_RANKS[4]
    Rank6BB = chess.BB_RANKS[5]

    if (w_d4 and b_d5) and not (w_e4 or b_e4 or w_e5 or b_e5):
        no_immediate_tension = True
        if (w_pawns & (Rank3BB | Rank4BB)) or (b_pawns & (Rank6BB | Rank5BB)):
            no_immediate_tension = False
        if no_immediate_tension:
            return "Static Center (d4-d5)"

    if (w_e4 and b_e5) and not (w_d4 or b_d4 or w_d5 or b_d5):
        no_immediate_tension = True
        if (w_pawns & (Rank3BB | Rank4BB)) or (b_pawns & (Rank6BB | Rank5BB)):
            no_immediate_tension = False
        if no_immediate_tension:
            return "Static Center (e4-e5)"

    # 4. Centro MOBILE
    if (w_d4 and (w_e3 or w_c3)) or (w_e4 and (w_d3 or w_f3)):
        return "Mobile Center"
    if (b_d5 and (b_e6 or b_c6)) or (b_e5 and (b_d6 or b_f6)):
        return "Mobile Center"

    # 5. Centro DINAMICO (Logica IQP e Hanging Pawns corretta dal C++)
    def is_isolated(color_pawns_bb: int, sq: int) -> bool:
        f = chess.square_file(sq)
        left_f = f - 1
        right_f = f + 1
        
        if left_f >= 0 and (color_pawns_bb & chess.BB_FILES[left_f]):
            return False
        if right_f <= 7 and (color_pawns_bb & chess.BB_FILES[right_f]):
            return False
        return True

    if w_d4 and is_isolated(w_pawns, chess.D4):
        return "Dynamic Center (Isolated Queen's Pawn)"
    if b_d5 and is_isolated(b_pawns, chess.D5):
        return "Dynamic Center (Isolated Queen's Pawn)"

    # Funzione Hanging Pawns fedele al C++ (find_hanging_pawns)
    def find_hanging_pawns(color_pawns: int, color: chess.Color) -> bool:
        # P = iterazione sui pedoni (per simulare il pop_lsb del C++)
        for s in chess.SQUARES:
            if not (color_pawns & sq_bb(s)):
                continue
                
            f = chess.square_file(s)
            r = chess.square_rank(s)
            
            # Devono essere pedoni centrali o semi-centrali (c, d, e) -> indici 2, 3, 4
            if 2 <= f <= 4:
                # Devono essere avanzati (non sulle traverse di partenza)
                is_advanced = (r >= 2) if color == chess.WHITE else (r <= 5)
                
                # Controlliamo che ci sia il compagno esattamente a destra (s+1)
                # Nota: In python-chess la casa s+1 è quella a destra se f non è H
                if is_advanced and (color_pawns & sq_bb(s + 1)):
                    left_outer = f - 1
                    right_outer = f + 2
                    
                    has_left_outer = bool(color_pawns & chess.BB_FILES[left_outer]) if left_outer >= 0 else False
                    has_right_outer = bool(color_pawns & chess.BB_FILES[right_outer]) if right_outer <= 7 else False
                    
                    if not has_left_outer and not has_right_outer:
                        return True
        return False

    if find_hanging_pawns(w_pawns, chess.WHITE) or find_hanging_pawns(b_pawns, chess.BLACK):
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