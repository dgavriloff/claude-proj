"""
IPL - Information Processing Language

A Python implementation of the core ideas from Allen Newell, Cliff Shaw,
and Herbert Simon's IPL (1956), the first list-processing language.

See ipl.py module docstring for full historical context.
"""

from .ipl import (
    Memory,
    Cell,
    IPLList,
    AssociationStore,
    Generator,
    generator,
    PatternMatcher,
    Logictheorist,
    Expr,
    implies,
    neg,
    lor,
    land,
    var,
    axiom,
)
