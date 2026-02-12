from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class HandLog:
    hand_id: int
    pot: float
    action: str
    ev: float
    result: float  # realized PnL
    bankroll: float

@dataclass
class SessionState:
    bankroll: float = 0.0
    hand_id: int = 0
    logs: List[HandLog] = field(default_factory=list)

    def add_hand(self, pot: float, action: str, ev: float, result: float):
        self.hand_id += 1
        self.bankroll += result
        self.logs.append(HandLog(
            hand_id=self.hand_id,
            pot=pot,
            action=action,
            ev=ev,
            result=result,
            bankroll=self.bankroll
        ))

    def to_frame(self):
        import pandas as pd
        return pd.DataFrame([{
            "hand_id": h.hand_id,
            "pot": h.pot,
            "action": h.action,
            "ev": h.ev,
            "result": h.result,
            "bankroll": h.bankroll
        } for h in self.logs])
