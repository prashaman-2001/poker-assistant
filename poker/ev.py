def ev_fold() -> float:
    return 0.0

def ev_call(pot: float, call_amount: float, equity: float) -> float:
    """
    EV of calling a bet of size call_amount into pot.
    If you call, final pot becomes pot + call_amount + call_amount (opponent's bet already counted?).
    Convention here:
      - pot is current pot BEFORE you call, including opponent bet.
      - calling adds call_amount to pot.
    So your win payoff = pot + call_amount, your loss = call_amount.
    """
    return equity * (pot + call_amount) - (1 - equity) * call_amount

def ev_raise(pot: float, raise_amount: float, equity: float, fold_prob: float) -> float:
    """
    Very simplified: when you raise:
      - with prob fold_prob, opponent folds and you win pot
      - otherwise you get called and:
         - you risk raise_amount
         - pot increases by raise_amount (your raise) + raise_amount (their call) -> + 2*raise_amount
         - win payoff = pot + 2*raise_amount
         - loss = raise_amount
    """
    fold_prob = min(0.95, max(0.05, fold_prob))
    called_ev = equity * (pot + 2 * raise_amount) - (1 - equity) * raise_amount
    return fold_prob * pot + (1 - fold_prob) * called_ev
