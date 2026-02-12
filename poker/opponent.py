from dataclasses import dataclass

@dataclass
class OpponentStats:
    hands: int = 0
    vpip: int = 0          # voluntarily put money in pot preflop
    pfr: int = 0           # preflop raise
    postflop_bets: int = 0
    postflop_calls: int = 0
    postflop_folds: int = 0

    def vpip_rate(self) -> float:
        return self.vpip / self.hands if self.hands else 0.0

    def pfr_rate(self) -> float:
        return self.pfr / self.hands if self.hands else 0.0

    def aggression_factor(self) -> float:
        # AF = bets / calls (avoid div by zero)
        return self.postflop_bets / max(1, self.postflop_calls)

    def fold_rate_postflop(self) -> float:
        denom = self.postflop_bets + self.postflop_calls + self.postflop_folds
        return self.postflop_folds / denom if denom else 0.0


class OpponentModel:
    """
    Translates observed stats into a crude opponent range tightness and fold tendencies.
    This is intentionally simple for MVP; we can upgrade later.
    """
    def __init__(self, stats: OpponentStats):
        self.stats = stats

    def preflop_tightness(self) -> float:
        """
        Returns tightness in [0,1], where 1 is very tight.
        Derived from VPIP: higher VPIP => looser => lower tightness.
        """
        vpip = self.stats.vpip_rate()
        # Clamp a typical heads-up VPIP range: 0.3 to 0.9
        vpip_clamped = min(0.9, max(0.3, vpip if self.stats.hands >= 10 else 0.6))
        # Map vpip 0.9 -> 0.0 tight, vpip 0.3 -> 1.0 tight
        return (0.9 - vpip_clamped) / (0.9 - 0.3)

    def fold_to_bet_postflop(self) -> float:
        """
        Fold tendency postflop. Uses observed fold rate with a prior.
        """
        # Prior: 0.35 fold
        prior = 0.35
        w = min(1.0, self.stats.hands / 50.0)
        return (1 - w) * prior + w * self.stats.fold_rate_postflop()

    def bluffiness(self) -> float:
        """
        Higher aggression factor => more bluffy / more likely to bet marginal hands.
        """
        af = self.stats.aggression_factor()
        # AF in HU can be 0.5 to 4+. Map 0.5->0, 4->1
        af_clamped = min(4.0, max(0.5, af))
        return (af_clamped - 0.5) / (4.0 - 0.5)
