"""
planner.py -- Goal-directed reasoning in the spirit of PLANNER and SHRDLU
==========================================================================

Historical Context
------------------

In 1969, Carl Hewitt, then a graduate student at the MIT AI Laboratory under
Marvin Minsky and Seymour Papert, published his PhD thesis describing PLANNER,
a programming language for proving theorems and manipulating models.  PLANNER
was never fully implemented -- only a subset called MICRO-PLANNER, built by
Gerald Jay Sussman, Eugene Charniak, and Terry Winograd in 1969-1970 -- but
its ideas were among the most consequential in the history of AI.

PLANNER's key insight was GOAL-DIRECTED INVOCATION.  Earlier theorem provers
(like those based on Robinson's 1965 resolution principle) worked by forward-
chaining: start from axioms, apply inference rules, hope you reach the goal.
Hewitt turned this around.  In PLANNER, you state the goal -- the thing you
want to be true -- and the system works BACKWARDS, searching for theorems
whose consequents match your goal and recursively trying to establish their
antecedents.  This is "antecedent theorem" invocation, and it is the heart
of the system.

PLANNER also introduced "consequent theorems" (forward-chaining demons that
fire automatically when new facts are asserted), an assertion database with
pattern-directed retrieval, and automatic chronological backtracking -- the
system would undo side effects and try alternative proof paths on failure.

Hewitt's design directly influenced:

  - PROLOG (1972): Alain Colmerauer and Robert Kowalski's logic programming
    language adopted backward-chaining and backtracking from PLANNER, but
    replaced PLANNER's procedural flavor with a purer declarative semantics
    based on Horn clauses.  Kowalski later wrote that Prolog could be seen
    as a rational reconstruction of PLANNER's core ideas.

  - CONNIVER (1972): Sussman and Drew McDermott, dissatisfied with PLANNER's
    automatic backtracking (which they considered too rigid), built CONNIVER
    to give programmers explicit control over the search process.  This
    debate -- automatic vs. explicit backtracking -- has never been fully
    resolved.

  - The ACTOR MODEL (1973): Hewitt himself moved on from PLANNER to develop
    the Actor model of concurrent computation, partly motivated by the
    realization that goal-directed search and message-passing could be
    unified.

SHRDLU and the Illusion of Understanding
-----------------------------------------

Terry Winograd's SHRDLU (1971), built atop MICRO-PLANNER at the MIT AI Lab,
was a program that could converse in English about a simulated "blocks world"
-- a table with colored blocks, pyramids, and boxes that could be stacked
and moved.  The user could type commands like "Pick up a big red block" or
ask questions like "Is there a block which is taller than the one you are
holding?" and SHRDLU would respond sensibly, updating its model of the world.

The demonstration was electrifying.  For a brief, heady moment, it seemed
like natural language understanding was nearly solved.  SHRDLU could parse
complex sentences, resolve pronoun references, handle quantifiers, and
explain its own reasoning -- all in a 1971 program.

But the appearance was deceiving.  SHRDLU worked because the blocks world
was tiny and closed.  Every noun had a clear referent.  Every verb mapped
to a known action.  There was no metaphor, no ambiguity beyond what the
grammar could handle, no common-sense knowledge about the world outside
the table.  When researchers tried to extend the approach to richer domains,
the systems shattered.  The number of rules needed grew combinatorially,
and the brittle pattern-matching could not handle the open-ended flexibility
of real language.

Winograd himself became one of the most eloquent critics of his own early
work.  In "Understanding Computers and Cognition" (1986, with Fernando
Flores), he argued that the rationalist tradition underlying AI -- the
assumption that understanding can be reduced to symbol manipulation over
formal representations -- was fundamentally limited.  He drew on Heidegger
and Gadamer to argue that human understanding is situated, embodied, and
hermeneutic in ways that no formal system can capture.

The AI Winter
-------------

The collapse of early NLU optimism was one thread in the broader "AI Winter"
of the mid-1970s through the 1980s.  The Lighthill Report (1973) in Britain,
DARPA funding cuts in the US, and the manifest failure of ambitious projects
like machine translation and general problem-solving led to a decade of
reduced funding and lowered expectations.

PLANNER and SHRDLU were buried, but their ideas survived.  Backward chaining
lives on in Prolog, in rule engines, in planning systems like STRIPS and its
descendants (PDDL, FastDownward, etc.), and in the goal-directed search that
underlies modern AI planning.  The blocks world remains a standard benchmark.
And the tension between PLANNER's automatic backtracking and CONNIVER's
explicit control reappears every time a programmer debates whether to use
exceptions, continuations, or explicit state machines.

This module implements the core ideas of PLANNER -- assertion databases,
consequent and antecedent theorems, goal-directed backward chaining, and
automatic backtracking -- applied to a SHRDLU-style blocks world.  It is
a pedagogical reconstruction, not a historical replica; the original
MICRO-PLANNER was written in Lisp for the PDP-10 and its source is not
easily runnable today.


Implementation Overview
-----------------------

Classes:
    Assertion          -- A ground fact in the database (e.g., (on A B))
    ConsequentTheorem  -- Forward-chaining rule: when pattern is asserted, fire
    AntecedentTheorem  -- Backward-chaining rule: to prove goal, try subgoals
    Action             -- An operator with preconditions and effects
    PlannerDatabase    -- The central database + inference engine
    BlocksWorld        -- A blocks-world domain built on PlannerDatabase
    Unifier            -- Pattern matching / unification utilities
    BacktrackPoint     -- Saved state for chronological backtracking

Uses only the Python standard library.
"""

from __future__ import annotations

import copy
import itertools
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class PlannerError(Exception):
    """Base exception for the planner system."""


class GoalFailure(PlannerError):
    """Raised when a goal cannot be achieved."""


class BacktrackSignal(PlannerError):
    """Internal signal used to trigger backtracking."""


# ---------------------------------------------------------------------------
# Terms and patterns
# ---------------------------------------------------------------------------

# A Term is either a string (constant/predicate), a Variable, or a tuple of Terms.
# Variables are strings that start with '?'.

def is_variable(term: Any) -> bool:
    """Return True if *term* is a logic variable (a string starting with '?')."""
    return isinstance(term, str) and len(term) > 1 and term[0] == "?"


def walk(term: Any, bindings: Dict[str, Any]) -> Any:
    """Chase variable bindings to find the ultimate value of *term*."""
    while is_variable(term) and term in bindings:
        term = bindings[term]
    if isinstance(term, (list, tuple)):
        walked = tuple(walk(t, bindings) for t in term)
        return list(walked) if isinstance(term, list) else walked
    return term


def substitute(term: Any, bindings: Dict[str, Any]) -> Any:
    """Recursively substitute all variables in *term* using *bindings*."""
    return walk(term, bindings)


# ---------------------------------------------------------------------------
# Unifier
# ---------------------------------------------------------------------------

class Unifier:
    """
    Pattern-matching / unification engine.

    Supports:
      - Constants unify with identical constants.
      - A variable unifies with any term, creating a binding.
      - Tuples unify element-wise.
      - The wildcard '?' matches anything without creating a binding.

    This is essentially Robinson's unification (1965) restricted to the
    simple term language used by PLANNER.
    """

    @staticmethod
    def unify(
        pattern: Any,
        datum: Any,
        bindings: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to unify *pattern* with *datum* under existing *bindings*.

        Returns an extended binding dictionary on success, or ``None`` on
        failure.  Does NOT mutate the input bindings dict.
        """
        if bindings is None:
            bindings = {}
        else:
            bindings = dict(bindings)  # copy so we don't mutate caller's dict
        return Unifier._unify(pattern, datum, bindings)

    @staticmethod
    def _unify(pattern: Any, datum: Any, bindings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pattern = walk(pattern, bindings)
        datum = walk(datum, bindings)

        if pattern == datum:
            return bindings

        if pattern == "?":
            # Anonymous wildcard -- matches anything, binds nothing.
            return bindings

        if is_variable(pattern):
            bindings[pattern] = datum
            return bindings

        if is_variable(datum):
            bindings[datum] = pattern
            return bindings

        if isinstance(pattern, (tuple, list)) and isinstance(datum, (tuple, list)):
            if len(pattern) != len(datum):
                return None
            for p, d in zip(pattern, datum):
                result = Unifier._unify(p, d, bindings)
                if result is None:
                    return None
                bindings = result
            return bindings

        return None

    @staticmethod
    def match(pattern: Any, datum: Any) -> Optional[Dict[str, Any]]:
        """One-directional match: only variables in *pattern* may bind."""
        return Unifier.unify(pattern, datum)

    @staticmethod
    def apply_bindings(term: Any, bindings: Dict[str, Any]) -> Any:
        """Substitute all bound variables in *term*."""
        return substitute(term, bindings)


# ---------------------------------------------------------------------------
# Database entries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Assertion:
    """
    A ground fact in the database.

    In PLANNER terminology this is simply an assertion -- a statement held
    to be true in the current state of the world.  Assertions are tuples
    of constants, e.g. ``("on", "A", "B")`` meaning block A is on block B.
    """

    content: tuple

    def __post_init__(self):
        if not isinstance(self.content, tuple):
            object.__setattr__(self, "content", tuple(self.content))

    def __repr__(self) -> str:
        return f"Assertion({self.content})"


@dataclass
class ConsequentTheorem:
    """
    A forward-chaining rule (PLANNER's "consequent theorem").

    When a new assertion matching *pattern* is added to the database, the
    *action* callable is invoked with the database and the binding dictionary.
    The action may assert new facts, causing further consequent theorems to
    fire -- this is forward chaining.

    In Hewitt's original design, consequent theorems were the dual of
    antecedent theorems: where antecedent theorems say "to ACHIEVE this
    goal, try these subgoals", consequent theorems say "when this fact
    BECOMES true, perform these side effects".
    """

    name: str
    pattern: tuple
    action: Callable  # (db: PlannerDatabase, bindings: dict) -> None

    def __repr__(self) -> str:
        return f"ConsequentTheorem({self.name!r}, {self.pattern})"


@dataclass
class AntecedentTheorem:
    """
    A backward-chaining rule (PLANNER's "antecedent theorem").

    To prove that *goal_pattern* holds, the system will invoke *body*,
    which receives the database and current bindings and must return an
    iterable of alternative binding dictionaries (each representing a
    successful proof).  Yielding an empty iterable means the theorem
    failed to prove the goal.

    This is the central mechanism of PLANNER and the direct ancestor of
    Prolog's clause resolution.
    """

    name: str
    goal_pattern: tuple
    body: Callable  # (db: PlannerDatabase, bindings: dict) -> Iterator[dict]

    def __repr__(self) -> str:
        return f"AntecedentTheorem({self.name!r}, {self.goal_pattern})"


@dataclass
class Action:
    """
    A STRIPS-style operator with preconditions and effects.

    STRIPS (Fikes & Nilsson, 1971) was developed at SRI concurrently with
    SHRDLU at MIT.  Both systems reasoned about actions in a blocks world,
    but STRIPS focused on plan generation while SHRDLU focused on language
    understanding.  We incorporate both ideas here.

    An Action has:
      - *name*: identifier
      - *parameters*: list of variable names (e.g. ["?block", "?from", "?to"])
      - *preconditions*: list of patterns that must hold before the action
      - *add_effects*: facts to assert after the action executes
      - *delete_effects*: facts to retract after the action executes
    """

    name: str
    parameters: List[str]
    preconditions: List[tuple]
    add_effects: List[tuple]
    delete_effects: List[tuple]

    def __repr__(self) -> str:
        return f"Action({self.name}, params={self.parameters})"


# ---------------------------------------------------------------------------
# Backtracking machinery
# ---------------------------------------------------------------------------

class BacktrackType(Enum):
    CHRONOLOGICAL = auto()
    DEPENDENCY = auto()


@dataclass
class BacktrackPoint:
    """
    A saved snapshot of the database for backtracking.

    PLANNER introduced automatic chronological backtracking: when a proof
    path fails, the system undoes all assertions and retractions made since
    the last choice point and tries the next alternative.

    This module supports two strategies:

    - CHRONOLOGICAL (the PLANNER default): undo to the most recent choice
      point, regardless of whether the most recent choice was relevant to
      the failure.  Simple but can waste work.

    - DEPENDENCY-DIRECTED: track which assertions each subgoal depends on,
      and backtrack only to a choice point that is actually responsible for
      the failure.  This was pioneered by Stallman & Sussman (1977) and is
      the basis of modern constraint solvers and SAT-based planners.
    """

    assertions_snapshot: List[tuple]
    description: str = ""
    dependencies: FrozenSet[tuple] = field(default_factory=frozenset)


# ---------------------------------------------------------------------------
# The database and inference engine
# ---------------------------------------------------------------------------

class PlannerDatabase:
    """
    The central assertion database and inference engine.

    Combines:
      - A set of ground assertions (the "world model")
      - Consequent theorems (forward-chaining rules)
      - Antecedent theorems (backward-chaining rules)
      - Actions (STRIPS-style operators)
      - Automatic backtracking (chronological or dependency-directed)
    """

    def __init__(self, backtrack_type: BacktrackType = BacktrackType.CHRONOLOGICAL):
        self._assertions: List[tuple] = []
        self._consequent_theorems: List[ConsequentTheorem] = []
        self._antecedent_theorems: List[AntecedentTheorem] = []
        self._actions: List[Action] = []
        self._backtrack_stack: List[BacktrackPoint] = []
        self._backtrack_type = backtrack_type
        self._trace: bool = False  # set True for debug output

    # -- Assertions ---------------------------------------------------------

    def assert_fact(self, *content: Any) -> Assertion:
        """
        Add a fact to the database and fire any matching consequent theorems.

        Example::

            db.assert_fact("on", "A", "B")
        """
        fact = tuple(content)
        if fact not in self._assertions:
            self._assertions.append(fact)
            if self._trace:
                print(f"  ASSERT  {fact}")
            self._fire_consequent_theorems(fact)
        return Assertion(fact)

    def retract_fact(self, *content: Any) -> bool:
        """Remove a fact from the database.  Returns True if it was present."""
        fact = tuple(content)
        if fact in self._assertions:
            self._assertions.remove(fact)
            if self._trace:
                print(f"  RETRACT {fact}")
            return True
        return False

    def holds(self, *content: Any) -> bool:
        """Return True if the exact fact is in the database."""
        return tuple(content) in self._assertions

    def query(self, pattern: tuple, bindings: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
        """
        Yield all binding dicts for which *pattern* matches an assertion.

        This is PLANNER's pattern-directed retrieval -- the database is
        searched for assertions that unify with the given pattern.
        """
        if bindings is None:
            bindings = {}
        for fact in self._assertions:
            result = Unifier.unify(pattern, fact, bindings)
            if result is not None:
                yield result

    def all_facts(self) -> List[tuple]:
        """Return a copy of all current assertions."""
        return list(self._assertions)

    # -- Consequent theorems (forward chaining) -----------------------------

    def add_consequent_theorem(self, theorem: ConsequentTheorem) -> None:
        """Register a forward-chaining rule."""
        self._consequent_theorems.append(theorem)

    def _fire_consequent_theorems(self, fact: tuple) -> None:
        """Check all consequent theorems against a newly asserted fact."""
        for ct in self._consequent_theorems:
            bindings = Unifier.match(ct.pattern, fact)
            if bindings is not None:
                if self._trace:
                    print(f"  FIRE consequent theorem {ct.name!r} with {bindings}")
                ct.action(self, bindings)

    # -- Antecedent theorems (backward chaining) ----------------------------

    def add_antecedent_theorem(self, theorem: AntecedentTheorem) -> None:
        """Register a backward-chaining rule."""
        self._antecedent_theorems.append(theorem)

    def prove(
        self,
        goal: tuple,
        bindings: Optional[Dict[str, Any]] = None,
        depth: int = 0,
        max_depth: int = 50,
    ) -> Iterator[Dict[str, Any]]:
        """
        Attempt to prove *goal* by backward chaining.

        This is the core of PLANNER's goal-directed reasoning.  The
        algorithm is:

        1.  Try to satisfy the goal directly from the assertion database
            (pattern-directed retrieval).
        2.  If that fails (or to find additional proofs), try each
            antecedent theorem whose goal_pattern unifies with the goal.
            For each such theorem, invoke its body, which may recursively
            call ``prove`` for subgoals.
        3.  Yield each successful binding dictionary.  The caller can
            iterate to get the first solution (committed choice) or all
            solutions (enumeration).

        The *depth* / *max_depth* parameters prevent infinite recursion,
        which is the Achilles' heel of naive backward chaining (and of
        early PLANNER implementations, which often went into infinite
        loops on circular rule sets).
        """
        if depth > max_depth:
            return

        if bindings is None:
            bindings = {}

        if self._trace:
            indent = "  " * depth
            print(f"{indent}PROVE {substitute(goal, bindings)} [depth={depth}]")

        # Strategy 1: satisfy from the database directly.
        for result in self.query(goal, bindings):
            if self._trace:
                indent = "  " * depth
                print(f"{indent}  FOUND in DB: {result}")
            yield result

        # Strategy 2: try antecedent theorems.
        grounded_goal = substitute(goal, bindings)
        for at in self._antecedent_theorems:
            at_match = Unifier.match(at.goal_pattern, grounded_goal)
            if at_match is not None:
                if self._trace:
                    indent = "  " * depth
                    print(f"{indent}  TRY antecedent theorem {at.name!r}")
                try:
                    # Pass the caller's bindings AND the match separately.
                    # The body receives: db, goal_args (from the match),
                    # caller_bindings, depth.
                    for result in at.body(self, at_match, depth + 1):
                        # Merge result bindings back into caller's bindings.
                        merged = dict(bindings)
                        merged.update(result)
                        yield merged
                except BacktrackSignal:
                    continue

    def prove_all(
        self,
        goals: List[tuple],
        bindings: Optional[Dict[str, Any]] = None,
        depth: int = 0,
    ) -> Iterator[Dict[str, Any]]:
        """
        Prove a conjunction of goals (all must succeed).

        Bindings produced by earlier goals propagate to later goals,
        exactly as in Prolog's left-to-right conjunction evaluation.
        """
        if bindings is None:
            bindings = {}
        if not goals:
            yield bindings
            return
        first, *rest = goals
        for result in self.prove(first, bindings, depth):
            yield from self.prove_all(rest, result, depth)

    # -- Actions (STRIPS operators) -----------------------------------------

    def add_action(self, action: Action) -> None:
        """Register a STRIPS-style action."""
        self._actions.append(action)

    def get_action(self, name: str) -> Optional[Action]:
        """Look up an action by name."""
        for a in self._actions:
            if a.name == name:
                return a
        return None

    def apply_action(self, action: Action, bindings: Dict[str, Any]) -> bool:
        """
        Apply an action with the given variable bindings.

        1. Check all preconditions are satisfied.
        2. Retract delete effects.
        3. Assert add effects.

        Returns True on success, False if preconditions are not met.
        """
        # Ground all patterns.
        grounded_pre = [substitute(p, bindings) for p in action.preconditions]
        grounded_add = [substitute(e, bindings) for e in action.add_effects]
        grounded_del = [substitute(e, bindings) for e in action.delete_effects]

        # Check preconditions.
        for pre in grounded_pre:
            if pre not in self._assertions:
                if self._trace:
                    print(f"  PRECOND FAIL: {pre}")
                return False

        # Apply effects.
        for d in grounded_del:
            self.retract_fact(*d)
        for a in grounded_add:
            self.assert_fact(*a)

        if self._trace:
            print(f"  APPLIED {action.name} with {bindings}")
        return True

    # -- Backtracking -------------------------------------------------------

    def save_state(self, description: str = "", dependencies: FrozenSet[tuple] = frozenset()) -> None:
        """Push a backtrack point (snapshot of assertions)."""
        bp = BacktrackPoint(
            assertions_snapshot=list(self._assertions),
            description=description,
            dependencies=dependencies,
        )
        self._backtrack_stack.append(bp)

    def backtrack(self) -> bool:
        """
        Restore the most recent backtrack point.

        Returns True if a backtrack point was available, False otherwise.

        In dependency-directed mode, the system skips backtrack points
        whose dependencies are disjoint from the current assertion set
        (i.e., the choice point is irrelevant to the current failure).
        """
        if self._backtrack_type == BacktrackType.CHRONOLOGICAL:
            if not self._backtrack_stack:
                return False
            bp = self._backtrack_stack.pop()
            self._assertions = bp.assertions_snapshot
            if self._trace:
                print(f"  BACKTRACK (chronological) to: {bp.description}")
            return True
        else:
            # Dependency-directed: find most recent relevant choice point.
            current_facts = frozenset(tuple(a) for a in self._assertions)
            while self._backtrack_stack:
                bp = self._backtrack_stack.pop()
                if not bp.dependencies or bp.dependencies & current_facts:
                    self._assertions = bp.assertions_snapshot
                    if self._trace:
                        print(f"  BACKTRACK (dependency-directed) to: {bp.description}")
                    return True
            return False

    # -- Goal-directed planning ---------------------------------------------

    def plan(
        self,
        goals: List[tuple],
        max_steps: int = 100,
    ) -> Optional[List[Tuple[str, Dict[str, Any]]]]:
        """
        Find a sequence of actions that transforms the current state into
        one satisfying all *goals*.

        Uses a forward-state-space search guided by goal regression:

        1.  Pick an unsatisfied goal.
        2.  Find an action whose add-effects can satisfy it.
        3.  Try all possible groundings of that action's parameters
            (using the current state and the goal to constrain bindings).
        4.  Apply the action (updating the state), recurse on remaining goals.
        5.  On failure, backtrack (restore state) and try alternatives.

        This is essentially the means-ends analysis strategy used by GPS
        (Newell & Simon, 1963) and STRIPS (Fikes & Nilsson, 1971), both
        of which influenced PLANNER.

        Returns a list of (action_name, bindings) pairs, or None if no plan
        is found within *max_steps*.
        """
        return self._plan_search(goals, [], 0, max_steps, set())

    def _plan_search(
        self,
        goals: List[tuple],
        plan_so_far: List[Tuple[str, Dict[str, Any]]],
        depth: int,
        max_steps: int,
        visited_states: set,
    ) -> Optional[List[Tuple[str, Dict[str, Any]]]]:
        if depth > max_steps:
            return None

        # Check which goals are unsatisfied.
        unsatisfied = [g for g in goals if g not in self._assertions]
        if not unsatisfied:
            return plan_so_far  # All goals met!

        # Create a hashable state key to detect cycles.
        state_key = frozenset(self._assertions)
        if state_key in visited_states:
            return None
        visited_states = visited_states | {state_key}

        # Pick the first unsatisfied goal.
        target_goal = unsatisfied[0]

        # Find actions that can achieve this goal (means-ends analysis).
        relevant = self._relevant_actions(target_goal)

        for action, goal_bindings in relevant:
            # Try all possible complete groundings of the action.
            for gb in self._enumerate_groundings(action, goal_bindings):
                # Save state for backtracking.
                old_assertions = list(self._assertions)
                self.save_state(
                    description=f"before {action.name} {gb}",
                    dependencies=frozenset(
                        substitute(p, gb) for p in action.preconditions
                    ),
                )

                # Check if preconditions are met; if so, apply.
                if self.apply_action(action, gb):
                    new_plan = plan_so_far + [(action.name, dict(gb))]

                    # Recurse: try to satisfy remaining goals.
                    result = self._plan_search(
                        goals, new_plan, depth + 1, max_steps, visited_states
                    )
                    if result is not None:
                        return result

                # Backtrack: restore state.
                self._assertions = old_assertions

        # No relevant action worked for target_goal directly.
        # Try ANY applicable action (breadth of search) -- this handles
        # cases where we need to clear the way (e.g., unstack a block
        # that is in the way, even though that action doesn't directly
        # achieve any current goal).
        for action in self._actions:
            for gb in self._enumerate_groundings(action, {}):
                # Skip if this wouldn't change anything useful.
                grounded_add = [substitute(e, gb) for e in action.add_effects]
                if all(a in self._assertions for a in grounded_add):
                    continue  # Action adds nothing new.

                old_assertions = list(self._assertions)
                self.save_state(description=f"before {action.name} {gb}")

                if self.apply_action(action, gb):
                    new_plan = plan_so_far + [(action.name, dict(gb))]
                    result = self._plan_search(
                        goals, new_plan, depth + 1, max_steps, visited_states
                    )
                    if result is not None:
                        return result

                self._assertions = old_assertions

        return None  # No plan found from this state.

    def _relevant_actions(
        self, goal: tuple
    ) -> List[Tuple[Action, Dict[str, Any]]]:
        """
        Find actions with an add-effect that unifies with *goal*.
        Returns (action, partial_bindings) pairs.
        """
        results = []
        for action in self._actions:
            for add_effect in action.add_effects:
                bindings = Unifier.match(add_effect, goal)
                if bindings is not None:
                    results.append((action, bindings))
        return results

    def _enumerate_groundings(
        self, action: Action, seed_bindings: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Enumerate all fully-ground instantiations of *action* consistent
        with *seed_bindings*, by matching preconditions against the database.

        If preconditions contain variables not bound by seed_bindings,
        we find all database facts that could bind them.
        """
        unbound = [p for p in action.parameters if p not in seed_bindings]
        if not unbound:
            return [dict(seed_bindings)]

        # Use preconditions to bind remaining variables.
        pres = [substitute(p, seed_bindings) for p in action.preconditions]
        return list(self.prove_all(pres, seed_bindings))


# ---------------------------------------------------------------------------
# Blocks World
# ---------------------------------------------------------------------------

class BlocksWorld:
    """
    A SHRDLU-style blocks world built on top of PlannerDatabase.

    The world consists of blocks (named by single uppercase letters) that
    can be stacked on each other or placed on the table.  The database
    tracks:

      - ``("on", X, Y)``     -- block X is directly on block Y
      - ``("on-table", X)``  -- block X is on the table
      - ``("clear", X)``     -- nothing is on top of block X
      - ``("holding", X)``   -- the robot arm is holding block X
      - ``("arm-empty",)``   -- the robot arm is empty

    Actions:
      - **pick-up**: pick up a clear block from the table
      - **put-down**: put a held block on the table
      - **stack**: put a held block on top of a clear block
      - **unstack**: pick up a clear block from on top of another block

    These are the classic four operators from the STRIPS blocks world,
    exactly as described in Nilsson's "Principles of AI" (1980).
    """

    def __init__(self, backtrack_type: BacktrackType = BacktrackType.CHRONOLOGICAL):
        self.db = PlannerDatabase(backtrack_type=backtrack_type)
        self._define_actions()
        self._define_antecedent_theorems()
        self._define_consequent_theorems()

    @property
    def trace(self) -> bool:
        return self.db._trace

    @trace.setter
    def trace(self, value: bool) -> None:
        self.db._trace = value

    # -- World setup --------------------------------------------------------

    def setup(self, on_table: List[str], stacks: List[List[str]]) -> None:
        """
        Initialize the blocks world.

        *on_table* is a list of lone blocks sitting on the table.
        *stacks* is a list of bottom-to-top stacks, e.g.
        ``[["A", "B", "C"]]`` means A is on the table, B is on A,
        C is on B, and C is clear.
        """
        # Clear existing state.
        self.db._assertions.clear()
        self.db.assert_fact("arm-empty")

        all_blocks: Set[str] = set(on_table)

        for block in on_table:
            self.db.assert_fact("on-table", block)
            self.db.assert_fact("clear", block)

        for stack in stacks:
            if not stack:
                continue
            bottom = stack[0]
            self.db.assert_fact("on-table", bottom)
            all_blocks.add(bottom)
            for i in range(1, len(stack)):
                self.db.assert_fact("on", stack[i], stack[i - 1])
                all_blocks.add(stack[i])
            top = stack[-1]
            self.db.assert_fact("clear", top)
            # Everything below top is NOT clear (implicit closed world).

        for block in all_blocks:
            self.db.assert_fact("block", block)

    # -- Action definitions -------------------------------------------------

    def _define_actions(self) -> None:
        self.db.add_action(Action(
            name="pick-up",
            parameters=["?block"],
            preconditions=[
                ("on-table", "?block"),
                ("clear", "?block"),
                ("arm-empty",),
            ],
            add_effects=[("holding", "?block")],
            delete_effects=[
                ("on-table", "?block"),
                ("clear", "?block"),
                ("arm-empty",),
            ],
        ))

        self.db.add_action(Action(
            name="put-down",
            parameters=["?block"],
            preconditions=[("holding", "?block")],
            add_effects=[
                ("on-table", "?block"),
                ("clear", "?block"),
                ("arm-empty",),
            ],
            delete_effects=[("holding", "?block")],
        ))

        self.db.add_action(Action(
            name="stack",
            parameters=["?block", "?onto"],
            preconditions=[
                ("holding", "?block"),
                ("clear", "?onto"),
            ],
            add_effects=[
                ("on", "?block", "?onto"),
                ("clear", "?block"),
                ("arm-empty",),
            ],
            delete_effects=[
                ("holding", "?block"),
                ("clear", "?onto"),
            ],
        ))

        self.db.add_action(Action(
            name="unstack",
            parameters=["?block", "?from"],
            preconditions=[
                ("on", "?block", "?from"),
                ("clear", "?block"),
                ("arm-empty",),
            ],
            add_effects=[
                ("holding", "?block"),
                ("clear", "?from"),
            ],
            delete_effects=[
                ("on", "?block", "?from"),
                ("clear", "?block"),
                ("arm-empty",),
            ],
        ))

    # -- Antecedent theorems ------------------------------------------------

    def _define_antecedent_theorems(self) -> None:
        """
        Backward-chaining rules for the blocks world.

        These encode knowledge like: "to prove (on ?x ?y), check if it's
        already true, and if not, find an action that achieves it."
        """

        def prove_above(db: PlannerDatabase, bindings: dict, depth: int) -> Iterator[dict]:
            """To prove (above ?x ?y): ?x is on ?y, or ?x is on ?z and ?z is above ?y."""
            x = bindings["?x"]
            y = bindings["?y"]

            # Direct: x is directly on y.
            if db.holds("on", x, y):
                yield bindings

            # Transitive: x is on some z, and z is above y.
            for fact in db.all_facts():
                if len(fact) == 3 and fact[0] == "on" and fact[1] == x:
                    z = fact[2]
                    # Recursively check if z is above y.
                    for _ in db.prove(("above", z, y), {}, depth + 1):
                        yield bindings

        self.db.add_antecedent_theorem(AntecedentTheorem(
            name="above-transitive",
            goal_pattern=("above", "?x", "?y"),
            body=prove_above,
        ))

        def prove_on_table_or_supported(db: PlannerDatabase, bindings: dict, depth: int) -> Iterator[dict]:
            """To prove (supported ?x): either on-table or on something supported."""
            x = bindings["?x"]

            # Base case: directly on the table.
            if db.holds("on-table", x):
                yield bindings
                return

            # Recursive: on something that is itself supported.
            for fact in db.all_facts():
                if len(fact) == 3 and fact[0] == "on" and fact[1] == x:
                    y = fact[2]
                    for _ in db.prove(("supported", y), {}, depth + 1):
                        yield bindings
                        return  # One proof suffices.

        self.db.add_antecedent_theorem(AntecedentTheorem(
            name="supported-recursive",
            goal_pattern=("supported", "?x"),
            body=prove_on_table_or_supported,
        ))

    # -- Consequent theorems ------------------------------------------------

    def _define_consequent_theorems(self) -> None:
        """
        Forward-chaining rules that fire when facts are asserted.
        """

        def on_holding_clear_arm(db: PlannerDatabase, bindings: dict) -> None:
            """When we start holding a block, arm is no longer empty."""
            # This is handled by action effects, but we include it as
            # an example of the consequent theorem mechanism.
            pass

        self.db.add_consequent_theorem(ConsequentTheorem(
            name="holding-implies-not-arm-empty",
            pattern=("holding", "?block"),
            action=on_holding_clear_arm,
        ))

    # -- High-level interface -----------------------------------------------

    def show(self) -> str:
        """Return a human-readable representation of the current state."""
        lines = []
        facts = sorted(self.db.all_facts())

        # Find stacks.
        on_table_blocks = [f[1] for f in facts if f[0] == "on-table"]
        on_pairs = {f[1]: f[2] for f in facts if f[0] == "on" and len(f) == 3}
        holding = [f[1] for f in facts if f[0] == "holding"]

        # Build stacks from bottom up.
        # on_pairs maps block -> what_its_on; invert to get what_its_on -> block
        above_map: Dict[str, str] = {}
        for blk, base in on_pairs.items():
            above_map[base] = blk

        stacks = []
        for base in sorted(on_table_blocks):
            stack = [base]
            current = base
            while current in above_map:
                current = above_map[current]
                stack.append(current)
            stacks.append(stack)

        # Render.
        if holding:
            lines.append(f"  Holding: {', '.join(holding)}")
        if self.db.holds("arm-empty"):
            lines.append("  Arm: empty")

        if stacks:
            max_height = max(len(s) for s in stacks)
            for level in range(max_height - 1, -1, -1):
                row_parts = []
                for stack in stacks:
                    if level < len(stack):
                        row_parts.append(f"[{stack[level]}]")
                    else:
                        row_parts.append("   ")
                lines.append("  " + "  ".join(row_parts))
            lines.append("  " + "---" * len(stacks) + "-")

        return "\n".join(lines)

    def achieve(self, goals: List[tuple], max_steps: int = 100) -> Optional[List[Tuple[str, Dict[str, Any]]]]:
        """
        Find and execute a plan to achieve the given goals.

        Returns the plan (list of (action_name, bindings) pairs) on success,
        or None on failure.
        """
        # Save state so we can plan non-destructively, then replay.
        original_assertions = list(self.db._assertions)

        plan = self.db.plan(goals, max_steps=max_steps)

        if plan is None:
            self.db._assertions = original_assertions
            return None

        # Replay plan on original state.
        self.db._assertions = original_assertions
        executed_plan = []
        for action_name, bindings in plan:
            action = self.db.get_action(action_name)
            if action is None:
                return None
            success = self.db.apply_action(action, bindings)
            if not success:
                return None
            executed_plan.append((action_name, bindings))

        return executed_plan

    def query_above(self, x: str, y: str) -> bool:
        """Query whether block *x* is anywhere above block *y*."""
        results = list(self.db.prove(("above", x, y)))
        return len(results) > 0

    def query_supported(self, x: str) -> bool:
        """Query whether block *x* is transitively supported by the table."""
        results = list(self.db.prove(("supported", x)))
        return len(results) > 0


# ---------------------------------------------------------------------------
# Demonstration
# ---------------------------------------------------------------------------

def demo() -> None:
    """
    Run a demonstration of the blocks world planner.

    Recreates a simplified version of the kind of interaction Winograd
    demonstrated with SHRDLU in 1971 -- but using explicit plan generation
    rather than natural language parsing.
    """
    print("=" * 68)
    print("PLANNER/SHRDLU Blocks World Demonstration")
    print("=" * 68)
    print()
    print("Inspired by Carl Hewitt's PLANNER (MIT, 1969) and")
    print("Terry Winograd's SHRDLU (MIT, 1971).")
    print()

    world = BlocksWorld()

    # Initial state:
    #   [C]
    #   [B]
    #   [A]  [D]
    #   ---------
    world.setup(on_table=["D"], stacks=[["A", "B", "C"]])

    print("Initial state:")
    print(world.show())
    print()

    # --- Backward chaining demo ---
    print("--- Backward Chaining (Antecedent Theorems) ---")
    print()
    print("Query: Is C above A?")
    result = world.query_above("C", "A")
    print(f"  Answer: {result}")
    print()

    print("Query: Is A above C?")
    result = world.query_above("A", "C")
    print(f"  Answer: {result}")
    print()

    print("Query: Is B supported (transitively on the table)?")
    result = world.query_supported("B")
    print(f"  Answer: {result}")
    print()

    # --- Pattern matching demo ---
    print("--- Pattern-Directed Retrieval ---")
    print()
    print("Query: What is on top of A?  pattern = ('on', '?x', 'A')")
    for bindings in world.db.query(("on", "?x", "A")):
        print(f"  ?x = {bindings['?x']}")
    print()

    print("Query: What is clear?  pattern = ('clear', '?x')")
    for bindings in world.db.query(("clear", "?x")):
        print(f"  ?x = {bindings['?x']}")
    print()

    # --- Planning demo ---
    print("--- Goal-Directed Planning ---")
    print()

    # Goal: put A on D  (requires unstacking C, then B, from on top of A)
    goal = [("on", "A", "D")]
    print(f"Goal: {goal}")
    print("  (This requires unstacking C and B from A first.)")
    print()

    plan = world.achieve(goal)
    if plan:
        print("Plan found:")
        for i, (action_name, bindings) in enumerate(plan, 1):
            params = ", ".join(f"{k}={v}" for k, v in bindings.items() if k.startswith("?"))
            print(f"  Step {i}: {action_name}({params})")
        print()
        print("State after executing plan:")
        print(world.show())
    else:
        print("No plan found!")
    print()

    # --- Forward chaining demo ---
    print("--- Forward Chaining (Consequent Theorems) ---")
    print()
    print("Adding a consequent theorem: when ('on', ?x, ?y) is asserted,")
    print("also assert ('above', ?x, ?y) as a cached fact.")

    def cache_above(db: PlannerDatabase, bindings: dict) -> None:
        x = bindings.get("?x")
        y = bindings.get("?y")
        if x and y:
            db.assert_fact("above-cached", x, y)

    world.db.add_consequent_theorem(ConsequentTheorem(
        name="cache-above",
        pattern=("on", "?x", "?y"),
        action=cache_above,
    ))

    # Stack E on something to trigger the consequent theorem.
    world.db.assert_fact("block", "E")
    world.db.assert_fact("on-table", "E")
    world.db.assert_fact("clear", "E")

    goal2 = [("on", "E", "C")]
    print(f"New goal: {goal2}")
    plan2 = world.achieve(goal2)
    if plan2:
        print("Plan found:")
        for i, (action_name, bindings) in enumerate(plan2, 1):
            params = ", ".join(f"{k}={v}" for k, v in bindings.items() if k.startswith("?"))
            print(f"  Step {i}: {action_name}({params})")
        print()
        # Check if consequent theorem fired.
        if world.db.holds("above-cached", "E", "C"):
            print("Consequent theorem fired: ('above-cached', 'E', 'C') is now in DB.")
        print()
        print("Final state:")
        print(world.show())
    else:
        print("No plan found!")
    print()

    # --- Backtracking demo ---
    print("--- Backtracking ---")
    print()
    print("Demonstrating chronological backtracking:")

    world2 = BlocksWorld()
    #   [B]
    #   [A]  [C]
    #   ---------
    world2.setup(on_table=["C"], stacks=[["A", "B"]])
    print("Initial state:")
    print(world2.show())
    print()

    # Goal: C on A and B on C  (a complete restack)
    goal3 = [("on", "B", "C"), ("on", "C", "A")]
    print(f"Goal: {goal3}")
    print("  (Requires careful ordering: unstack B from A, put B down,")
    print("   pick up C, stack C on A, pick up B, stack B on C.)")
    print()

    plan3 = world2.achieve(goal3)
    if plan3:
        print("Plan found:")
        for i, (action_name, bindings) in enumerate(plan3, 1):
            params = ", ".join(f"{k}={v}" for k, v in bindings.items() if k.startswith("?"))
            print(f"  Step {i}: {action_name}({params})")
        print()
        print("Final state:")
        print(world2.show())
    else:
        print("No plan found!")

    print()
    print("=" * 68)
    print("End of demonstration.")
    print("=" * 68)


if __name__ == "__main__":
    demo()
