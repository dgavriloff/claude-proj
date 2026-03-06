"""
Sketchpad — A constraint-based geometric drawing system.

A Python implementation inspired by Ivan Sutherland's Sketchpad (1963),
the first interactive computer graphics program and the ancestor of
all modern CAD software, GUI toolkits, and object-oriented programming.
"""

from .sketchpad import (
    Point,
    Line,
    Circle,
    Arc,
    Constraint,
    Coincident,
    Parallel,
    Perpendicular,
    EqualLength,
    FixedDistance,
    Tangent,
    Horizontal,
    Vertical,
    FixedAngle,
    Midpoint,
    OnCircle,
    ConstraintSolver,
    Drawing,
    Master,
    Instance,
    make_rectangle,
    make_regular_polygon,
    make_triangle,
)

__all__ = [
    "Point",
    "Line",
    "Circle",
    "Arc",
    "Constraint",
    "Coincident",
    "Parallel",
    "Perpendicular",
    "EqualLength",
    "FixedDistance",
    "Tangent",
    "Horizontal",
    "Vertical",
    "FixedAngle",
    "Midpoint",
    "OnCircle",
    "ConstraintSolver",
    "Drawing",
    "Master",
    "Instance",
    "make_rectangle",
    "make_regular_polygon",
    "make_triangle",
]
