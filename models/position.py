from dataclasses import dataclass

@dataclass
class Position:
    id: str
    instrument_id: int
    route_id: int
    side: str
    entry_price: float