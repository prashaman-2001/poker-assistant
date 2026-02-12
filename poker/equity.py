import random
from treys import Deck, Evaluator

def monte_carlo_equity(hero_hole, board, dead_cards, n=2000, seed=7) -> float:
    """
    hero_hole: [int,int]
    board: list[int] length 0..5
    dead_cards: set[int] cards not allowed (hero + board)
    Returns P(hero wins) + 0.5*P(tie)
    """
    rng = random.Random(seed)
    evaluator = Evaluator()

    wins = 0
    ties = 0
    trials = 0

    for _ in range(n):
        # Build a deck with dead cards removed
        deck = Deck()
        deck.cards = [c for c in deck.cards if c not in dead_cards]
        rng.shuffle(deck.cards)

        # Sample opponent hole
        opp_hole = [deck.draw(1)[0], deck.draw(1)[0]]

        # Complete board
        needed = 5 - len(board)
        runout = board[:] + deck.draw(needed)

        hero_rank = evaluator.evaluate(runout, hero_hole)
        opp_rank = evaluator.evaluate(runout, opp_hole)

        # In treys: lower rank is better
        if hero_rank < opp_rank:
            wins += 1
        elif hero_rank == opp_rank:
            ties += 1
        trials += 1

    return (wins + 0.5 * ties) / max(1, trials)
