from treys import Card

RANKS = "23456789TJQKA"
SUITS = "shdc"  # spades, hearts, diamonds, clubs (treys uses these letters)

def str_to_card(card_str: str) -> int:
    """
    Convert 'As' -> treys Card int.
    """
    card_str = card_str.strip()
    if len(card_str) != 2:
        raise ValueError("Card must be like 'As', 'Td', '7h'.")
    r, s = card_str[0].upper(), card_str[1].lower()
    if r not in RANKS or s not in SUITS:
        raise ValueError("Invalid card string.")
    return Card.new(r + s)

def card_to_str(card_int: int) -> str:
    return Card.int_to_str(card_int)
