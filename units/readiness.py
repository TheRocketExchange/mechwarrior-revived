"""Readiness transitions shared by costing and worked-example checks.

This models non-'Mech orders, not movement, targeting, or a whole game.
The caller resolves an action before applying its returned pushing damage.
"""
from enum import IntEnum


class Readiness(IntEnum):
    READY = 0
    COMMITTED = 1
    SPENT = 2


COMBAT = {"Fire", "Advance", "Assault", "Bypass"}
RECOVERY = {"Move", "Hold", "Disengage", "Regroup"}
OTHER = {"Rush", "Repair", "Coolant Flush", "Embark", "Disembark"}


def order(state, action):
    """Return (new state, pushing damage owed by each surviving base)."""
    state = Readiness(state)
    if action in RECOVERY:
        return Readiness.READY, 0
    if action not in COMBAT | OTHER:
        raise ValueError(f"Unknown non-Mech action: {action}")
    if state == Readiness.SPENT:
        raise ValueError("A Spent group must recover")
    if action in COMBAT:
        return Readiness(state + 1), int(state == Readiness.COMMITTED)
    return state, 0


def finish_action(live_clicks, damage_during_action, pushing_damage):
    """Remove casualties before paying push; never pass that damage to allies."""
    remaining = max(0, live_clicks - damage_during_action)
    return max(0, remaining - pushing_damage) if remaining else 0
