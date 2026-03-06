"""
planner -- A goal-directed reasoning system inspired by Hewitt's PLANNER
and Winograd's SHRDLU.

Provides backward-chaining goal resolution, forward-chaining consequent
theorems, an assertion database, automatic backtracking, and a blocks-world
demonstration environment.

    from planner import PlannerDatabase, BlocksWorld

See planner.py for the full historical essay and implementation.
"""

from .planner import (
    PlannerDatabase,
    Assertion,
    ConsequentTheorem,
    AntecedentTheorem,
    Action,
    BlocksWorld,
    PlannerError,
    GoalFailure,
    BacktrackPoint,
    Unifier,
)

__all__ = [
    "PlannerDatabase",
    "Assertion",
    "ConsequentTheorem",
    "AntecedentTheorem",
    "Action",
    "BlocksWorld",
    "PlannerError",
    "GoalFailure",
    "BacktrackPoint",
    "Unifier",
]
