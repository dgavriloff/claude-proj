"""
IPL -- Information Processing Language (1956)
=============================================

A Python module implementing the core ideas from the **first list-processing
language ever created**, developed by Allen Newell, Cliff Shaw, and Herbert
A. Simon at the RAND Corporation in 1956.

Historical Background
---------------------

In the mid-1950s, Newell, Shaw, and Simon set out to build a program that
could prove theorems in symbolic logic -- what they called the **Logic
Theorist**.  They needed a language that could manipulate symbolic
expressions, build and traverse linked structures, and support recursive
problem-solving.  No such language existed.  Fortran (1957) was still being
developed and dealt only with numbers.  So they invented one.

**IPL (Information Processing Language)** was first implemented on the RAND
JOHNNIAC computer.  Its key innovations were:

* **Linked lists** as a first-class data structure.  Memory was organized as
  numbered cells, each containing a *symbol* (datum) and a *link* (pointer
  to the next cell).  This was the birth of the linked list in computing.

* **List-processing primitives** -- operations to take the head of a list,
  the tail, to prepend an element (what Lisp later called ``car``, ``cdr``,
  and ``cons``).  IPL called these by numeric routine codes (J1 for "get
  symbol from cell", J2 for "get link", J3 for "set symbol", etc.).

* **Association lists / description lists** -- every symbol could carry a
  *property list* of attribute-value pairs.  This idea passed directly into
  Lisp's property lists and influenced object-oriented programming.

* **Recursive subroutines** -- IPL was among the first systems to use a
  push-down stack for subroutine calls, enabling recursion.  The concept
  was radical; most programmers of the era avoided recursion entirely.

* **Generators** -- IPL introduced a *generator* mechanism: a routine that
  could produce a sequence of values one at a time, suspending and resuming
  its state.  This anticipated Python generators (2001) and coroutines by
  nearly half a century.

* **Symbol manipulation as computation** -- the idea that intelligence
  could be modeled by manipulating discrete symbols, not just crunching
  numbers.  This became the foundation of the "Physical Symbol System
  Hypothesis" (Newell & Simon, 1976).

The Logic Theorist
------------------

The **Logic Theorist** (1956) was the world's first artificial intelligence
program.  Running on IPL, it attempted to prove the theorems of propositional
calculus from Whitehead and Russell's *Principia Mathematica* (1910-1913).

The program succeeded in proving **38 of the first 52 theorems** in Chapter 2
of *Principia Mathematica*.  For Theorem 2.85, it found a proof that was
shorter and more elegant than Russell and Whitehead's own -- Simon reportedly
tried (unsuccessfully) to get the *Journal of Symbolic Logic* to accept a
co-authored paper with the program.

The Logic Theorist used three principal methods:

1. **Substitution** -- replacing variables in an axiom or proven theorem
   with specific expressions to match a target.
2. **Detachment (Modus Ponens)** -- if ``A`` and ``A => B`` are both
   proven, conclude ``B``.
3. **Chaining** -- forward and backward chaining through implications
   to connect known truths to the target theorem.

The program was demonstrated at the 1956 Dartmouth Conference, the founding
event of artificial intelligence as a field.

Influence on Lisp
-----------------

John McCarthy, who created **Lisp** in 1958, explicitly acknowledged IPL's
influence.  In his 1978 "History of Lisp" paper, McCarthy wrote that IPL's
linked lists and list-processing operations were a direct inspiration.
However, McCarthy found IPL's low-level, assembly-like notation cumbersome
and sought a higher-level, mathematically cleaner formalism.  This led him
to adopt:

* S-expressions (symbolic expressions) instead of numbered cells
* ``car`` / ``cdr`` / ``cons`` as primitives (named after IBM 704 registers)
* Lambda calculus as the theoretical foundation
* Garbage collection instead of IPL's explicit free-list management

IPL went through several versions (IPL-I through IPL-V, with IPL-V being
the most widely used), but it was ultimately eclipsed by Lisp.  Nevertheless,
IPL's ideas live on in every language that supports linked lists, property
lists, generators, or symbolic computation.

Newell and Simon went on to develop the **General Problem Solver** (1959),
and both received the ACM Turing Award in 1975 for their "basic contributions
to artificial intelligence, the psychology of human cognition, and list
processing."  Cliff Shaw, a systems programmer at RAND, was the principal
implementer of IPL and the Logic Theorist, though he is less remembered
because the Turing Award was limited to two recipients.

This Module
-----------

This module provides a faithful (if modernized) implementation of IPL's
core concepts:

* :class:`Memory` -- cell-based memory with numbered addresses
* :class:`IPLList` -- linked list with head/tail/cons/append/reverse/map/filter
* :class:`AssociationStore` -- symbol property lists (description lists)
* :class:`Generator` -- lazy value production via coroutines
* :class:`PatternMatcher` -- symbolic pattern matching
* :class:`Logictheorist` -- a propositional-logic theorem prover using
  substitution, detachment, and chaining, in the spirit of the original
  Logic Theorist

Only the Python standard library is used.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Generator as GenType,
    Hashable,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)


# ---------------------------------------------------------------------------
# 1. Cell-based memory system
# ---------------------------------------------------------------------------

@dataclass
class Cell:
    """
    A single memory cell, mirroring IPL's fundamental storage unit.

    In the original IPL, every cell had three fields:

    * **P** (prefix) -- a tag indicating the cell type
    * **Q** (symbol) -- the datum stored in the cell
    * **LINK** -- pointer to the next cell (forming a linked list)

    We keep *symbol* and *link*, and add an *address* assigned by
    :class:`Memory`.
    """

    address: int
    symbol: Any = None
    link: Optional[int] = None  # address of next cell, or None

    def __repr__(self) -> str:
        link_repr = self.link if self.link is not None else "NIL"
        return f"Cell({self.address}: {self.symbol!r} -> {link_repr})"


class Memory:
    """
    A cell-addressed memory store, inspired by IPL's numbered-cell architecture.

    IPL programs operated on a flat array of cells identified by integer
    addresses.  Free cells were kept on a special *available-space list*
    (what we now call a free list).  Allocation meant popping from this list;
    deallocation meant pushing back onto it.

    Usage::

        mem = Memory(size=1024)
        a = mem.allocate("hello")
        b = mem.allocate("world", link=a)
        print(mem[b])          # Cell(1: 'world' -> 0)
        print(mem.get_symbol(b))  # 'world'
        mem.free(a)
    """

    def __init__(self, size: int = 4096) -> None:
        self._cells: Dict[int, Cell] = {}
        self._next_address: int = 0
        self._free: List[int] = []
        self.size = size

    # -- allocation --------------------------------------------------------

    def allocate(self, symbol: Any = None, link: Optional[int] = None) -> int:
        """Allocate a cell, returning its address."""
        if self._free:
            addr = self._free.pop()
            cell = Cell(address=addr, symbol=symbol, link=link)
            self._cells[addr] = cell
        else:
            if self._next_address >= self.size:
                raise MemoryError("IPL memory exhausted")
            addr = self._next_address
            self._next_address += 1
            cell = Cell(address=addr, symbol=symbol, link=link)
            self._cells[addr] = cell
        return addr

    def free(self, address: int) -> None:
        """Return a cell to the free list."""
        if address in self._cells:
            del self._cells[address]
            self._free.append(address)

    # -- access ------------------------------------------------------------

    def __getitem__(self, address: int) -> Cell:
        return self._cells[address]

    def get_symbol(self, address: int) -> Any:
        """IPL's J1 routine: fetch the symbol field of a cell."""
        return self._cells[address].symbol

    def get_link(self, address: int) -> Optional[int]:
        """IPL's J2 routine: fetch the link field of a cell."""
        return self._cells[address].link

    def set_symbol(self, address: int, value: Any) -> None:
        """IPL's J3 routine: set the symbol field."""
        self._cells[address].symbol = value

    def set_link(self, address: int, link: Optional[int]) -> None:
        """IPL's J4 routine: set the link field."""
        self._cells[address].link = link

    # -- diagnostics -------------------------------------------------------

    def allocated_count(self) -> int:
        return len(self._cells)

    def free_count(self) -> int:
        return self.size - self._next_address + len(self._free)

    def dump(self, address: int, max_cells: int = 20) -> List[Cell]:
        """Walk a linked list starting at *address*, returning cells."""
        result: List[Cell] = []
        cur: Optional[int] = address
        seen: Set[int] = set()
        while cur is not None and cur in self._cells and len(result) < max_cells:
            if cur in seen:
                break  # cycle detection
            seen.add(cur)
            result.append(self._cells[cur])
            cur = self._cells[cur].link
        return result


# ---------------------------------------------------------------------------
# 2. Linked-list operations
# ---------------------------------------------------------------------------

class IPLList:
    """
    A linked list built on top of :class:`Memory`, providing the operations
    that IPL pioneered and that Lisp later adopted.

    IPL's core list operations (numbered J-routines) map to familiar names:

    =========  ==========  ===========================================
    IPL        Lisp         This class
    =========  ==========  ===========================================
    J1 (sym)   ``car``     :meth:`head`
    J2 (link)  ``cdr``     :meth:`tail`
    J5 (push)  ``cons``    :meth:`cons`
    =========  ==========  ===========================================

    Usage::

        mem = Memory()
        lst = IPLList(mem)

        a = lst.from_sequence([1, 2, 3, 4, 5])
        print(lst.head(a))        # 1
        print(lst.to_list(a))     # [1, 2, 3, 4, 5]

        b = lst.cons(0, a)
        print(lst.to_list(b))     # [0, 1, 2, 3, 4, 5]

        c = lst.reverse(a)
        print(lst.to_list(c))     # [5, 4, 3, 2, 1]
    """

    def __init__(self, memory: Optional[Memory] = None) -> None:
        self.mem = memory or Memory()

    # -- constructors ------------------------------------------------------

    def empty(self) -> None:
        """The empty list is represented as ``None`` (no cell)."""
        return None

    def cons(self, symbol: Any, rest: Optional[int] = None) -> int:
        """
        Prepend *symbol* to the list beginning at *rest*.

        This is IPL's J5 routine and Lisp's ``cons``.
        """
        return self.mem.allocate(symbol=symbol, link=rest)

    def from_sequence(self, items: Sequence[Any]) -> Optional[int]:
        """Build a linked list from a Python sequence (preserving order)."""
        head: Optional[int] = None
        for item in reversed(items):
            head = self.cons(item, head)
        return head

    # -- accessors ---------------------------------------------------------

    def head(self, address: int) -> Any:
        """
        Return the first element (IPL's J1 / Lisp's ``car``).
        """
        return self.mem.get_symbol(address)

    def tail(self, address: int) -> Optional[int]:
        """
        Return the rest of the list (IPL's J2 / Lisp's ``cdr``).

        Returns ``None`` for a single-element list.
        """
        return self.mem.get_link(address)

    def is_empty(self, address: Optional[int]) -> bool:
        return address is None

    def length(self, address: Optional[int]) -> int:
        n = 0
        cur = address
        while cur is not None:
            n += 1
            cur = self.mem.get_link(cur)
        return n

    def nth(self, address: Optional[int], n: int) -> Any:
        """Return the *n*-th element (0-indexed)."""
        cur = address
        for _ in range(n):
            if cur is None:
                raise IndexError(f"list index {n} out of range")
            cur = self.mem.get_link(cur)
        if cur is None:
            raise IndexError(f"list index {n} out of range")
        return self.mem.get_symbol(cur)

    # -- conversion --------------------------------------------------------

    def to_list(self, address: Optional[int]) -> List[Any]:
        """Collect all symbols into a Python list."""
        result: List[Any] = []
        cur = address
        while cur is not None:
            result.append(self.mem.get_symbol(cur))
            cur = self.mem.get_link(cur)
        return result

    def __iter_addrs(self, address: Optional[int]) -> Iterator[int]:
        cur = address
        while cur is not None:
            yield cur
            cur = self.mem.get_link(cur)

    # -- higher-order operations -------------------------------------------

    def append(self, a: Optional[int], b: Optional[int]) -> Optional[int]:
        """
        Non-destructively append list *b* to list *a*.
        """
        if a is None:
            return b
        items = self.to_list(a)
        result = b
        for item in reversed(items):
            result = self.cons(item, result)
        return result

    def reverse(self, address: Optional[int]) -> Optional[int]:
        """Return a new reversed copy of the list."""
        result: Optional[int] = None
        cur = address
        while cur is not None:
            result = self.cons(self.mem.get_symbol(cur), result)
            cur = self.mem.get_link(cur)
        return result

    def map(self, address: Optional[int], fn: Callable[[Any], Any]) -> Optional[int]:
        """Apply *fn* to every element, returning a new list."""
        items = [fn(x) for x in self.to_list(address)]
        return self.from_sequence(items)

    def filter(self, address: Optional[int], pred: Callable[[Any], bool]) -> Optional[int]:
        """Keep only elements satisfying *pred*, returning a new list."""
        items = [x for x in self.to_list(address) if pred(x)]
        return self.from_sequence(items)

    def foldl(self, address: Optional[int], fn: Callable[[Any, Any], Any], init: Any) -> Any:
        """Left fold over the list."""
        acc = init
        cur = address
        while cur is not None:
            acc = fn(acc, self.mem.get_symbol(cur))
            cur = self.mem.get_link(cur)
        return acc

    def member(self, address: Optional[int], value: Any) -> bool:
        """Return True if *value* is an element of the list."""
        cur = address
        while cur is not None:
            if self.mem.get_symbol(cur) == value:
                return True
            cur = self.mem.get_link(cur)
        return False

    def copy(self, address: Optional[int]) -> Optional[int]:
        """Return a fresh copy of the list."""
        return self.from_sequence(self.to_list(address))


# ---------------------------------------------------------------------------
# 3. Association lists / property lists (description lists)
# ---------------------------------------------------------------------------

class AssociationStore:
    """
    IPL's *description lists* -- every symbol can have a list of
    attribute-value pairs attached to it.

    In IPL, any list could carry a "description list" that recorded
    properties of the symbol.  For example, a symbol representing a
    logical proposition might have properties like ``type=implies``,
    ``antecedent=P``, ``consequent=Q``.

    This passed directly into Lisp's *property lists* (``get`` / ``putprop``
    / ``remprop``) and later into object-attribute models generally.

    Usage::

        store = AssociationStore()
        store.put("socrates", "species", "human")
        store.put("socrates", "occupation", "philosopher")
        print(store.get("socrates", "species"))        # 'human'
        print(store.properties("socrates"))             # {'species': 'human', ...}
    """

    def __init__(self) -> None:
        self._store: Dict[Hashable, Dict[Hashable, Any]] = {}

    def put(self, symbol: Hashable, attribute: Hashable, value: Any) -> None:
        """Attach *attribute* = *value* to *symbol*."""
        if symbol not in self._store:
            self._store[symbol] = {}
        self._store[symbol][attribute] = value

    def get(self, symbol: Hashable, attribute: Hashable, default: Any = None) -> Any:
        """Retrieve the value of *attribute* on *symbol*."""
        return self._store.get(symbol, {}).get(attribute, default)

    def has(self, symbol: Hashable, attribute: Hashable) -> bool:
        return symbol in self._store and attribute in self._store[symbol]

    def remove(self, symbol: Hashable, attribute: Hashable) -> None:
        if symbol in self._store:
            self._store[symbol].pop(attribute, None)

    def properties(self, symbol: Hashable) -> Dict[Hashable, Any]:
        """Return a copy of all properties for *symbol*."""
        return dict(self._store.get(symbol, {}))

    def symbols(self) -> List[Hashable]:
        return list(self._store.keys())

    def find(self, attribute: Hashable, value: Any) -> List[Hashable]:
        """Find all symbols where *attribute* equals *value*."""
        return [
            sym
            for sym, props in self._store.items()
            if props.get(attribute) == value
        ]

    def dump(self) -> Dict[Hashable, Dict[Hashable, Any]]:
        return {k: dict(v) for k, v in self._store.items()}


# ---------------------------------------------------------------------------
# 4. Generator / coroutine system
# ---------------------------------------------------------------------------

class Generator:
    """
    IPL's *generator* concept -- a routine that produces a sequence of values
    lazily, suspending after each one.

    IPL generators were a remarkable anticipation of modern coroutines and
    Python generators.  An IPL generator would be invoked repeatedly; each
    invocation resumed it where it left off, and it yielded the next value.
    A special "quit" signal indicated exhaustion.

    This class wraps a Python generator function and provides an IPL-like
    interface with ``next()``, ``has_next()``, and iteration.

    Usage::

        @generator
        def count_up(start, stop):
            i = start
            while i < stop:
                yield i
                i += 1

        g = count_up(1, 5)
        while g.has_next():
            print(g.next())   # 1, 2, 3, 4
    """

    def __init__(self, gen_fn: Callable[..., GenType], *args: Any, **kwargs: Any) -> None:
        self._gen: GenType = gen_fn(*args, **kwargs)
        self._buffer: List[Any] = []
        self._exhausted: bool = False

    def _advance(self) -> None:
        if not self._exhausted and not self._buffer:
            try:
                self._buffer.append(next(self._gen))
            except StopIteration:
                self._exhausted = True

    def has_next(self) -> bool:
        self._advance()
        return bool(self._buffer)

    def next(self) -> Any:
        """Return the next value, or raise ``StopIteration``."""
        self._advance()
        if self._buffer:
            return self._buffer.pop(0)
        raise StopIteration("generator exhausted")

    def take(self, n: int) -> List[Any]:
        """Take up to *n* values."""
        result: List[Any] = []
        for _ in range(n):
            if not self.has_next():
                break
            result.append(self.next())
        return result

    def to_list(self) -> List[Any]:
        """Drain the generator into a list (careful with infinite generators)."""
        result: List[Any] = []
        while self.has_next():
            result.append(self.next())
        return result

    def __iter__(self) -> Iterator[Any]:
        while self.has_next():
            yield self.next()

    def __next__(self) -> Any:
        return self.next()


def generator(fn: Callable[..., GenType]) -> Callable[..., Generator]:
    """
    Decorator that turns a Python generator function into an IPL-style
    :class:`Generator` factory.

    Usage::

        @generator
        def fibonacci():
            a, b = 0, 1
            while True:
                yield a
                a, b = b, a + b

        fib = fibonacci()
        print(fib.take(10))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    """

    def wrapper(*args: Any, **kwargs: Any) -> Generator:
        return Generator(fn, *args, **kwargs)

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


# ---------------------------------------------------------------------------
# 5. Symbolic expressions and pattern matcher
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Expr:
    """
    A symbolic expression for propositional logic.

    Every expression is a tree.  Leaf nodes have ``op`` set to a variable
    name (like ``"p"``, ``"q"``) and no ``args``.  Internal nodes have an
    ``op`` like ``"=>"``, ``"~"``, ``"|"``, ``"&"`` and one or two children
    in ``args``.

    This mirrors how IPL stored logical propositions as nested list
    structures in memory.
    """

    op: str
    args: Tuple["Expr", ...] = ()

    @property
    def is_var(self) -> bool:
        return len(self.args) == 0

    def __repr__(self) -> str:
        if self.is_var:
            return self.op
        if self.op == "~" and len(self.args) == 1:
            child = self.args[0]
            if child.is_var:
                return f"~{child}"
            return f"~({child})"
        if len(self.args) == 2:
            left, right = self.args
            return f"({left} {self.op} {right})"
        return f"{self.op}({', '.join(repr(a) for a in self.args)})"

    def variables(self) -> Set[str]:
        """Return all variable names occurring in this expression."""
        if self.is_var:
            return {self.op}
        result: Set[str] = set()
        for a in self.args:
            result |= a.variables()
        return result

    def substitute(self, bindings: Dict[str, "Expr"]) -> "Expr":
        """
        Replace variables according to *bindings*.

        This is IPL's substitution operation -- the Logic Theorist's
        primary inference mechanism.
        """
        if self.is_var:
            return bindings.get(self.op, self)
        return Expr(self.op, tuple(a.substitute(bindings) for a in self.args))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Expr):
            return NotImplemented
        return self.op == other.op and self.args == other.args

    def __hash__(self) -> int:
        return hash((self.op, self.args))


# -- convenience constructors ------------------------------------------------

def var(name: str) -> Expr:
    """Create a propositional variable."""
    return Expr(name)


def implies(a: Expr, b: Expr) -> Expr:
    """``a => b``"""
    return Expr("=>", (a, b))


def neg(a: Expr) -> Expr:
    """``~a``"""
    return Expr("~", (a,))


def lor(a: Expr, b: Expr) -> Expr:
    """``a | b`` (logical or)."""
    return Expr("|", (a, b))


def land(a: Expr, b: Expr) -> Expr:
    """``a & b`` (logical and)."""
    return Expr("&", (a, b))


def axiom(expr: Expr) -> Expr:
    """Marker -- just returns the expression (for readability)."""
    return expr


# -- pattern matching --------------------------------------------------------

class PatternMatcher:
    """
    A simple pattern matcher for symbolic expressions.

    Patterns are :class:`Expr` trees where certain variables act as
    *pattern variables* (wildcards).  The matcher attempts to find a
    substitution (binding of pattern variables to sub-expressions) that
    makes the pattern identical to a target expression.

    This is a unification-like operation that the Logic Theorist used
    when trying to match axioms against goals.

    Usage::

        pm = PatternMatcher()
        p, q = var("p"), var("q")
        pattern = implies(p, q)          # p => q
        target = implies(var("A"), var("B"))  # A => B
        bindings = pm.match(pattern, target, pattern_vars={"p", "q"})
        # => {"p": A, "q": B}
    """

    def match(
        self,
        pattern: Expr,
        target: Expr,
        pattern_vars: Optional[Set[str]] = None,
        bindings: Optional[Dict[str, Expr]] = None,
    ) -> Optional[Dict[str, Expr]]:
        """
        Try to match *pattern* against *target*.

        *pattern_vars* names the variables in *pattern* that are wildcards.
        Returns a dict of bindings on success, or ``None`` on failure.
        """
        if pattern_vars is None:
            pattern_vars = set()
        if bindings is None:
            bindings = {}

        return self._match(pattern, target, pattern_vars, dict(bindings))

    def _match(
        self,
        pattern: Expr,
        target: Expr,
        pvars: Set[str],
        bindings: Dict[str, Expr],
    ) -> Optional[Dict[str, Expr]]:
        # Pattern variable -- try to bind
        if pattern.is_var and pattern.op in pvars:
            if pattern.op in bindings:
                # Already bound -- must match consistently
                if bindings[pattern.op] == target:
                    return bindings
                return None
            bindings[pattern.op] = target
            return bindings

        # Structural match
        if pattern.op != target.op:
            return None
        if len(pattern.args) != len(target.args):
            return None
        if pattern.is_var and target.is_var:
            # Both are concrete variables (non-pattern) -- must be same name
            return bindings

        for pa, ta in zip(pattern.args, target.args):
            result = self._match(pa, ta, pvars, bindings)
            if result is None:
                return None
            bindings = result
        return bindings

    def unify(
        self, a: Expr, b: Expr, a_vars: Set[str], b_vars: Set[str]
    ) -> Optional[Dict[str, Expr]]:
        """
        Symmetric unification: variables in *a_vars* and *b_vars* are
        both treated as wildcards.

        Returns combined bindings or ``None``.
        """
        all_vars = a_vars | b_vars
        return self._unify(a, b, all_vars, {})

    def _unify(
        self,
        a: Expr,
        b: Expr,
        uvars: Set[str],
        bindings: Dict[str, Expr],
    ) -> Optional[Dict[str, Expr]]:
        a = self._apply(a, bindings)
        b = self._apply(b, bindings)

        if a == b:
            return bindings

        if a.is_var and a.op in uvars:
            if self._occurs(a.op, b, uvars):
                return None
            bindings[a.op] = b
            return bindings

        if b.is_var and b.op in uvars:
            if self._occurs(b.op, a, uvars):
                return None
            bindings[b.op] = a
            return bindings

        if a.op != b.op or len(a.args) != len(b.args):
            return None

        for aa, bb in zip(a.args, b.args):
            result = self._unify(aa, bb, uvars, bindings)
            if result is None:
                return None
            bindings = result
        return bindings

    @staticmethod
    def _apply(expr: Expr, bindings: Dict[str, Expr]) -> Expr:
        if expr.is_var and expr.op in bindings:
            return PatternMatcher._apply(bindings[expr.op], bindings)
        if expr.args:
            return Expr(
                expr.op,
                tuple(PatternMatcher._apply(a, bindings) for a in expr.args),
            )
        return expr

    @staticmethod
    def _occurs(var_name: str, expr: Expr, uvars: Set[str]) -> bool:
        if expr.is_var:
            return expr.op == var_name
        return any(PatternMatcher._occurs(var_name, a, uvars) for a in expr.args)


# ---------------------------------------------------------------------------
# 6. Logic Theorist -- theorem prover
# ---------------------------------------------------------------------------

@dataclass
class ProofStep:
    """A single step in a proof."""

    rule: str  # "axiom", "substitution", "detachment", "chaining"
    result: Expr
    detail: str = ""

    def __repr__(self) -> str:
        return f"[{self.rule}] {self.result}  {self.detail}"


class Logictheorist:
    """
    A theorem prover inspired by Newell, Shaw, and Simon's Logic Theorist.

    The Logic Theorist (1956) proved theorems by searching through a space
    of derivations using three operations:

    1. **Substitution** -- instantiate variables in a known theorem to
       produce a new theorem.
    2. **Detachment (Modus Ponens)** -- from ``A`` and ``A => B``, conclude
       ``B``.
    3. **Chaining** -- from ``A => B`` and ``B => C``, conclude ``A => C``
       (forward chaining); or work backward from the goal.

    The prover maintains a set of *proven theorems* (initially the axioms)
    and tries to derive the target by applying these operations with
    bounded depth.

    Usage::

        p, q, r = var("p"), var("q"), var("r")
        lt = Logictheorist()
        lt.add_axiom(implies(p, lor(p, q)))                    # 1.2
        lt.add_axiom(implies(lor(p, q), lor(q, p)))            # 1.4
        lt.add_axiom(implies(implies(p, q),
                             implies(neg(q), neg(p))))          # 1.3 (transposition)

        # Prove: p => (q | p)   -- i.e., substitute into axiom 1.2 then use 1.4
        ok = lt.prove(implies(p, lor(q, p)))
        assert ok is not None
    """

    def __init__(self, max_depth: int = 4) -> None:
        self.axioms: List[Expr] = []
        self.proven: List[Expr] = []  # ordered list of proven theorems
        self.proofs: Dict[Expr, List[ProofStep]] = {}
        self.matcher = PatternMatcher()
        self.max_depth = max_depth

    # -- setup -------------------------------------------------------------

    def add_axiom(self, expr: Expr) -> None:
        """Add an axiom (assumed true without proof)."""
        self.axioms.append(expr)
        if expr not in self.proven:
            self.proven.append(expr)
            self.proofs[expr] = [ProofStep("axiom", expr)]

    # -- main interface ----------------------------------------------------

    def prove(self, goal: Expr) -> Optional[List[ProofStep]]:
        """
        Attempt to prove *goal* from the current axioms and proven theorems.

        Returns a list of proof steps on success, or ``None`` on failure.
        """
        if goal in self.proofs:
            return self.proofs[goal]

        result = self._prove_recursive(goal, depth=0)
        return result

    def _prove_recursive(self, goal: Expr, depth: int) -> Optional[List[ProofStep]]:
        if goal in self.proofs:
            return self.proofs[goal]

        if depth >= self.max_depth:
            return None

        # Strategy 1: Substitution -- try to match goal against each known
        # theorem by finding an instantiation of the theorem's variables.
        result = self._try_substitution(goal)
        if result is not None:
            return result

        # Strategy 2: Detachment (Modus Ponens) -- if goal is B, look for
        # known A => B and try to prove A; or look for known A and known
        # A => B.
        result = self._try_detachment(goal, depth)
        if result is not None:
            return result

        # Strategy 3: Chaining -- if goal is A => C, look for A => B and
        # B => C that can compose.
        result = self._try_chaining(goal, depth)
        if result is not None:
            return result

        return None

    # -- substitution ------------------------------------------------------

    def _try_substitution(self, goal: Expr) -> Optional[List[ProofStep]]:
        """
        Try to derive *goal* by substituting into a known theorem.

        For each known theorem T with variables {v1, v2, ...}, try to find
        a binding such that T[bindings] == goal.
        """
        for thm in list(self.proven):
            thm_vars = thm.variables()
            if not thm_vars:
                continue
            bindings = self.matcher.match(thm, goal, pattern_vars=thm_vars)
            if bindings is not None:
                result = thm.substitute(bindings)
                if result == goal:
                    steps = list(self.proofs[thm]) + [
                        ProofStep(
                            "substitution",
                            goal,
                            f"from {thm} with {self._fmt_bindings(bindings)}",
                        )
                    ]
                    self._record(goal, steps)
                    return steps
        return None

    # -- detachment (modus ponens) -----------------------------------------

    def _try_detachment(self, goal: Expr, depth: int) -> Optional[List[ProofStep]]:
        """
        Modus ponens: to prove B, find (or prove) some A such that A => B
        is known, and A is known (or provable).

        Also: if A is known, and we can find/prove A => goal, conclude goal.
        """
        # Forward: for each known implication A => X, see if X can be
        # matched to goal by substitution, then check if A is provable.
        for thm in list(self.proven):
            if thm.op == "=>" and len(thm.args) == 2:
                antecedent, consequent = thm.args
                thm_vars = thm.variables()
                bindings = self.matcher.match(consequent, goal, pattern_vars=thm_vars)
                if bindings is not None:
                    needed = antecedent.substitute(bindings)
                    actual_consequent = consequent.substitute(bindings)
                    if actual_consequent != goal:
                        continue
                    # Check if the antecedent is already proven or provable
                    needed_proof = self._prove_recursive(needed, depth + 1)
                    if needed_proof is not None:
                        steps = needed_proof + list(self.proofs.get(thm, [])) + [
                            ProofStep(
                                "detachment",
                                goal,
                                f"modus ponens on {needed} and {thm.substitute(bindings)}",
                            )
                        ]
                        self._record(goal, steps)
                        return steps

        return None

    # -- chaining ----------------------------------------------------------

    def _try_chaining(self, goal: Expr, depth: int) -> Optional[List[ProofStep]]:
        """
        If goal is ``A => C``, look for a midpoint B such that
        ``A => B`` and ``B => C`` are both known/provable.

        Also try backward chaining: if we know ``B => C``, try to prove
        ``A => B``.
        """
        if goal.op != "=>" or len(goal.args) != 2:
            return None

        goal_a, goal_c = goal.args

        # Try each known implication as a potential first or second link.
        for thm in list(self.proven):
            if thm.op != "=>" or len(thm.args) != 2:
                continue

            thm_ante, thm_cons = thm.args
            thm_vars = thm.variables()

            # Forward chaining: thm is A => B, need B => C.
            bindings = self.matcher.match(thm_ante, goal_a, pattern_vars=thm_vars)
            if bindings is not None:
                mid = thm_cons.substitute(bindings)
                needed = implies(mid, goal_c)
                needed_proof = self._prove_recursive(needed, depth + 1)
                if needed_proof is not None:
                    first_link = thm.substitute(bindings)
                    steps = (
                        list(self.proofs.get(thm, []))
                        + needed_proof
                        + [
                            ProofStep(
                                "chaining",
                                goal,
                                f"chain {first_link} with {needed}",
                            )
                        ]
                    )
                    self._record(goal, steps)
                    return steps

            # Backward chaining: thm is B => C, need A => B.
            bindings = self.matcher.match(thm_cons, goal_c, pattern_vars=thm_vars)
            if bindings is not None:
                mid = thm_ante.substitute(bindings)
                needed = implies(goal_a, mid)
                needed_proof = self._prove_recursive(needed, depth + 1)
                if needed_proof is not None:
                    second_link = thm.substitute(bindings)
                    steps = (
                        needed_proof
                        + list(self.proofs.get(thm, []))
                        + [
                            ProofStep(
                                "chaining",
                                goal,
                                f"chain {needed} with {second_link}",
                            )
                        ]
                    )
                    self._record(goal, steps)
                    return steps

        return None

    # -- helpers -----------------------------------------------------------

    def _record(self, expr: Expr, steps: List[ProofStep]) -> None:
        if expr not in self.proofs:
            self.proven.append(expr)
            self.proofs[expr] = steps

    @staticmethod
    def _fmt_bindings(bindings: Dict[str, Expr]) -> str:
        return "{" + ", ".join(f"{k} := {v}" for k, v in bindings.items()) + "}"

    def proven_theorems(self) -> List[Expr]:
        """Return a list of everything proven so far."""
        return list(self.proven)

    def show_proof(self, expr: Expr) -> str:
        """Pretty-print the proof of *expr*."""
        if expr not in self.proofs:
            return f"No proof found for {expr}"
        lines = [f"Proof of {expr}:"]
        for i, step in enumerate(self.proofs[expr], 1):
            lines.append(f"  {i}. {step}")
        return "\n".join(lines)
