"""
LOGO and Turtle Geometry — A Computational Reconstruction
==========================================================

Seymour Papert (1928-2016) was a South African-born mathematician who
spent years working with Jean Piaget in Geneva before joining MIT in 1963.
Piaget had shown that children are not empty vessels waiting to be filled
with knowledge — they are active builders of their own intellectual
structures. Papert took this further: children don't just construct
knowledge in their heads, they construct it best when they are constructing
something *in the world* — a sandcastle, a poem, a computer program.

At MIT, Papert and his colleagues (including Wally Feurzeig and Cynthia
Solomon at BBN) created LOGO around 1967. The language itself was a Lisp
dialect, but its soul was the Turtle — a small robot (later a screen cursor)
that children could command: FORWARD 100, RIGHT 90. The turtle carried a pen,
so its movements left trails. Geometry was no longer abstract — it was
*body-syntonic*. To draw a circle, you didn't need to understand equations.
You walked in a circle yourself, noticed you were going forward a little and
turning a little, and wrote: REPEAT 360 [FORWARD 1 RIGHT 1].

This was "Turtle Geometry" — Papert and Andrea diSessa's insight that
differential geometry could be made accessible to children through the
turtle's local, intrinsic frame of reference. The Total Turtle Trip Theorem
(any closed path involves turning a total of 360 degrees) is genuinely deep
mathematics that a ten-year-old can discover.

Papert's book "Mindstorms: Children, Computers, and Powerful Ideas" (1980)
laid out the vision. The title refers to the intellectual storms that
happen when a child encounters a powerful idea in the right context.
Papert argued for "microworlds" — constrained computational environments
where children could explore specific mathematical ideas. The Turtle
microworld made geometry tangible. A music microworld could make
composition tangible. The computer was not a teaching machine — it was
a material for construction, an "object to think with."

Then something went wrong.

In the 1980s, as personal computers flooded into schools, the educational
establishment decided that "computer literacy" meant learning to type,
using spreadsheets, running educational drill software — the computer
as an electronic worksheet. LOGO was marginalized. Schools that used it
often did so badly, reducing it to "make pretty pictures" without the
deeper mathematical exploration Papert envisioned. The National Science
Foundation and others funded studies that evaluated LOGO by testing
whether children could do better on standardized tests of "cognitive
skills" — completely missing the point. You don't evaluate a piano by
testing whether pianists are better at mathematics.

Papert wrote bitterly about this in "The Children's Machine" (1993).
The school system had assimilated the computer into its existing
structure rather than allowing the computer to transform learning.
The revolutionary tool became a prop for the status quo.

But the ideas never died. Scratch (created by Mitchel Resnick, Papert's
student at MIT) carries LOGO's DNA. The maker movement, constructionism
in education, computational thinking — all trace back to Papert's
vision of children as builders, not recipients. Every child who
makes a sprite move in Scratch is, whether they know it or not,
inheriting a tradition that began with a mathematician who believed
that the best way to learn about circles was to walk in one.

This module implements a faithful LOGO interpreter with turtle graphics,
SVG output, recursive procedures, multiple turtles, and microworlds —
the computational tools Papert imagined, rendered in modern Python.

References:
    Papert, S. (1980). Mindstorms: Children, Computers, and Powerful Ideas.
    Papert, S. (1993). The Children's Machine.
    Papert, S. & diSessa, A. (1981). Turtle Geometry.
    Solomon, C. (2020). Cynthia Solomon on the History of LOGO.
    Feurzeig, W. et al. (1969). Programming Languages as a Conceptual
        Framework for Teaching Mathematics. (BBN Report No. 1889)
"""

from __future__ import annotations

import copy
import math
import re
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Turtle
# ---------------------------------------------------------------------------

@dataclass
class TurtlePath:
    """A single continuous pen-down path segment."""
    points: List[Tuple[float, float]] = field(default_factory=list)
    color: str = "black"
    width: float = 2.0


@dataclass
class Turtle:
    """
    A LOGO turtle that tracks position, heading, pen state, and path history.

    The turtle lives on a Cartesian plane where (0, 0) is the center,
    positive X is to the right, and positive Y is *up* (matching
    mathematical convention and Papert's original design, not screen
    coordinates). Heading 0 is North (up), and angles increase clockwise
    — because when you face forward and turn RIGHT, that's clockwise.

    This is body-syntonic: the turtle moves the way *you* move.
    """

    name: str = "default"
    x: float = 0.0
    y: float = 0.0
    heading: float = 0.0  # degrees, 0 = North/up, clockwise positive
    pen_down: bool = True
    pen_color: str = "black"
    pen_width: float = 2.0
    visible: bool = True
    paths: List[TurtlePath] = field(default_factory=list)
    _current_path: Optional[TurtlePath] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.pen_down:
            self._start_path()

    def _start_path(self) -> None:
        self._current_path = TurtlePath(
            points=[(self.x, self.y)],
            color=self.pen_color,
            width=self.pen_width,
        )

    def _finish_path(self) -> None:
        if self._current_path and len(self._current_path.points) > 1:
            self.paths.append(self._current_path)
        self._current_path = None

    def forward(self, distance: float) -> None:
        """Move forward in the current heading direction."""
        rad = math.radians(self.heading)
        # heading 0 = North => dx=sin(h), dy=cos(h)
        new_x = self.x + distance * math.sin(rad)
        new_y = self.y + distance * math.cos(rad)
        self.x = new_x
        self.y = new_y
        if self.pen_down and self._current_path is not None:
            self._current_path.points.append((self.x, self.y))

    def back(self, distance: float) -> None:
        self.forward(-distance)

    def right(self, angle: float) -> None:
        self.heading = (self.heading + angle) % 360

    def left(self, angle: float) -> None:
        self.heading = (self.heading - angle) % 360

    def penup(self) -> None:
        self._finish_path()
        self.pen_down = False

    def pendown(self) -> None:
        self.pen_down = True
        self._start_path()

    def setpencolor(self, color: str) -> None:
        if self.pen_down:
            self._finish_path()
        self.pen_color = color
        if self.pen_down:
            self._start_path()

    def setpenwidth(self, width: float) -> None:
        if self.pen_down:
            self._finish_path()
        self.pen_width = width
        if self.pen_down:
            self._start_path()

    def setposition(self, x: float, y: float) -> None:
        """Move to absolute position, drawing if pen is down."""
        self.x = x
        self.y = y
        if self.pen_down and self._current_path is not None:
            self._current_path.points.append((self.x, self.y))

    def setheading(self, angle: float) -> None:
        self.heading = angle % 360

    def home(self) -> None:
        """Return to origin facing north."""
        self.setposition(0, 0)
        self.heading = 0.0

    def clear(self) -> None:
        """Erase all paths but keep position."""
        self._finish_path()
        self.paths.clear()
        if self.pen_down:
            self._start_path()

    def reset(self) -> None:
        """Full reset: clear paths, go home, pen down."""
        self.paths.clear()
        self._current_path = None
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0
        self.pen_down = True
        self.pen_color = "black"
        self.pen_width = 2.0
        self.visible = True
        self._start_path()

    def finalize(self) -> None:
        """Flush current path to the path list (call before rendering)."""
        self._finish_path()
        if self.pen_down:
            self._start_path()


# ---------------------------------------------------------------------------
# SVG Renderer
# ---------------------------------------------------------------------------

class SVGRenderer:
    """
    Renders turtle paths as SVG.

    Converts from turtle coordinates (Y-up, origin center) to SVG
    coordinates (Y-down, origin top-left).
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        background: str = "white",
        padding: int = 20,
        auto_scale: bool = True,
    ) -> None:
        self.width = width
        self.height = height
        self.background = background
        self.padding = padding
        self.auto_scale = auto_scale

    def _compute_bounds(
        self, turtles: List[Turtle]
    ) -> Tuple[float, float, float, float]:
        """Find bounding box of all paths across all turtles."""
        all_x: List[float] = []
        all_y: List[float] = []
        for t in turtles:
            for path in t.paths:
                for px, py in path.points:
                    all_x.append(px)
                    all_y.append(py)
        if not all_x:
            return -100, -100, 100, 100
        return min(all_x), min(all_y), max(all_x), max(all_y)

    def render(self, turtles: List[Turtle]) -> str:
        """Produce a complete SVG string from one or more turtles."""
        # Finalize all turtles
        for t in turtles:
            t.finalize()

        min_x, min_y, max_x, max_y = self._compute_bounds(turtles)

        if self.auto_scale:
            data_w = max_x - min_x or 1.0
            data_h = max_y - min_y or 1.0
            avail_w = self.width - 2 * self.padding
            avail_h = self.height - 2 * self.padding
            scale = min(avail_w / data_w, avail_h / data_h)
            cx = (min_x + max_x) / 2.0
            cy = (min_y + max_y) / 2.0
        else:
            scale = 1.0
            cx = 0.0
            cy = 0.0

        def tx(x: float) -> float:
            return self.width / 2.0 + (x - cx) * scale

        def ty(y: float) -> float:
            # Flip Y: turtle Y-up -> SVG Y-down
            return self.height / 2.0 - (y - cy) * scale

        lines: List[str] = []
        lines.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}">'
        )
        lines.append(
            f'  <rect width="100%" height="100%" fill="{self.background}"/>'
        )

        for t in turtles:
            for path in t.paths:
                if len(path.points) < 2:
                    continue
                d_parts = []
                x0, y0 = path.points[0]
                d_parts.append(f"M {tx(x0):.2f} {ty(y0):.2f}")
                for px, py in path.points[1:]:
                    d_parts.append(f"L {tx(px):.2f} {ty(py):.2f}")
                d = " ".join(d_parts)
                lines.append(
                    f'  <path d="{d}" fill="none" '
                    f'stroke="{path.color}" '
                    f'stroke-width="{path.width}" '
                    f'stroke-linecap="round" '
                    f'stroke-linejoin="round"/>'
                )

        # Draw turtle cursors
        for t in turtles:
            if t.visible:
                sx = tx(t.x)
                sy = ty(t.y)
                # Triangle pointing in heading direction
                # SVG rotation: turtle heading 0=North means -90 in SVG terms
                # Actually, since we flip Y, heading 0 (North/up) points up
                # in SVG that means towards negative Y.
                # SVG rotate is clockwise from East(right).
                # We want 0 heading = pointing up = -90 SVG degrees
                svg_angle = t.heading - 90
                size = 8
                rad = math.radians(t.heading)
                # Compute three vertices of the turtle triangle
                # Tip (forward direction)
                tip_x = sx + size * 1.5 * math.sin(math.radians(t.heading))
                tip_y = sy - size * 1.5 * math.cos(math.radians(t.heading))
                # Left rear
                lr_x = sx + size * math.sin(math.radians(t.heading - 140))
                lr_y = sy - size * math.cos(math.radians(t.heading - 140))
                # Right rear
                rr_x = sx + size * math.sin(math.radians(t.heading + 140))
                rr_y = sy - size * math.cos(math.radians(t.heading + 140))
                lines.append(
                    f'  <polygon points="{tip_x:.2f},{tip_y:.2f} '
                    f'{lr_x:.2f},{lr_y:.2f} {rr_x:.2f},{rr_y:.2f}" '
                    f'fill="green" stroke="darkgreen" stroke-width="1"/>'
                )

        lines.append("</svg>")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# LOGO Tokenizer & Parser
# ---------------------------------------------------------------------------

class LogoError(Exception):
    """Raised for any error in LOGO parsing or execution."""
    pass


def _tokenize(source: str) -> List[str]:
    """
    Tokenize LOGO source into a flat list of tokens.

    LOGO syntax is simple:
    - Words separated by whitespace
    - [ and ] are bracket tokens (for REPEAT bodies, procedure bodies, etc.)
    - Strings starting with : are variable references
    - Strings starting with " are literal words
    - Numbers
    - Arithmetic operators: + - * / ( )
    - Comparison operators: < > =
    """
    tokens: List[str] = []
    source = source.replace("[", " [ ").replace("]", " ] ")
    source = source.replace("(", " ( ").replace(")", " ) ")
    # Ensure operators are separate tokens
    for op in ["<=", ">=", "<>", "<", ">", "="]:
        source = source.replace(op, f" {op} ")
    # Careful: we may have double-spaced things, re-split
    for tok in source.split():
        # Skip comments (lines beginning with ;)
        if tok.startswith(";"):
            break
        tokens.append(tok)
    # Handle line-level comments properly
    result: List[str] = []
    lines = source.split("\n")
    for line in lines:
        # Strip comment
        comment_idx = line.find(";")
        if comment_idx >= 0:
            line = line[:comment_idx]
        line = line.strip()
        if not line:
            continue
        for tok in line.split():
            result.append(tok)
    return result


class LogoParser:
    """
    Parse a token stream into an AST.

    LOGO AST nodes are simple lists/tuples:
    - ("forward", expr)
    - ("right", expr)
    - ("repeat", count_expr, body_stmts)
    - ("to", name, params, body_stmts)
    - ("if", condition_expr, body_stmts)
    - ("ifelse", condition_expr, true_body, false_body)
    - ("make", varname, expr)
    - ("call", name, args)
    - ("num", value)
    - ("var", name)
    - ("word", text)
    - ("binop", op, left, right)
    - ("neg", expr)  # unary minus
    """

    def __init__(
        self,
        tokens: List[str],
        proc_arities: Optional[Dict[str, int]] = None,
    ) -> None:
        self.tokens = tokens
        self.pos = 0
        # Map of PROCEDURE_NAME -> number of parameters, used to
        # greedily parse the correct number of arguments for calls.
        self.proc_arities: Dict[str, int] = proc_arities or {}

    def peek(self) -> Optional[str]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self) -> str:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, value: str) -> str:
        tok = self.advance()
        if tok.upper() != value.upper():
            raise LogoError(f"Expected '{value}', got '{tok}'")
        return tok

    def at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def parse_program(self) -> List[Any]:
        stmts: List[Any] = []
        while not self.at_end():
            s = self.parse_statement()
            if s is not None:
                stmts.append(s)
        return stmts

    def parse_block(self) -> List[Any]:
        """Parse [ ... ] block, returning list of statements."""
        self.expect("[")
        stmts: List[Any] = []
        while self.peek() != "]":
            if self.at_end():
                raise LogoError("Unexpected end of input inside [ ]")
            s = self.parse_statement()
            if s is not None:
                stmts.append(s)
        self.expect("]")
        return stmts

    def parse_statement(self) -> Any:
        tok = self.peek()
        if tok is None:
            return None
        upper = tok.upper()

        if upper == "FORWARD" or upper == "FD":
            self.advance()
            return ("forward", self.parse_expr())
        elif upper == "BACK" or upper == "BK":
            self.advance()
            return ("back", self.parse_expr())
        elif upper == "RIGHT" or upper == "RT":
            self.advance()
            return ("right", self.parse_expr())
        elif upper == "LEFT" or upper == "LT":
            self.advance()
            return ("left", self.parse_expr())
        elif upper == "PENUP" or upper == "PU":
            self.advance()
            return ("penup",)
        elif upper == "PENDOWN" or upper == "PD":
            self.advance()
            return ("pendown",)
        elif upper == "SETPENCOLOR" or upper == "SETPC":
            self.advance()
            return ("setpencolor", self.parse_expr())
        elif upper == "SETPENWIDTH" or upper == "SETPW":
            self.advance()
            return ("setpenwidth", self.parse_expr())
        elif upper == "HOME":
            self.advance()
            return ("home",)
        elif upper == "CLEARSCREEN" or upper == "CS":
            self.advance()
            return ("clearscreen",)
        elif upper == "HIDETURTLE" or upper == "HT":
            self.advance()
            return ("hideturtle",)
        elif upper == "SHOWTURTLE" or upper == "ST":
            self.advance()
            return ("showturtle",)
        elif upper == "SETXY" or upper == "SETPOS":
            self.advance()
            x_expr = self.parse_expr()
            y_expr = self.parse_expr()
            return ("setxy", x_expr, y_expr)
        elif upper == "SETHEADING" or upper == "SETH":
            self.advance()
            return ("setheading", self.parse_expr())
        elif upper == "REPEAT":
            self.advance()
            count = self.parse_expr()
            body = self.parse_block()
            return ("repeat", count, body)
        elif upper == "FOR":
            # FOR [var start end step] [body]
            self.advance()
            self.expect("[")
            varname = self.advance()
            start = self.parse_expr()
            end = self.parse_expr()
            # step is optional
            if self.peek() != "]":
                step = self.parse_expr()
            else:
                step = ("num", 1)
            self.expect("]")
            body = self.parse_block()
            return ("for", varname, start, end, step, body)
        elif upper == "IF":
            self.advance()
            cond = self.parse_expr()
            true_body = self.parse_block()
            # Check for optional ELSE or second block (IFELSE style)
            if self.peek() and self.peek() == "[":
                false_body = self.parse_block()
                return ("ifelse", cond, true_body, false_body)
            return ("if", cond, true_body)
        elif upper == "IFELSE":
            self.advance()
            cond = self.parse_expr()
            true_body = self.parse_block()
            false_body = self.parse_block()
            return ("ifelse", cond, true_body, false_body)
        elif upper == "TO":
            self.advance()
            name = self.advance().upper()
            params: List[str] = []
            while self.peek() and self.peek().startswith(":"):
                params.append(self.advance()[1:].upper())
            body: List[Any] = []
            while self.peek() and self.peek().upper() != "END":
                s = self.parse_statement()
                if s is not None:
                    body.append(s)
            if self.at_end():
                raise LogoError(f"Procedure '{name}' missing END")
            self.expect("END")
            return ("to", name, params, body)
        elif upper == "MAKE":
            self.advance()
            # MAKE "varname value
            name_expr = self.parse_expr()
            val_expr = self.parse_expr()
            return ("make", name_expr, val_expr)
        elif upper == "PRINT":
            self.advance()
            return ("print", self.parse_expr())
        elif upper == "STOP":
            self.advance()
            return ("stop",)
        elif upper == "OUTPUT" or upper == "OP":
            self.advance()
            return ("output", self.parse_expr())
        else:
            # Try as procedure call — greedily consume args if arity known
            self.advance()
            args: List[Any] = []
            arity = self.proc_arities.get(upper, 0)
            for _ in range(arity):
                if self.at_end() or self.peek() in ("]", ")"):
                    break
                args.append(self.parse_expr())
            return ("call", upper, args)

    # ---- Expression parser (with operator precedence) ----

    def parse_expr(self) -> Any:
        return self._parse_comparison()

    def _parse_comparison(self) -> Any:
        left = self._parse_add_sub()
        while self.peek() in ("<", ">", "=", "<=", ">=", "<>"):
            op = self.advance()
            right = self._parse_add_sub()
            left = ("binop", op, left, right)
        return left

    def _parse_add_sub(self) -> Any:
        left = self._parse_mul_div()
        while self.peek() in ("+", "-"):
            op = self.advance()
            right = self._parse_mul_div()
            left = ("binop", op, left, right)
        return left

    def _parse_mul_div(self) -> Any:
        left = self._parse_unary()
        while self.peek() in ("*", "/"):
            op = self.advance()
            right = self._parse_unary()
            left = ("binop", op, left, right)
        return left

    def _parse_unary(self) -> Any:
        if self.peek() == "-":
            self.advance()
            operand = self._parse_atom()
            return ("neg", operand)
        return self._parse_atom()

    def _parse_atom(self) -> Any:
        tok = self.peek()
        if tok is None:
            raise LogoError("Unexpected end of input in expression")

        # Parenthesized expression or function call
        if tok == "(":
            self.advance()
            # Check if next token is a function name (not a number, not a var)
            inner = self.peek()
            if inner and not inner.startswith(":") and not inner.startswith('"'):
                try:
                    float(inner)
                    is_number = True
                except ValueError:
                    is_number = False
                if not is_number and inner not in ("+", "-", "*", "/", "(", ")"):
                    # Function call with explicit args: (FUNCNAME arg1 arg2 ...)
                    fname = self.advance().upper()
                    args = []
                    while self.peek() != ")":
                        args.append(self.parse_expr())
                    self.expect(")")
                    return ("call", fname, args)
            # Regular parenthesized expression
            expr = self.parse_expr()
            self.expect(")")
            return expr

        # Variable reference :varname
        if tok.startswith(":"):
            self.advance()
            return ("var", tok[1:].upper())

        # Quoted word "something
        if tok.startswith('"'):
            self.advance()
            return ("word", tok[1:])

        # Number
        try:
            val = float(tok)
            self.advance()
            if val == int(val):
                return ("num", int(val))
            return ("num", val)
        except ValueError:
            pass

        # Built-in reporters (functions that return values)
        upper = tok.upper()
        reporters_0 = {
            "XCOR", "YCOR", "HEADING", "REPCOUNT",
            "RANDOM", "PI",
        }
        reporters_1 = {
            "SIN", "COS", "TAN", "SQRT", "ABS", "INT",
            "ROUND", "RANDOM", "NOT",
        }
        reporters_2 = {
            "SUM", "DIFFERENCE", "PRODUCT", "QUOTIENT",
            "REMAINDER", "MODULO", "POWER", "AND", "OR",
        }

        if upper in ("XCOR", "YCOR", "HEADING", "PI"):
            self.advance()
            return ("reporter0", upper)

        if upper in reporters_1:
            self.advance()
            arg = self.parse_expr()
            return ("reporter1", upper, arg)

        if upper in reporters_2:
            self.advance()
            a = self.parse_expr()
            b = self.parse_expr()
            return ("reporter2", upper, a, b)

        if upper == "REPCOUNT":
            self.advance()
            return ("repcount",)

        # Unknown — treat as function call, greedily consume args if arity known
        self.advance()
        args = []
        arity = self.proc_arities.get(upper, 0)
        for _ in range(arity):
            if self.at_end() or self.peek() in ("]", ")"):
                break
            args.append(self.parse_expr())
        return ("call", upper, args)


# ---------------------------------------------------------------------------
# LOGO Interpreter
# ---------------------------------------------------------------------------

class StopSignal(Exception):
    """Raised by STOP command to exit a procedure."""
    pass


class OutputSignal(Exception):
    """Raised by OUTPUT command to return a value from a procedure."""
    def __init__(self, value: Any) -> None:
        self.value = value


@dataclass
class Procedure:
    """A user-defined LOGO procedure."""
    name: str
    params: List[str]
    body: List[Any]


class LogoInterpreter:
    """
    A LOGO language interpreter with turtle graphics.

    Supports the core LOGO command set: movement, pen control, repetition,
    procedure definition, variables, conditionals, and arithmetic.

    Multiple turtles can be created and switched between.
    """

    def __init__(self) -> None:
        self.turtles: Dict[str, Turtle] = {"default": Turtle(name="default")}
        self.current_turtle_name: str = "default"
        self.procedures: Dict[str, Procedure] = {}
        self.global_vars: Dict[str, Any] = {}
        self._local_vars_stack: List[Dict[str, Any]] = []
        self._repcount_stack: List[int] = []
        self._output: List[str] = []  # captured PRINT output
        self._step_limit: int = 0  # 0 = unlimited
        self._steps: int = 0

    @property
    def turtle(self) -> Turtle:
        return self.turtles[self.current_turtle_name]

    def add_turtle(self, name: str) -> Turtle:
        """Create and register a new turtle."""
        t = Turtle(name=name)
        self.turtles[name] = t
        return t

    def switch_turtle(self, name: str) -> None:
        if name not in self.turtles:
            raise LogoError(f"No turtle named '{name}'")
        self.current_turtle_name = name

    def remove_turtle(self, name: str) -> None:
        if name == "default":
            raise LogoError("Cannot remove the default turtle")
        if name not in self.turtles:
            raise LogoError(f"No turtle named '{name}'")
        del self.turtles[name]
        if self.current_turtle_name == name:
            self.current_turtle_name = "default"

    # ---- Variable access ----

    def _get_var(self, name: str) -> Any:
        name = name.upper()
        # Search local scopes from innermost out
        for frame in reversed(self._local_vars_stack):
            if name in frame:
                return frame[name]
        if name in self.global_vars:
            return self.global_vars[name]
        raise LogoError(f"Unknown variable '{name}'")

    def _set_var(self, name: str, value: Any) -> None:
        name = name.upper()
        # Set in innermost local scope if it exists there, else global
        for frame in reversed(self._local_vars_stack):
            if name in frame:
                frame[name] = value
                return
        self.global_vars[name] = value

    # ---- Expression evaluation ----

    def _eval(self, expr: Any) -> Any:
        if not isinstance(expr, tuple):
            return expr
        tag = expr[0]

        if tag == "num":
            return expr[1]
        elif tag == "word":
            return expr[1]
        elif tag == "var":
            return self._get_var(expr[1])
        elif tag == "neg":
            return -self._eval(expr[1])
        elif tag == "repcount":
            if self._repcount_stack:
                return self._repcount_stack[-1]
            return 0
        elif tag == "binop":
            op, left, right = expr[1], expr[2], expr[3]
            lv = self._eval(left)
            rv = self._eval(right)
            if op == "+":
                return lv + rv
            elif op == "-":
                return lv - rv
            elif op == "*":
                return lv * rv
            elif op == "/":
                if rv == 0:
                    raise LogoError("Division by zero")
                return lv / rv
            elif op == "<":
                return lv < rv
            elif op == ">":
                return lv > rv
            elif op == "=":
                return lv == rv
            elif op == "<=":
                return lv <= rv
            elif op == ">=":
                return lv >= rv
            elif op == "<>":
                return lv != rv
            else:
                raise LogoError(f"Unknown operator '{op}'")
        elif tag == "reporter0":
            name = expr[1]
            if name == "XCOR":
                return self.turtle.x
            elif name == "YCOR":
                return self.turtle.y
            elif name == "HEADING":
                return self.turtle.heading
            elif name == "PI":
                return math.pi
            else:
                raise LogoError(f"Unknown reporter '{name}'")
        elif tag == "reporter1":
            name = expr[1]
            val = self._eval(expr[2])
            if name == "SIN":
                return math.sin(math.radians(val))
            elif name == "COS":
                return math.cos(math.radians(val))
            elif name == "TAN":
                return math.tan(math.radians(val))
            elif name == "SQRT":
                return math.sqrt(val)
            elif name == "ABS":
                return abs(val)
            elif name == "INT":
                return int(val)
            elif name == "ROUND":
                return round(val)
            elif name == "RANDOM":
                # Deterministic for testing; for real randomness use random module
                import random as _random
                return _random.randint(0, int(val) - 1) if val > 0 else 0
            elif name == "NOT":
                return not val
            else:
                raise LogoError(f"Unknown reporter '{name}'")
        elif tag == "reporter2":
            name = expr[1]
            a = self._eval(expr[2])
            b = self._eval(expr[3])
            if name == "SUM":
                return a + b
            elif name == "DIFFERENCE":
                return a - b
            elif name == "PRODUCT":
                return a * b
            elif name == "QUOTIENT":
                return a / b if b != 0 else 0
            elif name == "REMAINDER" or name == "MODULO":
                return a % b if b != 0 else 0
            elif name == "POWER":
                return a ** b
            elif name == "AND":
                return a and b
            elif name == "OR":
                return a or b
            else:
                raise LogoError(f"Unknown reporter '{name}'")
        elif tag == "call":
            return self._call_proc(expr[1], expr[2])
        else:
            raise LogoError(f"Cannot evaluate '{expr}'")

    # ---- Statement execution ----

    def _exec(self, stmt: Any) -> None:
        self._steps += 1
        if self._step_limit and self._steps > self._step_limit:
            raise LogoError(
                f"Execution exceeded step limit of {self._step_limit}"
            )

        tag = stmt[0]
        t = self.turtle

        if tag == "forward":
            t.forward(self._eval(stmt[1]))
        elif tag == "back":
            t.back(self._eval(stmt[1]))
        elif tag == "right":
            t.right(self._eval(stmt[1]))
        elif tag == "left":
            t.left(self._eval(stmt[1]))
        elif tag == "penup":
            t.penup()
        elif tag == "pendown":
            t.pendown()
        elif tag == "setpencolor":
            t.setpencolor(str(self._eval(stmt[1])))
        elif tag == "setpenwidth":
            t.setpenwidth(float(self._eval(stmt[1])))
        elif tag == "home":
            t.home()
        elif tag == "clearscreen":
            t.clear()
            t.home()
        elif tag == "hideturtle":
            t.visible = False
        elif tag == "showturtle":
            t.visible = True
        elif tag == "setxy":
            x = self._eval(stmt[1])
            y = self._eval(stmt[2])
            t.setposition(x, y)
        elif tag == "setheading":
            t.setheading(self._eval(stmt[1]))
        elif tag == "repeat":
            count = int(self._eval(stmt[1]))
            body = stmt[2]
            for i in range(count):
                self._repcount_stack.append(i + 1)
                try:
                    self._exec_block(body)
                finally:
                    self._repcount_stack.pop()
        elif tag == "for":
            varname, start_e, end_e, step_e, body = (
                stmt[1], stmt[2], stmt[3], stmt[4], stmt[5]
            )
            start = self._eval(start_e)
            end = self._eval(end_e)
            step = self._eval(step_e)
            val = start
            while (step > 0 and val <= end) or (step < 0 and val >= end):
                self._local_vars_stack.append({varname.upper(): val})
                try:
                    self._exec_block(body)
                finally:
                    self._local_vars_stack.pop()
                val += step
        elif tag == "if":
            cond = self._eval(stmt[1])
            if cond:
                self._exec_block(stmt[2])
        elif tag == "ifelse":
            cond = self._eval(stmt[1])
            if cond:
                self._exec_block(stmt[2])
            else:
                self._exec_block(stmt[3])
        elif tag == "to":
            name, params, body = stmt[1], stmt[2], stmt[3]
            self.procedures[name] = Procedure(name=name, params=params, body=body)
        elif tag == "make":
            name = str(self._eval(stmt[1]))
            val = self._eval(stmt[2])
            self._set_var(name.upper(), val)
        elif tag == "print":
            val = self._eval(stmt[1])
            self._output.append(str(val))
        elif tag == "stop":
            raise StopSignal()
        elif tag == "output":
            raise OutputSignal(self._eval(stmt[1]))
        elif tag == "call":
            self._call_proc(stmt[1], stmt[2])
        else:
            raise LogoError(f"Unknown statement type '{tag}'")

    def _exec_block(self, stmts: List[Any]) -> None:
        for s in stmts:
            self._exec(s)

    def _call_proc(self, name: str, arg_exprs: List[Any]) -> Any:
        name = name.upper()
        if name not in self.procedures:
            raise LogoError(f"Unknown procedure '{name}'")
        proc = self.procedures[name]

        # Evaluate arguments
        args = [self._eval(a) for a in arg_exprs]

        # If we have fewer args than params, try parsing more from the token stream
        # This handles the case where the parser couldn't know the arity
        # For runtime, we pad with 0 or error
        if len(args) < len(proc.params):
            raise LogoError(
                f"Procedure '{name}' expects {len(proc.params)} arguments, "
                f"got {len(args)}"
            )

        # Push local frame
        frame: Dict[str, Any] = {}
        for pname, pval in zip(proc.params, args):
            frame[pname.upper()] = pval
        self._local_vars_stack.append(frame)

        try:
            self._exec_block(proc.body)
        except StopSignal:
            pass
        except OutputSignal as out:
            return out.value
        finally:
            self._local_vars_stack.pop()
        return None

    # ---- Public API ----

    def _prescan_arities(self, tokens: List[str]) -> Dict[str, int]:
        """
        Quick pre-scan of tokens to find TO...END definitions and their
        parameter counts, so the parser can greedily consume the right
        number of arguments for procedure calls.
        """
        arities: Dict[str, int] = {}
        # Include already-known procedures
        for name, proc in self.procedures.items():
            arities[name] = len(proc.params)
        i = 0
        while i < len(tokens):
            if tokens[i].upper() == "TO" and i + 1 < len(tokens):
                i += 1  # skip TO
                proc_name = tokens[i].upper()
                i += 1
                param_count = 0
                while i < len(tokens) and tokens[i].startswith(":"):
                    param_count += 1
                    i += 1
                arities[proc_name] = param_count
            else:
                i += 1
        return arities

    def execute(self, source: str) -> List[str]:
        """
        Parse and execute LOGO source code.

        Returns a list of PRINT output strings.
        """
        self._output = []
        self._steps = 0
        tokens = _tokenize(source)
        if not tokens:
            return []

        # Pre-scan to discover procedure arities for the parser
        arities = self._prescan_arities(tokens)

        parser = LogoParser(tokens, proc_arities=arities)
        program = parser.parse_program()

        # Two-pass: first register all procedure definitions, then execute
        other_stmts: List[Any] = []
        for stmt in program:
            if isinstance(stmt, tuple) and stmt[0] == "to":
                self._exec(stmt)  # register procedure
            else:
                other_stmts.append(stmt)

        for stmt in other_stmts:
            self._exec(stmt)

        return self._output

    def to_svg(
        self,
        width: int = 800,
        height: int = 600,
        background: str = "white",
        auto_scale: bool = True,
    ) -> str:
        """Export current drawing as an SVG string."""
        renderer = SVGRenderer(
            width=width,
            height=height,
            background=background,
            auto_scale=auto_scale,
        )
        return renderer.render(list(self.turtles.values()))

    def reset(self) -> None:
        """Reset interpreter state completely."""
        for t in self.turtles.values():
            t.reset()
        self.procedures.clear()
        self.global_vars.clear()
        self._local_vars_stack.clear()
        self._repcount_stack.clear()
        self._output.clear()
        self._steps = 0


# ---------------------------------------------------------------------------
# Microworld System
# ---------------------------------------------------------------------------

class Microworld:
    """
    A constrained LOGO environment — Papert's concept of a space where
    specific powerful ideas become accessible through exploration.

    A microworld wraps a LogoInterpreter and can:
    - Pre-define procedures available to the learner
    - Restrict which commands are allowed
    - Set step limits (so infinite recursion is caught gently)
    - Provide a description of the world and its intended explorations

    Example: a "Polygon microworld" might pre-define a POLYGON procedure
    and invite the learner to explore what happens when you nest polygons,
    discovering the Total Turtle Trip Theorem along the way.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        setup_code: str = "",
        allowed_commands: Optional[set] = None,
        step_limit: int = 100_000,
    ) -> None:
        self.name = name
        self.description = description
        self.setup_code = setup_code
        self.allowed_commands = allowed_commands  # None = all allowed
        self.step_limit = step_limit
        self.interpreter = LogoInterpreter()
        self.interpreter._step_limit = step_limit
        if setup_code:
            self.interpreter.execute(setup_code)

    def run(self, source: str) -> List[str]:
        """Execute code within this microworld's constraints."""
        if self.allowed_commands is not None:
            tokens = _tokenize(source)
            for tok in tokens:
                upper = tok.upper()
                # Check if it's a command (not a number, not a variable, etc.)
                if (
                    not tok.startswith(":")
                    and not tok.startswith('"')
                    and tok not in ("[", "]", "(", ")", "+", "-", "*", "/",
                                    "<", ">", "=", "<=", ">=", "<>")
                    and upper not in ("END",)
                ):
                    try:
                        float(tok)
                        continue  # it's a number
                    except ValueError:
                        pass
                    if (
                        upper not in self.allowed_commands
                        and upper not in self.interpreter.procedures
                    ):
                        raise LogoError(
                            f"Command '{tok}' is not available in the "
                            f"'{self.name}' microworld"
                        )
        return self.interpreter.execute(source)

    def to_svg(self, **kwargs: Any) -> str:
        return self.interpreter.to_svg(**kwargs)

    def reset(self) -> None:
        self.interpreter.reset()
        self.interpreter._step_limit = self.step_limit
        if self.setup_code:
            self.interpreter.execute(self.setup_code)


# ---------------------------------------------------------------------------
# Built-in Microworlds
# ---------------------------------------------------------------------------

def polygon_microworld() -> Microworld:
    """
    The Polygon Microworld.

    Explore regular polygons and discover the Total Turtle Trip Theorem:
    any closed polygon involves the turtle turning a total of 360 degrees.
    A square: REPEAT 4 [FD 100 RT 90]  (4 * 90 = 360)
    A triangle: REPEAT 3 [FD 100 RT 120]  (3 * 120 = 360)
    A hexagon: REPEAT 6 [FD 50 RT 60]  (6 * 60 = 360)
    """
    return Microworld(
        name="Polygons",
        description=textwrap.dedent("""\
            Explore regular polygons and discover the Total Turtle Trip Theorem.

            Try: REPEAT 4 [FD 100 RT 90]      -- a square
            Try: REPEAT 3 [FD 100 RT 120]     -- a triangle
            Try: REPEAT 6 [FD 50 RT 60]       -- a hexagon
            Try: REPEAT 360 [FD 1 RT 1]       -- a circle!

            What do all closed shapes have in common?
        """),
        setup_code=textwrap.dedent("""\
            TO POLYGON :SIDES :SIZE
                REPEAT :SIDES [FD :SIZE RT 360 / :SIDES]
            END

            TO CIRCLE :RADIUS
                REPEAT 360 [FD :RADIUS * PI / 180 RT 1]
            END
        """),
        allowed_commands={
            "FD", "FORWARD", "BK", "BACK", "RT", "RIGHT", "LT", "LEFT",
            "REPEAT", "PENUP", "PU", "PENDOWN", "PD", "HOME",
            "POLYGON", "CIRCLE", "PRINT",
            "SETPENCOLOR", "SETPC", "HIDETURTLE", "HT",
        },
    )


def fractal_microworld() -> Microworld:
    """
    The Fractal Microworld.

    Explore recursion and self-similarity. Pre-loaded with procedures
    for Koch curves, Sierpinski triangles, and fractal trees.
    """
    return Microworld(
        name="Fractals",
        description=textwrap.dedent("""\
            Explore recursion and self-similarity through fractal drawings.

            Available procedures:
              KOCH :SIZE :LEVEL       -- Koch snowflake curve
              SIERPINSKI :SIZE :LEVEL -- Sierpinski triangle
              TREE :SIZE :LEVEL       -- fractal tree
              SPIRAL :SIZE :ANGLE     -- logarithmic spiral

            Try different sizes and levels to see how complexity emerges
            from simple recursive rules.
        """),
        setup_code=textwrap.dedent("""\
            TO KOCH :SIZE :LEVEL
                IF :LEVEL = 0 [FD :SIZE STOP]
                KOCH :SIZE / 3 :LEVEL - 1
                LT 60
                KOCH :SIZE / 3 :LEVEL - 1
                RT 120
                KOCH :SIZE / 3 :LEVEL - 1
                LT 60
                KOCH :SIZE / 3 :LEVEL - 1
            END

            TO SNOWFLAKE :SIZE :LEVEL
                REPEAT 3 [KOCH :SIZE :LEVEL RT 120]
            END

            TO SIERPINSKI :SIZE :LEVEL
                IF :LEVEL = 0 [
                    REPEAT 3 [FD :SIZE RT 120]
                    STOP
                ]
                SIERPINSKI :SIZE / 2 :LEVEL - 1
                FD :SIZE / 2
                SIERPINSKI :SIZE / 2 :LEVEL - 1
                BK :SIZE / 2
                LT 60
                FD :SIZE / 2
                RT 60
                SIERPINSKI :SIZE / 2 :LEVEL - 1
                LT 60
                BK :SIZE / 2
                RT 60
            END

            TO TREE :SIZE :LEVEL
                IF :LEVEL = 0 [STOP]
                FD :SIZE
                LT 30
                TREE :SIZE * 0.7 :LEVEL - 1
                RT 60
                TREE :SIZE * 0.7 :LEVEL - 1
                LT 30
                BK :SIZE
            END

            TO SPIRAL :SIZE :ANGLE
                IF :SIZE < 1 [STOP]
                FD :SIZE
                RT :ANGLE
                SPIRAL :SIZE * 0.98 :ANGLE
            END
        """),
        step_limit=500_000,
    )


# ---------------------------------------------------------------------------
# Built-in Demo Programs
# ---------------------------------------------------------------------------

DEMOS: Dict[str, str] = {
    "koch_snowflake": textwrap.dedent("""\
        ; Koch Snowflake — one of the first fractals children can understand.
        ; A line becomes four lines, each 1/3 the length. Repeat recursively.
        ; The boundary is infinite but encloses finite area.

        TO KOCH :SIZE :LEVEL
            IF :LEVEL = 0 [FD :SIZE STOP]
            KOCH :SIZE / 3 :LEVEL - 1
            LT 60
            KOCH :SIZE / 3 :LEVEL - 1
            RT 120
            KOCH :SIZE / 3 :LEVEL - 1
            LT 60
            KOCH :SIZE / 3 :LEVEL - 1
        END

        TO SNOWFLAKE :SIZE :LEVEL
            REPEAT 3 [KOCH :SIZE :LEVEL RT 120]
        END

        HT
        PU
        BK 100
        LT 90
        FD 160
        RT 90
        PD
        SNOWFLAKE 320 4
    """),

    "sierpinski": textwrap.dedent("""\
        ; Sierpinski Triangle — self-similar at every scale.
        ; Remove the middle triangle, recurse on the three remaining.

        TO SIERPINSKI :SIZE :LEVEL
            IF :LEVEL = 0 [
                REPEAT 3 [FD :SIZE RT 120]
                STOP
            ]
            SIERPINSKI :SIZE / 2 :LEVEL - 1
            FD :SIZE / 2
            SIERPINSKI :SIZE / 2 :LEVEL - 1
            BK :SIZE / 2
            LT 60
            FD :SIZE / 2
            RT 60
            SIERPINSKI :SIZE / 2 :LEVEL - 1
            LT 60
            BK :SIZE / 2
            RT 60
        END

        HT
        PU BK 150 LT 90 FD 170 RT 90 PD
        SIERPINSKI 340 5
    """),

    "spiral": textwrap.dedent("""\
        ; A spiral — forward a bit, turn a bit, shrink a bit.
        ; Change the angle to get wildly different patterns.
        ; This is "playing turtle" — imagining yourself as the turtle.

        TO SPIRAL :SIZE :ANGLE
            IF :SIZE < 1 [STOP]
            FD :SIZE
            RT :ANGLE
            SPIRAL :SIZE * 0.98 :ANGLE
        END

        HT
        SPIRAL 200 91
    """),

    "tree": textwrap.dedent("""\
        ; Fractal Tree — recursion as branching.
        ; Go forward (trunk), turn left and recurse (left branch),
        ; turn right and recurse (right branch), back up.
        ; The turtle returns to where it started — a key insight.

        TO TREE :SIZE :LEVEL
            IF :LEVEL = 0 [STOP]
            FD :SIZE
            LT 30
            TREE :SIZE * 0.7 :LEVEL - 1
            RT 60
            TREE :SIZE * 0.7 :LEVEL - 1
            LT 30
            BK :SIZE
        END

        HT
        PU BK 180 PD
        TREE 120 8
    """),

    "star_polygon": textwrap.dedent("""\
        ; Star Polygons — connect every Kth vertex of an N-gon.
        ; When N and K are coprime, you get a single star.
        ; When they share a factor, you get multiple overlapping stars.
        ; This is modular arithmetic made visible.

        TO STAR :SIZE :POINTS :SKIP
            REPEAT :POINTS [
                FD :SIZE
                RT 360 / :POINTS * :SKIP
            ]
        END

        HT

        ; 5-pointed star (pentagram)
        STAR 200 5 2

        ; Move over and draw a 7-pointed star
        PU RT 90 FD 300 LT 90 PD
        STAR 200 7 3

        ; Move over and draw a 9-pointed star
        PU RT 90 FD 300 LT 90 PD
        STAR 200 9 4
    """),

    "polygon_exploration": textwrap.dedent("""\
        ; Total Turtle Trip Theorem exploration.
        ; Every closed polygon turns the turtle 360 degrees total.
        ; Watch: 3 sides * 120 = 360. 4 * 90 = 360. 5 * 72 = 360. Always 360!

        TO POLYGON :SIDES :SIZE
            REPEAT :SIDES [FD :SIZE RT 360 / :SIDES]
        END

        HT

        ; Triangle
        PU LT 90 FD 280 RT 90 PD
        POLYGON 3 120

        ; Square
        PU LT 90 BK 70 RT 90 PD
        POLYGON 4 100

        ; Pentagon
        PU LT 90 BK 130 RT 90 PD
        POLYGON 5 80

        ; Hexagon
        PU LT 90 BK 130 RT 90 PD
        POLYGON 6 60

        ; Approaching a circle
        PU LT 90 BK 100 RT 90 PD
        POLYGON 36 15
    """),

    "dragon_curve": textwrap.dedent("""\
        ; Dragon Curve — fold a strip of paper in half repeatedly,
        ; then unfold all folds to 90 degrees. The resulting shape
        ; is a fractal that tiles the plane.

        TO DRAGON :SIZE :LEVEL :SIGN
            IF :LEVEL = 0 [FD :SIZE STOP]
            DRAGON :SIZE :LEVEL - 1 1
            RT 90 * :SIGN
            DRAGON :SIZE :LEVEL - 1 -1
        END

        HT
        DRAGON 5 10 1
    """),

    "flower": textwrap.dedent("""\
        ; A flower made of overlapping arcs — showing how
        ; circles are just polygons with many sides.

        TO ARC :RADIUS :DEGREES
            REPEAT :DEGREES [
                FD :RADIUS * PI / 180
                RT 1
            ]
        END

        TO PETAL :SIZE
            ARC :SIZE 60
            RT 120
            ARC :SIZE 60
            RT 120
        END

        TO FLOWER :SIZE :PETALS
            REPEAT :PETALS [
                PETAL :SIZE
                RT 360 / :PETALS
            ]
        END

        HT
        FLOWER 100 8
    """),
}


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def run(source: str, **svg_kwargs: Any) -> str:
    """
    Execute LOGO source code and return SVG output.

    This is the simplest entry point — give it LOGO code, get an SVG string.

    Example::

        svg = logo.run("REPEAT 4 [FD 100 RT 90]")
        with open("square.svg", "w") as f:
            f.write(svg)
    """
    interp = LogoInterpreter()
    interp.execute(source)
    return interp.to_svg(**svg_kwargs)


def run_demo(name: str, **svg_kwargs: Any) -> str:
    """
    Run a built-in demo and return SVG output.

    Available demos:
        koch_snowflake, sierpinski, spiral, tree, star_polygon,
        polygon_exploration, dragon_curve, flower
    """
    if name not in DEMOS:
        available = ", ".join(sorted(DEMOS.keys()))
        raise LogoError(f"Unknown demo '{name}'. Available: {available}")
    return run(DEMOS[name], **svg_kwargs)


def list_demos() -> List[str]:
    """Return names of all built-in demos."""
    return sorted(DEMOS.keys())
