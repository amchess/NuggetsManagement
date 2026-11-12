import asyncio
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List
from qualimetria import GamePhase

class NuggetStatus(Enum):
    PENDING = "Pending"               # In elaborazione
    NOT_NUGGET = "Not Nugget"         # Non rientra nei target WDL
    NUGGET = "Nugget"                 # È una pepita!

@dataclass
class NuggetRecord:
    """Modello dati per tracciare una posizione (FEN) e le sue metriche."""
    fen: str
    status: NuggetStatus
    frequency: int = 1
    last_seen_date: str = "1900-01-01"
    
    # Metriche (Popolate solo se status == NUGGET)
    win_probability: Optional[float] = None
    delta_win_probability: Optional[float] = None
    wdl_1: Optional[tuple] = None   # (W, D, L) della linea migliore, punto di vista del Bianco
    wdl_2: Optional[tuple] = None   # (W, D, L) della seconda linea
    fase: Optional[GamePhase] = None
    centro: Optional[str] = None
    tensione: Optional[int] = None
    material_imbalance: Optional[float] = None
    variant_pgn: Optional[str] = None

class StateManager:
    """Gestore thread-safe della cache delle posizioni."""
    
    def __init__(self):
        # Mappa la stringa FEN al suo record storico
        self._cache: Dict[str, NuggetRecord] = {}
        # Lock asincrono per prevenire race conditions tra i worker
        self._lock = asyncio.Lock()

    async def register_fen(self, fen: str, current_date: str) -> Optional[NuggetStatus]:
        """
        Controlla se la FEN è nota.
        Se esiste: aggiorna data/frequenza e restituisce lo status (salta l'analisi).
        Se non esiste: crea un record PENDING e restituisce None (procede all'analisi).
        """
        async with self._lock:
            if fen in self._cache:
                record = self._cache[fen]
                record.frequency += 1
                # Aggiorna alla data più recente (confronto stringhe standard YYYY.MM.DD)
                if current_date > record.last_seen_date:
                    record.last_seen_date = current_date
                return record.status
            else:
                self._cache[fen] = NuggetRecord(
                    fen=fen, 
                    status=NuggetStatus.PENDING, 
                    last_seen_date=current_date
                )
                return None

    async def update_to_not_nugget(self, fen: str):
        """Marca una FEN in elaborazione come scartata dal filtro WDL."""
        async with self._lock:
            if fen in self._cache:
                self._cache[fen].status = NuggetStatus.NOT_NUGGET

    async def update_to_nugget(self, fen: str, metrics: dict, variant_pgn: str):
        """Salva tutte le metriche per una pepita validata."""
        async with self._lock:
            if fen in self._cache:
                record = self._cache[fen]
                record.status = NuggetStatus.NUGGET
                record.variant_pgn = variant_pgn
                
                # Popola le nuove metriche fornite dal dizionario (senza delta_cp)
                record.win_probability = metrics.get('win_probability')
                record.delta_win_probability = metrics.get('delta_win_probability')
                record.wdl_1 = metrics.get('wdl_1')
                record.wdl_2 = metrics.get('wdl_2')
                record.fase = metrics.get('fase')
                record.centro = metrics.get('centro')
                record.tensione = metrics.get('tensione')
                record.material_imbalance = metrics.get('material_imbalance')

    def get_all_nuggets(self) -> List[NuggetRecord]:
        """Restituisce solo le pepite validate (usato alla fine per l'export)."""
        return [record for record in self._cache.values() if record.status == NuggetStatus.NUGGET]