import streamlit as st
import pandas as pd

from poker.cards import str_to_card
from poker.equity import monte_carlo_equity
from poker.ev import ev_fold, ev_call, ev_raise
from poker.sim import SessionState

st.set_page_config(page_title="Poker Decision Assistant (HU NLHE)", layout="wide")

# ---------------- Session init ----------------
if "session" not in st.session_state:
    st.session_state.session = SessionState(bankroll=0.0)

if "last_calc" not in st.session_state:
    # Stores last computed outputs so logging works even after reruns
    st.session_state.last_calc = None

session = st.session_state.session

# ---------------- Card Constants ----------------
RANKS = ["2","3","4","5","6","7","8","9","T","J","Q","K","A"]
SUITS = ["s","h","d","c"]

# ---------------- Helper Functions ----------------
def card_picker(label: str, key: str):
    """Dropdown-based card picker that returns 'As' style strings or None."""
    col1, col2 = st.columns(2)
    rank = col1.selectbox(f"{label} Rank", ["—"] + RANKS, key=f"{key}_rank")
    suit = col2.selectbox(f"{label} Suit", ["—"] + SUITS, key=f"{key}_suit")
    if rank == "—" or suit == "—":
        return None
    return rank + suit

def parse_cards(card_list):
    cards = []
    for c in card_list:
        if c is not None:
            cards.append(str_to_card(c))
    return cards

def has_duplicates(cards):
    return len(cards) != len(set(cards))

# ---------------- Tabs ----------------
tab_decision, tab_session, tab_about = st.tabs(["🧠 Decision", "📈 Session", "ℹ️ About"])

# =========================================================
# DECISION TAB
# =========================================================
with tab_decision:
    st.title("Heads-Up NLHE — Decision Assistant")
    st.caption("Select cards → set betting situation → compute EVs → optionally log the outcome.")

    # Use a form so inputs are “submitted” together (less confusing)
    with st.form("decision_form"):
        st.subheader("1) Select Your Hand")

        colA, colB = st.columns(2)

        with colA:
            st.markdown("### Hero Hole Cards")
            h1 = card_picker("Hero Card 1", "hero1")
            h2 = card_picker("Hero Card 2", "hero2")

        with colB:
            st.markdown("### Board (optional)")
            st.markdown("**Flop**")
            f1 = card_picker("Flop 1", "flop1")
            f2 = card_picker("Flop 2", "flop2")
            f3 = card_picker("Flop 3", "flop3")
            st.markdown("**Turn**")
            t1 = card_picker("Turn", "turn1")
            st.markdown("**River**")
            r1 = card_picker("River", "river1")

        st.subheader("2) Betting Situation")
        c1, c2, c3 = st.columns(3)
        pot = c1.number_input("Current Pot", min_value=0.0, value=10.0, step=1.0)
        call_amt = c2.number_input("Call Amount", min_value=0.0, value=5.0, step=1.0)
        raise_amt = c3.number_input("Raise Amount (your added risk)", min_value=0.0, value=15.0, step=1.0)

        st.subheader("3) Opponent Tendencies (simple)")
        o1, o2, o3 = st.columns(3)
        looseness = o1.slider("Preflop Looseness", 0, 100, 60)
        aggression = o2.slider("Postflop Aggression", 0, 100, 50)
        fold_to_raise = o3.slider("Fold to Raise % (estimate)", 0, 100, 35)

        fold_prob = max(0.05, min(0.95, fold_to_raise / 100.0))

        with st.expander("Advanced Settings", expanded=False):
            mc_trials = st.slider("Monte Carlo Trials", 500, 20000, 3000, step=500)
            seed = st.number_input("Random Seed", value=7, step=1)

        compute = st.form_submit_button("Compute Recommendation", type="primary")

    # ---------- Compute block (runs only when form submitted) ----------
    if compute:
        hero_cards = parse_cards([h1, h2])
        board_cards = parse_cards([f1, f2, f3, t1, r1])

        # Validations
        if len(hero_cards) != 2:
            st.error("Please select exactly 2 hero cards.")
            st.stop()

        # Basic board consistency checks (optional but helps UX)
        flop_selected = [f1, f2, f3]
        if any(x is not None for x in flop_selected) and not all(x is not None for x in flop_selected):
            st.error("If you enter a flop, please select all 3 flop cards.")
            st.stop()
        if t1 is not None and not all(x is not None for x in flop_selected):
            st.error("Turn selected but flop is incomplete. Please fill the flop first.")
            st.stop()
        if r1 is not None and t1 is None:
            st.error("River selected but turn is missing. Please select the turn first.")
            st.stop()

        all_cards = hero_cards + board_cards
        if has_duplicates(all_cards):
            st.error("Duplicate card detected. Please fix your card selection.")
            st.stop()

        dead = set(all_cards)

        equity = monte_carlo_equity(
            hero_hole=hero_cards,
            board=board_cards,
            dead_cards=dead,
            n=int(mc_trials),
            seed=int(seed)
        )

        evF = ev_fold()
        evC = ev_call(pot=pot, call_amount=call_amt, equity=equity)
        evR = ev_raise(pot=pot, raise_amount=raise_amt, equity=equity, fold_prob=fold_prob)

        results = {"FOLD": evF, "CALL": evC, "RAISE": evR}
        best_action = max(results, key=results.get)

        # Store results so "Log Outcome" works even after reruns
        st.session_state.last_calc = {
            "equity": float(equity),
            "evs": {k: float(v) for k, v in results.items()},
            "best_action": best_action,
            "pot": float(pot),
            "call_amt": float(call_amt),
            "raise_amt": float(raise_amt),
            "fold_prob": float(fold_prob),
            "meta": {
                "looseness": int(looseness),
                "aggression": int(aggression),
                "mc_trials": int(mc_trials),
                "seed": int(seed),
            }
        }

    # ---------- Display last computed results (if any) ----------
    last = st.session_state.last_calc

    st.divider()
    st.subheader("📊 Results")

    if last is None:
        st.info("Fill the form above and click **Compute Recommendation** to see EVs.")
    else:
        evs = last["evs"]
        best_action = last["best_action"]

        a, b, c = st.columns(3)
        a.metric("Equity (MC)", f"{last['equity']:.3f}")
        b.metric("Recommended Action", best_action)
        c.metric("Best EV", f"{evs[best_action]:.2f}")

        df = pd.DataFrame({"Action": list(evs.keys()), "EV": list(evs.values())}).sort_values("EV", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("🧠 Explanation")

        if best_action == "FOLD":
            st.info("""
Folding is recommended because the expected value of continuing does not
justify taking additional risk given your estimated equity and price to continue.
""")
        elif best_action == "CALL":
            st.info("""
Calling is recommended because your equity is strong enough relative to the call price.
Raising does not add enough fold equity or value to justify the added risk in this spot.
""")
        else:
            st.info(f"""
Raising is recommended because:

• Villain folds approximately {last['fold_prob']:.0%} of the time.
• When called, your equity of {last['equity']:.2f} still supports the risk.
• Fold equity + showdown equity produces the highest EV in this simplified model.
""")

    # ---------- Logging (works reliably because it uses last_calc) ----------
    st.divider()
    st.subheader("📒 Log Outcome (optional)")

last = st.session_state.last_calc
if last is None:
    st.info("Compute a recommendation first, then you can log the outcome here.")
else:
    # Persist log inputs so they don't reset on reruns
    if "log_action" not in st.session_state:
        st.session_state.log_action = last["best_action"]
    if "log_realized" not in st.session_state:
        st.session_state.log_realized = 0.0

    with st.form("log_form", clear_on_submit=False):
        l1, l2, l3 = st.columns([1, 1, 1])

        action_taken = l1.selectbox(
            "Action Taken",
            ["FOLD", "CALL", "RAISE"],
            index=["FOLD", "CALL", "RAISE"].index(st.session_state.log_action),
            key="log_action_selectbox"
        )

        realized = l2.number_input(
            "Realized PnL",
            value=float(st.session_state.log_realized),
            step=1.0,
            key="log_realized_input"
        )

        l3.metric("EV (logged)", f"{last['evs'][action_taken]:.2f}")

        submitted = st.form_submit_button("Add to Session", use_container_width=True)

        if submitted:
            # Save latest values
            st.session_state.log_action = action_taken
            st.session_state.log_realized = realized

            session.add_hand(
                pot=last["pot"],
                action=action_taken,
                ev=last["evs"][action_taken],
                result=realized
            )
            st.success("Hand logged ✅")

# =========================================================
# ABOUT TAB
# =========================================================
with tab_about:
    st.title("About This App")
    st.write("""
This MVP demonstrates:

• Monte Carlo equity simulation using treys  
• Expected value calculations for Fold / Call / Raise  
• Simple opponent modeling via fold probability sliders  
• Session tracking with bankroll curve + drawdown  

Next upgrades:

• Range-weighted opponent sampling (instead of random opponent hands)  
• Bet-size dependent fold modeling  
• Multi-street EV tree  
• CFR-lite solver training  
""")
