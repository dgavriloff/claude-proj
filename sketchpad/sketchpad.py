"""
===========================================================================
 SKETCHPAD — A Constraint-Based Geometric Drawing System
===========================================================================

 A Python implementation inspired by Ivan Edward Sutherland's Sketchpad,
 the most important computer program you have never heard of.

 HISTORICAL CONTEXT
 ------------------

 In January 1963, Ivan Sutherland — then a 25-year-old PhD student at MIT
 — demonstrated a program called "Sketchpad: A Man-Machine Graphical
 Communication System" on the Lincoln Laboratory TX-2 computer.  It was
 his doctoral thesis, supervised by Claude Shannon.  Nothing like it had
 ever existed.

 The TX-2 was a one-of-a-kind transistorized computer with 64K of 36-bit
 words of magnetic-core memory, an oscilloscope display capable of
 drawing 36-bit-addressed vectors, and — crucially — a light pen that
 could both detect and designate points on the phosphor screen.  The
 machine filled a room; Sutherland made it into a drawing table.

 What made Sketchpad revolutionary was not that you could draw on a
 screen (oscilloscopes had been used for display before).  It was *how*
 you drew.  In Sketchpad:

   1. CONSTRAINT-BASED GEOMETRY.  You did not position lines pixel by
      pixel.  You sketched rough shapes, then declared *relationships*
      between them: this line is parallel to that one; these two segments
      have equal length; this point lies on that circle; these lines meet
      at right angles.  The system then *solved* for the exact positions
      that satisfied all constraints simultaneously.  The drawing snapped
      into mathematical perfection before your eyes.

      Sutherland implemented this with a one-pass iterative relaxation
      method.  Each constraint was treated as a "virtual force" that
      pulled the geometry toward satisfaction.  The solver repeatedly
      applied small corrections — exactly the way a physical system of
      springs would settle toward equilibrium.  With enough iterations,
      the drawing converged.

   2. RECURSIVE MASTERS AND INSTANCES.  Sutherland invented what we
      would now call object-oriented instancing — sixteen years before
      Smalltalk.  You could define a "master" drawing (say, a rivet),
      then stamp out any number of "instances" of it.  Each instance
      shared the master's topology and constraints but had its own
      position, scale, and rotation.  If you edited the master, every
      instance updated.  Instances could themselves contain instances,
      giving you a recursive hierarchical structure — the first scene
      graph, the first prototype-based inheritance system.

   3. DIRECT MANIPULATION.  You could grab any point with the light pen
      and drag it.  The constraint solver ran in real time, so the
      entire connected structure — lines, circles, constrained
      companions — moved and deformed live, always satisfying its
      declared relationships.  This was the invention of direct
      manipulation as an interaction paradigm.

 Sketchpad was the ancestor of AutoCAD, SolidWorks, Illustrator, every
 GUI widget toolkit, the Model-View-Controller pattern, and the very
 concept of object-oriented programming.  Alan Kay, who created
 Smalltalk and coined "object-oriented," has said that Sketchpad was
 the most important program ever written, and that his own work was an
 attempt to bring Sutherland's ideas to a wider audience.

 Sutherland received the Turing Award in 1988 for Sketchpad.  The ACM
 citation reads: "for his pioneering and visionary contributions to
 computer graphics, starting with Sketchpad, which has forever changed
 the way people interact with computers."

 THE TX-2 AND THE LIGHT PEN
 --------------------------

 The TX-2 at Lincoln Laboratory was built as a testbed for transistor
 logic (its predecessor, the TX-0, was one of the first fully
 transistorized computers).  It had a 9-inch oscilloscope display that
 used a calligraphic (vector) scan — the electron beam traced lines
 directly rather than scanning a raster.  The display could draw about
 20,000 line-segments per refresh at roughly 30 Hz.

 The light pen was a photosensitive detector in a stylus.  When the
 CRT's electron beam swept past the pen's position, the pen registered
 a pulse, allowing the computer to determine which displayed element
 the user was pointing at.  Sutherland used this for selection, dragging,
 and menu interaction — the first pointing-device GUI, predating the
 mouse (Engelbart, 1964) by a year.

 THIS IMPLEMENTATION
 -------------------

 This module provides:

   - Geometric primitives: Point, Line, Circle, Arc
   - Constraints: Coincident, Parallel, Perpendicular, EqualLength,
     FixedDistance, Tangent, Horizontal, Vertical, FixedAngle,
     Midpoint, OnCircle
   - A constraint solver using iterative relaxation with configurable
     stiffness, damping, and convergence tolerance
   - A Master/Instance system with recursive instantiation
   - A Drawing container that owns geometry and constraints and
     provides the solve/drag interface

 The solver faithfully follows Sutherland's relaxation approach: each
 constraint computes an error and applies a corrective displacement to
 its dependent points, scaled by a stiffness factor.  The solver loops
 until the total error drops below a tolerance or a maximum number of
 iterations is reached.  Points can be pinned (fixed) so that
 constraints propagate *away* from anchored geometry — exactly as
 Sutherland's system behaved when you held a point with the light pen.

 Pure Python, standard library only.  As Sutherland had only 64K words,
 we need no dependencies.

 References
 ----------
 Sutherland, I.E. (1963). "Sketchpad: A Man-Machine Graphical
   Communication System." Ph.D. thesis, MIT.  Technical Report No. 296,
   Lincoln Laboratory, MIT.
 Sutherland, I.E. (2003). "Sketchpad: A Man-Machine Graphical
   Communication System." University of Cambridge Computer Laboratory
   Technical Report No. 574 (reissue of the 1963 thesis).

===========================================================================
"""

from __future__ import annotations

import math
import copy
import itertools
from typing import (
    List,
    Optional,
    Tuple,
    Dict,
    Set,
    Iterator,
    Any,
    Callable,
)
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

# -----------------------------------------------------------------------
#  GEOMETRIC PRIMITIVES
# -----------------------------------------------------------------------

_next_id = itertools.count(1)


def _new_id() -> int:
    return next(_next_id)


class Point:
    """A mutable 2-D point — the fundamental atom of Sketchpad geometry.

    Every piece of geometry is ultimately defined in terms of Points.
    A Point can be *pinned*, meaning the solver will not move it —
    analogous to holding it with the light pen on the TX-2.
    """

    __slots__ = ("x", "y", "pinned", "id", "_vx", "_vy")

    def __init__(self, x: float = 0.0, y: float = 0.0, pinned: bool = False) -> None:
        self.x = float(x)
        self.y = float(y)
        self.pinned = pinned
        self.id = _new_id()
        # Velocity accumulators used during relaxation.
        self._vx = 0.0
        self._vy = 0.0

    # -- algebraic helpers ------------------------------------------------

    def distance_to(self, other: "Point") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def move(self, dx: float, dy: float) -> None:
        """Displace this point.  Respects the pinned flag."""
        if not self.pinned:
            self.x += dx
            self.y += dy

    def set(self, x: float, y: float) -> None:
        if not self.pinned:
            self.x = float(x)
            self.y = float(y)

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def copy(self) -> "Point":
        return Point(self.x, self.y, self.pinned)

    def __repr__(self) -> str:
        pin = " PINNED" if self.pinned else ""
        return f"Point(id={self.id}, {self.x:.4f}, {self.y:.4f}{pin})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class Line:
    """A line segment defined by two Points.

    Not a geometric *line* (infinite extent) but a directed segment from
    ``p1`` to ``p2``.  In Sketchpad, every visible stroke was a segment;
    infinite constructions were implicit in constraints.
    """

    __slots__ = ("p1", "p2", "id")

    def __init__(self, p1: Point, p2: Point) -> None:
        self.p1 = p1
        self.p2 = p2
        self.id = _new_id()

    @property
    def dx(self) -> float:
        return self.p2.x - self.p1.x

    @property
    def dy(self) -> float:
        return self.p2.y - self.p1.y

    @property
    def length(self) -> float:
        return math.hypot(self.dx, self.dy)

    @property
    def angle(self) -> float:
        """Angle in radians from p1 to p2, measured from the +x axis."""
        return math.atan2(self.dy, self.dx)

    @property
    def midpoint_xy(self) -> Tuple[float, float]:
        return ((self.p1.x + self.p2.x) / 2, (self.p1.y + self.p2.y) / 2)

    def points(self) -> List[Point]:
        return [self.p1, self.p2]

    def __repr__(self) -> str:
        return f"Line(id={self.id}, {self.p1} -> {self.p2})"


class Circle:
    """A circle defined by a center Point and a radius.

    The radius is stored as a mutable float so that constraints (e.g.
    tangent, fixed-radius) can modify it during solving.
    """

    __slots__ = ("center", "radius", "id")

    def __init__(self, center: Point, radius: float) -> None:
        self.center = center
        self.radius = float(radius)
        self.id = _new_id()

    def point_at_angle(self, theta: float) -> Tuple[float, float]:
        """Return the (x, y) coordinates at angle *theta* on the circle."""
        return (
            self.center.x + self.radius * math.cos(theta),
            self.center.y + self.radius * math.sin(theta),
        )

    def points(self) -> List[Point]:
        return [self.center]

    def __repr__(self) -> str:
        return f"Circle(id={self.id}, center={self.center}, r={self.radius:.4f})"


class Arc:
    """A circular arc defined by a center Point, radius, start angle, and
    sweep angle (both in radians)."""

    __slots__ = ("center", "radius", "start_angle", "sweep_angle", "id")

    def __init__(
        self,
        center: Point,
        radius: float,
        start_angle: float = 0.0,
        sweep_angle: float = math.pi,
    ) -> None:
        self.center = center
        self.radius = float(radius)
        self.start_angle = float(start_angle)
        self.sweep_angle = float(sweep_angle)
        self.id = _new_id()

    @property
    def end_angle(self) -> float:
        return self.start_angle + self.sweep_angle

    def point_at(self, t: float) -> Tuple[float, float]:
        """Point on the arc at parameter *t* in [0, 1]."""
        theta = self.start_angle + t * self.sweep_angle
        return (
            self.center.x + self.radius * math.cos(theta),
            self.center.y + self.radius * math.sin(theta),
        )

    def start_xy(self) -> Tuple[float, float]:
        return self.point_at(0.0)

    def end_xy(self) -> Tuple[float, float]:
        return self.point_at(1.0)

    def points(self) -> List[Point]:
        return [self.center]

    def __repr__(self) -> str:
        return (
            f"Arc(id={self.id}, center={self.center}, r={self.radius:.4f}, "
            f"start={math.degrees(self.start_angle):.1f}°, "
            f"sweep={math.degrees(self.sweep_angle):.1f}°)"
        )


# -----------------------------------------------------------------------
#  CONSTRAINTS
# -----------------------------------------------------------------------
# Every constraint follows the same protocol: it reports an *error*
# (scalar measure of violation) and can *apply* a corrective
# displacement to the points it governs.  The displacement is scaled
# by a stiffness factor so that the relaxation is stable.
# -----------------------------------------------------------------------

class Constraint(ABC):
    """Abstract base class for all geometric constraints.

    Sub-classes must implement:

    ``error()``
        Return a non-negative scalar measuring how far the constraint
        is from being satisfied.  Zero means perfectly satisfied.

    ``apply(stiffness)``
        Nudge the governed points toward satisfaction.  ``stiffness``
        is a factor in (0, 1] that controls how aggressively the
        correction is applied on each relaxation pass.

    ``involved_points()``
        Return the set of Points that this constraint reads or writes.
    """

    def __init__(self) -> None:
        self.id = _new_id()
        self.enabled = True
        self.priority: float = 1.0  # multiplier on effective stiffness

    @abstractmethod
    def error(self) -> float: ...

    @abstractmethod
    def apply(self, stiffness: float) -> None: ...

    @abstractmethod
    def involved_points(self) -> Set[Point]: ...

    def __repr__(self) -> str:
        name = type(self).__name__
        err = self.error()
        return f"{name}(id={self.id}, error={err:.6f})"


# -- helpers --------------------------------------------------------------

_EPS = 1e-12  # avoid division by zero


def _normalize(dx: float, dy: float) -> Tuple[float, float]:
    m = math.hypot(dx, dy)
    if m < _EPS:
        return (0.0, 0.0)
    return (dx / m, dy / m)


def _dot(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * bx + ay * by


def _cross2(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * by - ay * bx


# -- concrete constraints -------------------------------------------------


class Coincident(Constraint):
    """Two points must occupy the same location.

    This is the most fundamental topological constraint in Sketchpad —
    it is how line endpoints are joined, how geometry shares vertices,
    and how instances attach to their environment.
    """

    def __init__(self, p1: Point, p2: Point) -> None:
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def error(self) -> float:
        return self.p1.distance_to(self.p2)

    def apply(self, stiffness: float) -> None:
        dx = self.p2.x - self.p1.x
        dy = self.p2.y - self.p1.y
        d = math.hypot(dx, dy)
        if d < _EPS:
            return
        # Each unpinned point moves half-way toward the other.
        f = stiffness * self.priority
        n1_free = not self.p1.pinned
        n2_free = not self.p2.pinned
        divisor = int(n1_free) + int(n2_free)
        if divisor == 0:
            return
        step = f / divisor
        if n1_free:
            self.p1.x += dx * step
            self.p1.y += dy * step
        if n2_free:
            self.p2.x -= dx * step
            self.p2.y -= dy * step

    def involved_points(self) -> Set[Point]:
        return {self.p1, self.p2}


class Horizontal(Constraint):
    """A line segment must be horizontal (Δy = 0)."""

    def __init__(self, line: Line) -> None:
        super().__init__()
        self.line = line

    def error(self) -> float:
        return abs(self.line.dy)

    def apply(self, stiffness: float) -> None:
        dy = self.line.dy
        if abs(dy) < _EPS:
            return
        f = stiffness * self.priority
        p1, p2 = self.line.p1, self.line.p2
        n1_free = not p1.pinned
        n2_free = not p2.pinned
        divisor = int(n1_free) + int(n2_free)
        if divisor == 0:
            return
        correction = dy * f / divisor
        if n1_free:
            p1.y += correction
        if n2_free:
            p2.y -= correction

    def involved_points(self) -> Set[Point]:
        return {self.line.p1, self.line.p2}


class Vertical(Constraint):
    """A line segment must be vertical (Δx = 0)."""

    def __init__(self, line: Line) -> None:
        super().__init__()
        self.line = line

    def error(self) -> float:
        return abs(self.line.dx)

    def apply(self, stiffness: float) -> None:
        dx = self.line.dx
        if abs(dx) < _EPS:
            return
        f = stiffness * self.priority
        p1, p2 = self.line.p1, self.line.p2
        n1_free = not p1.pinned
        n2_free = not p2.pinned
        divisor = int(n1_free) + int(n2_free)
        if divisor == 0:
            return
        correction = dx * f / divisor
        if n1_free:
            p1.x += correction
        if n2_free:
            p2.x -= correction

    def involved_points(self) -> Set[Point]:
        return {self.line.p1, self.line.p2}


class FixedDistance(Constraint):
    """Two points must be exactly ``distance`` apart."""

    def __init__(self, p1: Point, p2: Point, distance: float) -> None:
        super().__init__()
        self.p1 = p1
        self.p2 = p2
        self.distance = float(distance)

    def error(self) -> float:
        return abs(self.p1.distance_to(self.p2) - self.distance)

    def apply(self, stiffness: float) -> None:
        dx = self.p2.x - self.p1.x
        dy = self.p2.y - self.p1.y
        current = math.hypot(dx, dy)
        if current < _EPS:
            # Degenerate — nudge apart along an arbitrary direction.
            dx, dy = 1.0, 0.0
            current = _EPS
        diff = current - self.distance
        if abs(diff) < _EPS:
            return
        f = stiffness * self.priority
        nx, ny = dx / current, dy / current
        n1_free = not self.p1.pinned
        n2_free = not self.p2.pinned
        divisor = int(n1_free) + int(n2_free)
        if divisor == 0:
            return
        correction = diff * f / divisor
        if n1_free:
            self.p1.x += nx * correction
            self.p1.y += ny * correction
        if n2_free:
            self.p2.x -= nx * correction
            self.p2.y -= ny * correction

    def involved_points(self) -> Set[Point]:
        return {self.p1, self.p2}


class EqualLength(Constraint):
    """Two line segments must have the same length."""

    def __init__(self, line_a: Line, line_b: Line) -> None:
        super().__init__()
        self.line_a = line_a
        self.line_b = line_b

    def error(self) -> float:
        return abs(self.line_a.length - self.line_b.length)

    def apply(self, stiffness: float) -> None:
        la = self.line_a.length
        lb = self.line_b.length
        if la < _EPS and lb < _EPS:
            return
        diff = la - lb  # positive ⇒ a is longer
        if abs(diff) < _EPS:
            return
        f = stiffness * self.priority * 0.5  # share correction between the two lines

        # Shorten/lengthen each line by adjusting its endpoints.
        for line, sign in ((self.line_a, -1.0), (self.line_b, 1.0)):
            length = line.length
            if length < _EPS:
                continue
            dx, dy = line.dx / length, line.dy / length
            adj = sign * diff * f
            p1f = not line.p1.pinned
            p2f = not line.p2.pinned
            div = int(p1f) + int(p2f)
            if div == 0:
                continue
            step = adj / div
            if p1f:
                line.p1.x -= dx * step
                line.p1.y -= dy * step
            if p2f:
                line.p2.x += dx * step
                line.p2.y += dy * step

    def involved_points(self) -> Set[Point]:
        return {self.line_a.p1, self.line_a.p2, self.line_b.p1, self.line_b.p2}


class Parallel(Constraint):
    """Two line segments must be parallel.

    The error is measured as the absolute sine of the angle between them —
    zero when parallel (or anti-parallel).
    """

    def __init__(self, line_a: Line, line_b: Line) -> None:
        super().__init__()
        self.line_a = line_a
        self.line_b = line_b

    def error(self) -> float:
        la = self.line_a.length
        lb = self.line_b.length
        if la < _EPS or lb < _EPS:
            return 0.0
        cross = _cross2(self.line_a.dx, self.line_a.dy, self.line_b.dx, self.line_b.dy)
        return abs(cross) / (la * lb)

    def apply(self, stiffness: float) -> None:
        la = self.line_a.length
        lb = self.line_b.length
        if la < _EPS or lb < _EPS:
            return
        # We rotate line_b so its direction matches line_a.
        # The angle delta is asin(cross / (la*lb)), small-angle ≈ cross/(la*lb).
        cross = _cross2(self.line_a.dx, self.line_a.dy, self.line_b.dx, self.line_b.dy)
        dot = _dot(self.line_a.dx, self.line_a.dy, self.line_b.dx, self.line_b.dy)
        sin_err = cross / (la * lb)
        if abs(sin_err) < _EPS:
            return
        # Decide rotation sign: rotate b toward alignment with a.
        # If dot < 0, lines point in opposite directions (anti-parallel is fine).
        angle_err = math.asin(max(-1.0, min(1.0, sin_err)))
        f = stiffness * self.priority
        # Rotate both lines toward each other by half the angle error.
        self._rotate_line(self.line_b, -angle_err * f * 0.5)
        self._rotate_line(self.line_a, angle_err * f * 0.5)

    @staticmethod
    def _rotate_line(line: Line, angle: float) -> None:
        """Rotate *line* about its midpoint by *angle* radians."""
        mx, my = line.midpoint_xy
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        for p in (line.p1, line.p2):
            if p.pinned:
                continue
            rx, ry = p.x - mx, p.y - my
            p.x = mx + rx * cos_a - ry * sin_a
            p.y = my + rx * sin_a + ry * cos_a

    def involved_points(self) -> Set[Point]:
        return {self.line_a.p1, self.line_a.p2, self.line_b.p1, self.line_b.p2}


class Perpendicular(Constraint):
    """Two line segments must meet at right angles.

    The error is the absolute cosine of the angle between them — zero
    when perpendicular.
    """

    def __init__(self, line_a: Line, line_b: Line) -> None:
        super().__init__()
        self.line_a = line_a
        self.line_b = line_b

    def error(self) -> float:
        la = self.line_a.length
        lb = self.line_b.length
        if la < _EPS or lb < _EPS:
            return 0.0
        dot = _dot(self.line_a.dx, self.line_a.dy, self.line_b.dx, self.line_b.dy)
        return abs(dot) / (la * lb)

    def apply(self, stiffness: float) -> None:
        la = self.line_a.length
        lb = self.line_b.length
        if la < _EPS or lb < _EPS:
            return
        dot = _dot(self.line_a.dx, self.line_a.dy, self.line_b.dx, self.line_b.dy)
        cos_err = dot / (la * lb)
        if abs(cos_err) < _EPS:
            return
        # Angle between them; we want it to be ±π/2.
        angle = math.atan2(
            _cross2(self.line_a.dx, self.line_a.dy, self.line_b.dx, self.line_b.dy),
            dot,
        )
        # Target is the nearest right angle.
        if angle >= 0:
            target = math.pi / 2
        else:
            target = -math.pi / 2
        angle_err = angle - target
        f = stiffness * self.priority
        Parallel._rotate_line(self.line_b, -angle_err * f * 0.5)
        Parallel._rotate_line(self.line_a, angle_err * f * 0.5)

    def involved_points(self) -> Set[Point]:
        return {self.line_a.p1, self.line_a.p2, self.line_b.p1, self.line_b.p2}


class FixedAngle(Constraint):
    """A line segment must have a specific angle (radians) from the +x axis."""

    def __init__(self, line: Line, angle: float) -> None:
        super().__init__()
        self.line = line
        self.target_angle = float(angle)

    def error(self) -> float:
        if self.line.length < _EPS:
            return 0.0
        diff = self._angle_diff()
        return abs(diff)

    def _angle_diff(self) -> float:
        current = self.line.angle
        diff = current - self.target_angle
        # Normalize to [-π, π].
        diff = (diff + math.pi) % (2 * math.pi) - math.pi
        return diff

    def apply(self, stiffness: float) -> None:
        if self.line.length < _EPS:
            return
        diff = self._angle_diff()
        if abs(diff) < _EPS:
            return
        f = stiffness * self.priority
        Parallel._rotate_line(self.line, -diff * f)

    def involved_points(self) -> Set[Point]:
        return {self.line.p1, self.line.p2}


class Tangent(Constraint):
    """A line must be tangent to a circle.

    The tangent condition means the shortest distance from the circle's
    center to the (infinite) line through the segment equals the radius.
    """

    def __init__(self, line: Line, circle: Circle) -> None:
        super().__init__()
        self.line = line
        self.circle = circle

    def _signed_distance(self) -> float:
        """Signed distance from circle center to the line (positive = center
        is to the left of the directed segment p1→p2)."""
        dx, dy = self.line.dx, self.line.dy
        length = self.line.length
        if length < _EPS:
            return self.circle.center.distance_to(self.line.p1) - self.circle.radius
        # Perpendicular distance.
        cx = self.circle.center.x - self.line.p1.x
        cy = self.circle.center.y - self.line.p1.y
        cross = _cross2(dx, dy, cx, cy)
        return cross / length

    def error(self) -> float:
        return abs(abs(self._signed_distance()) - self.circle.radius)

    def apply(self, stiffness: float) -> None:
        length = self.line.length
        if length < _EPS:
            return
        sd = self._signed_distance()
        # We want |sd| == radius.  Error sign tells direction.
        if sd >= 0:
            err = sd - self.circle.radius
        else:
            err = sd + self.circle.radius  # -(|sd| - r) when sd < 0
        if abs(err) < _EPS:
            return
        f = stiffness * self.priority
        # Normal to the line (pointing left).
        nx, ny = -self.line.dy / length, self.line.dx / length
        correction = err * f
        # Move the line endpoints toward/away from center along the normal,
        # and/or move the center.
        n_free_line = int(not self.line.p1.pinned) + int(not self.line.p2.pinned)
        center_free = not self.circle.center.pinned
        total_free = n_free_line + int(center_free)
        if total_free == 0:
            return
        share = correction / total_free
        if not self.line.p1.pinned:
            self.line.p1.x += nx * share
            self.line.p1.y += ny * share
        if not self.line.p2.pinned:
            self.line.p2.x += nx * share
            self.line.p2.y += ny * share
        if center_free:
            self.circle.center.x -= nx * share
            self.circle.center.y -= ny * share

    def involved_points(self) -> Set[Point]:
        return {self.line.p1, self.line.p2, self.circle.center}


class Midpoint(Constraint):
    """A point must lie at the midpoint of a line segment."""

    def __init__(self, point: Point, line: Line) -> None:
        super().__init__()
        self.point = point
        self.line = line

    def error(self) -> float:
        mx, my = self.line.midpoint_xy
        return math.hypot(self.point.x - mx, self.point.y - my)

    def apply(self, stiffness: float) -> None:
        mx, my = self.line.midpoint_xy
        dx = mx - self.point.x
        dy = my - self.point.y
        d = math.hypot(dx, dy)
        if d < _EPS:
            return
        f = stiffness * self.priority
        pf = not self.point.pinned
        lf1 = not self.line.p1.pinned
        lf2 = not self.line.p2.pinned
        n_free = int(pf) + int(lf1) + int(lf2)
        if n_free == 0:
            return
        # Move point toward midpoint; move line endpoints the other way.
        if pf:
            self.point.x += dx * f * 0.5
            self.point.y += dy * f * 0.5
        # Adjust line endpoints so their midpoint moves toward the point.
        if lf1:
            self.line.p1.x -= dx * f * 0.25
            self.line.p1.y -= dy * f * 0.25
        if lf2:
            self.line.p2.x -= dx * f * 0.25
            self.line.p2.y -= dy * f * 0.25

    def involved_points(self) -> Set[Point]:
        return {self.point, self.line.p1, self.line.p2}


class OnCircle(Constraint):
    """A point must lie on a circle."""

    def __init__(self, point: Point, circle: Circle) -> None:
        super().__init__()
        self.point = point
        self.circle = circle

    def error(self) -> float:
        d = self.point.distance_to(self.circle.center)
        return abs(d - self.circle.radius)

    def apply(self, stiffness: float) -> None:
        cx, cy = self.circle.center.x, self.circle.center.y
        dx = self.point.x - cx
        dy = self.point.y - cy
        d = math.hypot(dx, dy)
        if d < _EPS:
            # Point is at center — push it out in an arbitrary direction.
            dx, dy, d = 1.0, 0.0, 1.0
        diff = d - self.circle.radius
        if abs(diff) < _EPS:
            return
        f = stiffness * self.priority
        nx, ny = dx / d, dy / d
        pf = not self.point.pinned
        cf = not self.circle.center.pinned
        n_free = int(pf) + int(cf)
        if n_free == 0:
            return
        share = diff * f / n_free
        if pf:
            self.point.x -= nx * share
            self.point.y -= ny * share
        if cf:
            self.circle.center.x += nx * share
            self.circle.center.y += ny * share

    def involved_points(self) -> Set[Point]:
        return {self.point, self.circle.center}


# -----------------------------------------------------------------------
#  CONSTRAINT SOLVER — Iterative Relaxation
# -----------------------------------------------------------------------
#
# Sutherland's solver worked by cycling over every constraint and
# applying a small correction on each pass.  After enough passes the
# geometry converged.  This is mathematically equivalent to Gauss-Seidel
# relaxation on a non-linear system, or to a spring simulation run
# until steady state.  It is simple, robust, and — for the moderate
# constraint counts of a typical CAD sketch — perfectly effective.
# -----------------------------------------------------------------------


class ConstraintSolver:
    """Iterative-relaxation constraint solver.

    Parameters
    ----------
    stiffness : float
        How aggressively each constraint corrects on every pass.
        Values near 1.0 converge faster but risk oscillation; values
        near 0.1–0.3 are more stable.  Default 0.5.
    tolerance : float
        The maximum per-constraint error at which the solver declares
        convergence.  Default 1e-6.
    max_iterations : int
        Hard cap on solver passes.  Default 1000.
    """

    def __init__(
        self,
        stiffness: float = 0.5,
        tolerance: float = 1e-6,
        max_iterations: int = 1000,
    ) -> None:
        self.stiffness = stiffness
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.last_iterations = 0
        self.last_max_error = 0.0

    def solve(self, constraints: List[Constraint]) -> bool:
        """Run relaxation until convergence or iteration limit.

        Returns ``True`` if all constraints are satisfied within
        tolerance, ``False`` if the iteration cap was reached.
        """
        active = [c for c in constraints if c.enabled]
        if not active:
            self.last_iterations = 0
            self.last_max_error = 0.0
            return True

        for iteration in range(1, self.max_iterations + 1):
            max_err = 0.0
            for c in active:
                err = c.error()
                if err > max_err:
                    max_err = err
                if err > self.tolerance:
                    c.apply(self.stiffness)
            self.last_iterations = iteration
            self.last_max_error = max_err
            if max_err <= self.tolerance:
                return True
        return False

    def solve_incremental(
        self,
        constraints: List[Constraint],
        steps: int = 1,
    ) -> float:
        """Run exactly *steps* relaxation passes and return the max error.

        Useful for interactive dragging where you want one pass per
        frame rather than solving to full convergence.
        """
        active = [c for c in constraints if c.enabled]
        max_err = 0.0
        for _ in range(steps):
            max_err = 0.0
            for c in active:
                err = c.error()
                if err > max_err:
                    max_err = err
                if err > self.tolerance:
                    c.apply(self.stiffness)
        self.last_max_error = max_err
        return max_err


# -----------------------------------------------------------------------
#  DRAWING — the container that binds geometry and constraints together
# -----------------------------------------------------------------------


class Drawing:
    """A container for geometric primitives and their constraints.

    A Drawing owns a set of points, lines, circles, arcs, and
    constraints.  It provides convenience methods for creating geometry,
    adding constraints, solving, and performing interactive drag
    operations (move a point, re-solve).
    """

    def __init__(self, solver: Optional[ConstraintSolver] = None) -> None:
        self.solver = solver or ConstraintSolver()
        self.points: List[Point] = []
        self.lines: List[Line] = []
        self.circles: List[Circle] = []
        self.arcs: List[Arc] = []
        self.constraints: List[Constraint] = []
        self._instances: List["Instance"] = []

    # -- geometry creation ------------------------------------------------

    def add_point(self, x: float = 0.0, y: float = 0.0, pinned: bool = False) -> Point:
        p = Point(x, y, pinned)
        self.points.append(p)
        return p

    def add_line(self, p1: Point, p2: Point) -> Line:
        ln = Line(p1, p2)
        self.lines.append(ln)
        return ln

    def add_line_xy(
        self, x1: float, y1: float, x2: float, y2: float
    ) -> Line:
        """Create a line from raw coordinates (also creating the points)."""
        p1 = self.add_point(x1, y1)
        p2 = self.add_point(x2, y2)
        return self.add_line(p1, p2)

    def add_circle(self, center: Point, radius: float) -> Circle:
        c = Circle(center, radius)
        self.circles.append(c)
        return c

    def add_arc(
        self,
        center: Point,
        radius: float,
        start_angle: float = 0.0,
        sweep_angle: float = math.pi,
    ) -> Arc:
        a = Arc(center, radius, start_angle, sweep_angle)
        self.arcs.append(a)
        return a

    # -- constraint creation ----------------------------------------------

    def add_constraint(self, constraint: Constraint) -> Constraint:
        self.constraints.append(constraint)
        return constraint

    def constrain_coincident(self, p1: Point, p2: Point) -> Coincident:
        c = Coincident(p1, p2)
        return self.add_constraint(c)  # type: ignore[return-value]

    def constrain_horizontal(self, line: Line) -> Horizontal:
        c = Horizontal(line)
        return self.add_constraint(c)  # type: ignore[return-value]

    def constrain_vertical(self, line: Line) -> Vertical:
        c = Vertical(line)
        return self.add_constraint(c)  # type: ignore[return-value]

    def constrain_fixed_distance(
        self, p1: Point, p2: Point, distance: float
    ) -> FixedDistance:
        c = FixedDistance(p1, p2, distance)
        return self.add_constraint(c)  # type: ignore[return-value]

    def constrain_equal_length(self, a: Line, b: Line) -> EqualLength:
        c = EqualLength(a, b)
        return self.add_constraint(c)  # type: ignore[return-value]

    def constrain_parallel(self, a: Line, b: Line) -> Parallel:
        c = Parallel(a, b)
        return self.add_constraint(c)  # type: ignore[return-value]

    def constrain_perpendicular(self, a: Line, b: Line) -> Perpendicular:
        c = Perpendicular(a, b)
        return self.add_constraint(c)  # type: ignore[return-value]

    def constrain_tangent(self, line: Line, circle: Circle) -> Tangent:
        c = Tangent(line, circle)
        return self.add_constraint(c)  # type: ignore[return-value]

    def constrain_midpoint(self, point: Point, line: Line) -> Midpoint:
        c = Midpoint(point, line)
        return self.add_constraint(c)  # type: ignore[return-value]

    def constrain_on_circle(self, point: Point, circle: Circle) -> OnCircle:
        c = OnCircle(point, circle)
        return self.add_constraint(c)  # type: ignore[return-value]

    def constrain_fixed_angle(self, line: Line, angle: float) -> FixedAngle:
        c = FixedAngle(line, angle)
        return self.add_constraint(c)  # type: ignore[return-value]

    # -- solving ----------------------------------------------------------

    def solve(self) -> bool:
        """Solve all constraints to convergence."""
        all_constraints = list(self.constraints)
        for inst in self._instances:
            all_constraints.extend(inst.constraints)
        return self.solver.solve(all_constraints)

    def solve_incremental(self, steps: int = 1) -> float:
        all_constraints = list(self.constraints)
        for inst in self._instances:
            all_constraints.extend(inst.constraints)
        return self.solver.solve_incremental(all_constraints, steps)

    # -- interactive drag -------------------------------------------------

    def drag(self, point: Point, x: float, y: float, iterations: int = 50) -> None:
        """Simulate an interactive drag: move *point* to (x, y) and relax.

        The point is temporarily pinned during the drag (as if the user
        is holding it with Sutherland's light pen), so constraints
        propagate outward from it.
        """
        was_pinned = point.pinned
        point.pinned = True
        point.x = float(x)
        point.y = float(y)
        all_constraints = list(self.constraints)
        for inst in self._instances:
            all_constraints.extend(inst.constraints)
        self.solver.solve(all_constraints)
        point.pinned = was_pinned

    # -- queries ----------------------------------------------------------

    def all_points(self) -> List[Point]:
        """Return every point in the drawing, including those belonging to
        instances."""
        seen: Set[int] = set()
        result: List[Point] = []
        for p in self.points:
            if p.id not in seen:
                seen.add(p.id)
                result.append(p)
        for inst in self._instances:
            for p in inst.all_points():
                if p.id not in seen:
                    seen.add(p.id)
                    result.append(p)
        return result

    def total_error(self) -> float:
        return sum(c.error() for c in self.constraints if c.enabled)

    def max_error(self) -> float:
        errors = [c.error() for c in self.constraints if c.enabled]
        return max(errors) if errors else 0.0

    def find_point_near(self, x: float, y: float, radius: float = 10.0) -> Optional[Point]:
        """Find the closest point within *radius* of (x, y)."""
        best: Optional[Point] = None
        best_d = radius
        for p in self.all_points():
            d = math.hypot(p.x - x, p.y - y)
            if d < best_d:
                best_d = d
                best = p
        return best

    # -- instances --------------------------------------------------------

    def add_instance(self, instance: "Instance") -> "Instance":
        self._instances.append(instance)
        return instance

    @property
    def instances(self) -> List["Instance"]:
        return list(self._instances)

    # -- serialization helpers (plain dict) --------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """Return a lightweight snapshot of all point positions, useful for
        undo/redo or animation recording."""
        return {p.id: (p.x, p.y) for p in self.all_points()}

    def restore(self, snap: Dict[int, Tuple[float, float]]) -> None:
        for p in self.all_points():
            if p.id in snap:
                p.x, p.y = snap[p.id]

    def __repr__(self) -> str:
        return (
            f"Drawing(points={len(self.points)}, lines={len(self.lines)}, "
            f"circles={len(self.circles)}, arcs={len(self.arcs)}, "
            f"constraints={len(self.constraints)}, "
            f"instances={len(self._instances)})"
        )


# -----------------------------------------------------------------------
#  MASTER / INSTANCE — Sutherland's proto-OOP
# -----------------------------------------------------------------------
#
# In Sketchpad, a "master" was a drawing template.  You could create
# any number of "instances" of a master.  Each instance had its own
# position, rotation, and scale, but shared the master's topology.
# Editing the master updated every instance.  Instances could be
# nested: a master could contain instances of other masters, producing
# a recursive part hierarchy — exactly like a modern scene graph.
#
# Our implementation:
#   - A Master wraps a Drawing (the prototype).
#   - An Instance deep-copies the Master's points and geometry, applies a
#     2-D similarity transform (translate + rotate + uniform scale),
#     and records mapping from master points to instance points so that
#     constraints can bridge the boundary.
# -----------------------------------------------------------------------


class Master:
    """A reusable drawing template — Sutherland's "master".

    Create a Drawing, add geometry and constraints to it, then wrap it
    in a Master.  Stamp out instances with ``create_instance()``.
    """

    def __init__(self, name: str, drawing: Drawing) -> None:
        self.name = name
        self.drawing = drawing
        self.id = _new_id()

    def create_instance(
        self,
        tx: float = 0.0,
        ty: float = 0.0,
        rotation: float = 0.0,
        scale: float = 1.0,
    ) -> "Instance":
        """Stamp out a new Instance of this master.

        Parameters
        ----------
        tx, ty : float
            Translation applied after rotation and scaling.
        rotation : float
            Rotation in radians.
        scale : float
            Uniform scale factor.
        """
        return Instance(self, tx, ty, rotation, scale)

    def __repr__(self) -> str:
        return f"Master({self.name!r}, id={self.id})"


class Instance:
    """A placed copy of a Master drawing.

    The instance deep-copies every Point from the master drawing, applies
    the similarity transform, rebuilds Lines/Circles/Arcs referencing the
    new points, and copies the master's constraints (re-bound to the new
    points).  The ``point_map`` dictionary maps each master Point id to
    the corresponding instance Point.
    """

    def __init__(
        self,
        master: Master,
        tx: float = 0.0,
        ty: float = 0.0,
        rotation: float = 0.0,
        scale: float = 1.0,
    ) -> None:
        self.master = master
        self.id = _new_id()
        self.tx = tx
        self.ty = ty
        self.rotation = rotation
        self.scale = scale

        # Deep-copy points with transform.
        self.point_map: Dict[int, Point] = {}  # master_point.id → instance point
        self.points: List[Point] = []
        self.lines: List[Line] = []
        self.circles: List[Circle] = []
        self.arcs: List[Arc] = []
        self.constraints: List[Constraint] = []

        self._instantiate()

    # -- internals -------------------------------------------------------

    def _transform(self, x: float, y: float) -> Tuple[float, float]:
        """Apply scale → rotate → translate."""
        sx = x * self.scale
        sy = y * self.scale
        cos_r = math.cos(self.rotation)
        sin_r = math.sin(self.rotation)
        rx = sx * cos_r - sy * sin_r
        ry = sx * sin_r + sy * cos_r
        return (rx + self.tx, ry + self.ty)

    def _clone_point(self, p: Point) -> Point:
        if p.id in self.point_map:
            return self.point_map[p.id]
        nx, ny = self._transform(p.x, p.y)
        np_ = Point(nx, ny, p.pinned)
        self.point_map[p.id] = np_
        self.points.append(np_)
        return np_

    def _instantiate(self) -> None:
        src = self.master.drawing

        # Clone points.
        for p in src.points:
            self._clone_point(p)

        # Clone lines.
        for ln in src.lines:
            new_line = Line(self._clone_point(ln.p1), self._clone_point(ln.p2))
            self.lines.append(new_line)

        # Clone circles.
        for ci in src.circles:
            new_circle = Circle(self._clone_point(ci.center), ci.radius * self.scale)
            self.circles.append(new_circle)

        # Clone arcs.
        for ar in src.arcs:
            new_arc = Arc(
                self._clone_point(ar.center),
                ar.radius * self.scale,
                ar.start_angle + self.rotation,
                ar.sweep_angle,
            )
            self.arcs.append(new_arc)

        # Clone constraints — we rebuild each one with the mapped points.
        line_map: Dict[int, Line] = {}
        for old, new in zip(src.lines, self.lines):
            line_map[old.id] = new
        circle_map: Dict[int, Circle] = {}
        for old, new in zip(src.circles, self.circles):
            circle_map[old.id] = new

        for c in src.constraints:
            new_c = self._clone_constraint(c, line_map, circle_map)
            if new_c is not None:
                new_c.priority = c.priority
                new_c.enabled = c.enabled
                self.constraints.append(new_c)

    def _clone_constraint(
        self,
        c: Constraint,
        line_map: Dict[int, Line],
        circle_map: Dict[int, Circle],
    ) -> Optional[Constraint]:
        pm = self.point_map

        if isinstance(c, Coincident):
            return Coincident(pm[c.p1.id], pm[c.p2.id])
        if isinstance(c, Horizontal):
            return Horizontal(line_map[c.line.id])
        if isinstance(c, Vertical):
            return Vertical(line_map[c.line.id])
        if isinstance(c, FixedDistance):
            return FixedDistance(pm[c.p1.id], pm[c.p2.id], c.distance * self.scale)
        if isinstance(c, EqualLength):
            return EqualLength(line_map[c.line_a.id], line_map[c.line_b.id])
        if isinstance(c, Parallel):
            return Parallel(line_map[c.line_a.id], line_map[c.line_b.id])
        if isinstance(c, Perpendicular):
            return Perpendicular(line_map[c.line_a.id], line_map[c.line_b.id])
        if isinstance(c, Tangent):
            return Tangent(line_map[c.line.id], circle_map[c.circle.id])
        if isinstance(c, Midpoint):
            return Midpoint(pm[c.point.id], line_map[c.line.id])
        if isinstance(c, OnCircle):
            return OnCircle(pm[c.point.id], circle_map[c.circle.id])
        if isinstance(c, FixedAngle):
            return FixedAngle(line_map[c.line.id], c.target_angle + self.rotation)
        return None

    # -- public interface -------------------------------------------------

    def get_instance_point(self, master_point: Point) -> Point:
        """Return the instance's copy of a master point."""
        return self.point_map[master_point.id]

    def all_points(self) -> List[Point]:
        return list(self.points)

    def set_transform(
        self,
        tx: Optional[float] = None,
        ty: Optional[float] = None,
        rotation: Optional[float] = None,
        scale: Optional[float] = None,
    ) -> None:
        """Update the instance transform and reposition all points.

        This recomputes every instance point from the master's coordinates
        and the new transform — useful for animating instances.
        """
        if tx is not None:
            self.tx = tx
        if ty is not None:
            self.ty = ty
        if rotation is not None:
            self.rotation = rotation
        if scale is not None:
            self.scale = scale

        src = self.master.drawing
        for mp in src.points:
            ip = self.point_map[mp.id]
            nx, ny = self._transform(mp.x, mp.y)
            ip.x = nx
            ip.y = ny

        # Update circle radii.
        for old_c, new_c in zip(src.circles, self.circles):
            new_c.radius = old_c.radius * self.scale

        # Update arc parameters.
        for old_a, new_a in zip(src.arcs, self.arcs):
            new_a.radius = old_a.radius * self.scale
            new_a.start_angle = old_a.start_angle + self.rotation

    def __repr__(self) -> str:
        return (
            f"Instance(master={self.master.name!r}, id={self.id}, "
            f"tx={self.tx:.2f}, ty={self.ty:.2f}, "
            f"rot={math.degrees(self.rotation):.1f}°, "
            f"scale={self.scale:.2f})"
        )


# -----------------------------------------------------------------------
#  CONVENIENCE: high-level construction helpers
# -----------------------------------------------------------------------


def make_rectangle(
    drawing: Drawing,
    x: float,
    y: float,
    width: float,
    height: float,
    pinned_origin: bool = False,
) -> Tuple[List[Point], List[Line]]:
    """Add a fully-constrained rectangle to *drawing*.

    Returns the four corner points and four edge lines.  Constraints
    added: horizontal top/bottom, vertical left/right, coincident
    corners, fixed distances for width and height.
    """
    p0 = drawing.add_point(x, y, pinned=pinned_origin)
    p1 = drawing.add_point(x + width, y)
    p2 = drawing.add_point(x + width, y + height)
    p3 = drawing.add_point(x, y + height)

    bottom = drawing.add_line(p0, p1)
    right = drawing.add_line(p1, p2)
    top = drawing.add_line(p2, p3)
    left = drawing.add_line(p3, p0)

    # Horizontal / vertical constraints.
    drawing.constrain_horizontal(bottom)
    drawing.constrain_horizontal(top)
    drawing.constrain_vertical(right)
    drawing.constrain_vertical(left)

    # Fixed side lengths.
    drawing.constrain_fixed_distance(p0, p1, width)
    drawing.constrain_fixed_distance(p1, p2, height)
    drawing.constrain_fixed_distance(p2, p3, width)
    drawing.constrain_fixed_distance(p3, p0, height)

    # Join corners.
    # (The lines already share Point objects, so coincident constraints
    # are implicit via identity.  We include them explicitly only when
    # bridging separate constructions.)

    return ([p0, p1, p2, p3], [bottom, right, top, left])


def make_regular_polygon(
    drawing: Drawing,
    cx: float,
    cy: float,
    radius: float,
    n: int,
    start_angle: float = 0.0,
) -> Tuple[List[Point], List[Line]]:
    """Add a regular *n*-gon inscribed in a circle of given radius.

    Returns the vertex points and edge lines.  Equal-length constraints
    are added between all consecutive edges.
    """
    points: List[Point] = []
    for i in range(n):
        theta = start_angle + 2 * math.pi * i / n
        px = cx + radius * math.cos(theta)
        py = cy + radius * math.sin(theta)
        points.append(drawing.add_point(px, py))

    lines: List[Line] = []
    for i in range(n):
        ln = drawing.add_line(points[i], points[(i + 1) % n])
        lines.append(ln)

    # Equal-length constraints on all edges.
    for i in range(1, n):
        drawing.constrain_equal_length(lines[0], lines[i])

    return (points, lines)


def make_triangle(
    drawing: Drawing,
    x1: float, y1: float,
    x2: float, y2: float,
    x3: float, y3: float,
) -> Tuple[List[Point], List[Line]]:
    """Add a triangle to *drawing* and return (points, lines)."""
    p1 = drawing.add_point(x1, y1)
    p2 = drawing.add_point(x2, y2)
    p3 = drawing.add_point(x3, y3)
    l1 = drawing.add_line(p1, p2)
    l2 = drawing.add_line(p2, p3)
    l3 = drawing.add_line(p3, p1)
    return ([p1, p2, p3], [l1, l2, l3])
