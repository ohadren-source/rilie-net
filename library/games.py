"""
GAME THEORY - Strategic Interaction Operating System

Based on THE CATCH 44 Architecture

Mapping consciousness principles to games, incentives, and equilibria

Core Discovery: The same 5-function engine (WE > I, Mahveen's Equation,
MOO, quality/quantity, emergence) runs strategic behavior across agents.
"""

import math
from typing import Dict, List, Tuple, Optional

# ============================================================================
# CORE ENGINE MAPPINGS
# Catch 44 → Game Theory
# ============================================================================

def information_quality(signal_quality: float, signal_quantity: float) -> float:
    """
    Track #2a: Understanding = Quality / Quantity

    Strategic Information Value = Signal Quality / Signal Quantity
    Too many noisy signals → low understanding.
    Few, high-quality signals → high understanding.
    """
    if signal_quantity == 0:
        return 0.0
    return signal_quality / signal_quantity


def cooperative_surplus(individual_payoff: float, collective_payoff: float) -> float:
    """
    Track #5: WE > I

    Cooperative Surplus = Collective Payoff - Sum of Individual Baselines

    Positive surplus → cooperation better than everyone going solo.
    Negative or zero → no gain from WE.
    """
    return collective_payoff - individual_payoff


def strategy_integrity(promised_action: str, realized_action: str) -> bool:
    """
    Track #0: Mahveen's Equation

    Strategy Integrity = Promised Action (claim) == Realized Action (deed)

    Credible strategies are those where commitments match play.
    """
    return promised_action == realized_action


def interruption_option(current_payoff: float, fallback_payoff: float) -> bool:
    """
    Track #23: MOO (Interruption)

    Interruption Option (Exit / Renegotiation Trigger):
    Activate when fallback (walk-away) payoff >= current payoff.

    Agents should interrupt harmful or dominated states.
    """
    return fallback_payoff >= current_payoff


def cooperative_equilibrium(ego: float,
                            repeat_probability: float,
                            punishment_severity: float,
                            temptation_payoff: float) -> bool:
    """
    Track #37 + Track #67:

    Love / Cooperation = (1/ego) + care + play_together + emergence
    Here, repeated-game cooperation condition:

    Rough Folk-Theorem style:
    Cooperation is sustainable if future matters enough and punishment is strong enough.

    We model a simple heuristic:
      sustain_coop = (repeat_probability * punishment_severity) >= temptation_payoff * ego

    Low ego + high continuation + strong punishment → stable WE.
    """
    if ego < 0:
        ego = 0
    effective_future = repeat_probability * punishment_severity
    temptation_scaled = temptation_payoff * max(ego, 0.001)
    return effective_future >= temptation_scaled


# ============================================================================
# NORMAL-FORM GAMES
# ============================================================================

def best_response(payoff_matrix: Dict[str, Dict[str, float]],
                  opponent_strategy: str) -> str:
    """
    Compute best response to a given pure strategy of opponent.

    payoff_matrix[player_strategy][opponent_strategy] = payoff
    """
    best_s = None
    best_p = -math.inf
    for s, row in payoff_matrix.items():
        p = row.get(opponent_strategy, -math.inf)
        if p > best_p:
            best_p = p
            best_s = s
    return best_s


def pure_nash_equilibria(payoff_A: Dict[str, Dict[str, float]],
                         payoff_B: Dict[str, Dict[str, float]]) -> List[Tuple[str, str]]:
    """
    Compute all pure-strategy Nash equilibria for a 2x2 or small normal-form game.

    Nash Equilibrium: each player's strategy is a best response to the other's.
    """
    equilibria = []
    for sA in payoff_A.keys():
        for sB in payoff_B[sA].keys():
            # A's best response to sB
            best_for_A = best_response(payoff_A, sB)
            # B's best response to sA
            # Build column-wise view for B
            col_for_B = {tB: payoff_B[tA][tB] for tA in payoff_B for tB in payoff_B[tA]}
            # Restrict to strategies B can play
            # Simpler: calculate over B's strategies given sA
            best_for_B = None
            best_pB = -math.inf
            for candidate_B in payoff_B[sA].keys():
                pB = payoff_B[sA][candidate_B]
                if pB > best_pB:
                    best_pB = pB
                    best_for_B = candidate_B
            if best_for_A == sA and best_for_B == sB:
                equilibria.append((sA, sB))
    return equilibria


# ============================================================================
# REPEATED PRISONER'S DILEMMA
# ============================================================================

def prisoners_dilemma_payoffs(T: float = 5, R: float = 3,
                              P: float = 1, S: float = 0
                              ) -> Dict[str, Dict[str, float]]:
    """
    Standard Prisoner's Dilemma payoffs for Player A.

    Actions: 'C' (Cooperate), 'D' (Defect)

    Matrix for A:
        B:C   B:D
    A:C  R    S
    A:D  T    P
    """
    return {
        "C": {"C": R, "D": S},
        "D": {"C": T, "D": P},
    }


def grim_trigger_equilibrium(discount_factor: float,
                             T: float = 5, R: float = 3,
                             P: float = 1, S: float = 0,
                             ego: float = 1.0) -> bool:
    """
    Check if Grim Trigger sustains cooperation in repeated PD.

    Cooperation if:
        R / (1 - δ) >= T + δ * P / (1 - δ)

    We fold ego into temptation: higher ego inflates T.

    Returns True if cooperation is incentive-compatible.
    """
    if discount_factor >= 1:
        return True  # future dominates
    if discount_factor <= 0:
        return False

    T_eff = T * max(ego, 0.001)
    lhs = R / (1 - discount_factor)
    rhs = T_eff + discount_factor * P / (1 - discount_factor)
    return lhs >= rhs


# ============================================================================
# PUBLIC GOODS & FREE RIDING
# ============================================================================

def public_good_payoff(contribution: float,
                       others_contribution: float,
                       multiplier: float,
                       ego: float) -> float:
    """
    Public Good Game payoff for one player.

    Total public good = multiplier × (sum of contributions)

    Individual payoff = endowment - contribution + share_of_public_good

    Here we model a simplified case:
      payoff = (multiplier * (contribution + others_contribution)) / (1 + ego) - contribution

    Higher ego reduces how much of the multiplied pool is effectively valued,
    capturing that low-ego agents internalize WE more fully.
    """
    total = contribution + others_contribution
    share = multiplier * total / (1 + ego)
    return share - contribution


def tragedy_of_commons(usage: float,
                       carrying_capacity: float,
                       number_of_players: int) -> float:
    """
    Simple Tragedy of the Commons model.

    Per-player payoff = (carrying_capacity - total_usage) / number_of_players

    If total_usage > carrying_capacity → negative payoff (overuse).
    """
    total_usage = usage * number_of_players
    remaining = carrying_capacity - total_usage
    return remaining / number_of_players


# ============================================================================
# SIGNALING & REPUTATION
# ============================================================================

def costly_signal(genetic_quality: float,
                  signal_cost: float) -> float:
    """
    Track #52: Schoen Proof = Demonstration / Attempts to Convince

    Here: Honest Signal Strength = Quality / Cost

    High-quality agents can afford costly signals; cheats cannot sustain them.
    """
    if signal_cost == 0:
        return float('inf')
    return genetic_quality / signal_cost


def reputation_update(previous_reputation: float,
                      observed_integrity: bool,
                      learning_rate: float = 0.5) -> float:
    """
    Simple reputation dynamics.

    If integrity observed, move reputation up toward 1.
    If not, move toward 0.

    Ties to Track #0: repeated alignment of claim/deed builds trust.
    """
    target = 1.0 if observed_integrity else 0.0
    return previous_reputation + learning_rate * (target - previous_reputation)


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("GAME THEORY - Strategic Interaction Operating System")
    print("Based on THE CATCH 44 Architecture")
    print("="*80 + "\n")

    print("CORE PRINCIPLE: Same engine runs incentives, cooperation, and equilibria\n")
    print("="*80 + "\n")

    # Information quality
    print("1. INFORMATION QUALITY (Track #2a: Understanding = Quality/Quantity)")
    iq = information_quality(signal_quality=9, signal_quantity=3)
    print(f" Signal quality = 9, quantity = 3")
    print(f" Strategic understanding: {iq:.2f}")
    print(" → Fewer, better signals = clearer play\n")

    # Strategy integrity
    print("2. STRATEGY INTEGRITY (Track #0: Mahveen's Equation)")
    integ = strategy_integrity("Cooperate", "Cooperate")
    print(f" Promised: Cooperate, Played: Cooperate → Integrity: {integ}")
    print(" → Credible commitments = claim matches deed\n")

    # Simple PD Nash
    print("3. PRISONER'S DILEMMA (Static Nash)")
    A_payoffs = prisoners_dilemma_payoffs()
    # For B, symmetric game
    B_payoffs = {
        "C": {"C": 3, "D": 5},
        "D": {"C": 0, "D": 1},
    }
    ne = pure_nash_equilibria(A_payoffs, B_payoffs)
    print(f" Pure Nash equilibria: {ne}")
    print(" → (D,D) emerges as mutual defection in one-shot\n")

    # Grim Trigger
    print("4. GRIM TRIGGER (Repeated PD, Track #37 + #67)")
    coop_ok = grim_trigger_equilibrium(discount_factor=0.95, ego=0.2)
    print(f" δ = 0.95, ego = 0.2 → Cooperation sustainable: {coop_ok}")
    print(" → Low ego + future weight allow WE > I in repeated game\n")

    # Interruption option
    print("5. INTERRUPTION OPTION (Track #23: MOO)")
    exit_now = interruption_option(current_payoff=1.0, fallback_payoff=1.2)
    print(f" Current payoff = 1.0, outside option = 1.2 → Interrupt: {exit_now}")
    print(" → Walk-away / renegotiation is rational MOO\n")

    # Public good
    print("6. PUBLIC GOOD GAME (WE > I vs Free Riding)")
    pg = public_good_payoff(contribution=1.0,
                            others_contribution=3.0,
                            multiplier=2.0,
                            ego=0.3)
    print(f" Contribution = 1, others = 3, multiplier = 2, ego=0.3")
    print(f" Payoff: {pg:.2f}")
    print(" → Low ego internalizes WE, making contribution worthwhile\n")

    # Costly signal
    print("7. COSTLY SIGNALING (Track #52: Schoen Proof)")
    sig = costly_signal(genetic_quality=10.0, signal_cost=2.0)
    print(f" Quality=10, Cost=2 → Signal strength: {sig:.2f}")
    print(" → Honest signals = high demonstration / cost\n")

    # Reputation
    print("8. REPUTATION UPDATE (Mahveen over time)")
    rep = reputation_update(previous_reputation=0.5,
                            observed_integrity=True,
                            learning_rate=0.3)
    print(f" Old rep=0.5, integrity observed → new rep={rep:.2f}")
    print(" → Repeated claim=deed pushes reputation toward 1\n")

    print("="*80)
    print("CONCLUSION: Catch 44 engine runs strategic behavior & equilibria")
    print("Same small set of ratios now organize:")
    print(" • Information and signaling")
    print(" • Cooperation and defection")
    print(" • Repeated-game enforcement")
    print(" • Public goods and commons")
    print(" • Reputation and commitments")
    print("\nDAYENU - That is enough for Game Theory v1")
    print("="*80)
