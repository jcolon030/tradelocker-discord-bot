from dataclasses import dataclass

@dataclass
class Position:
    id: str
    instrument_id: int
    route_id: int
    side: str
    quantity: float
    entry_price: float

    @classmethod
    def convert_to_position(cls, data):
        return cls(
            id = data[0],
            instrument_id = data[1],
            route_id = data[2],
            side = data[3],
            quantity = float(data[4]),
            entry_price = float(data[5])
        )