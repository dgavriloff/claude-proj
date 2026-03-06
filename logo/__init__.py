"""
LOGO and Turtle Geometry
========================

A Python implementation of Seymour Papert's LOGO language and Turtle
Graphics, producing SVG output. Includes a LOGO interpreter, multiple
turtle support, built-in fractal demos, and a microworld system.

Quick start::

    import logo

    # Draw a square
    svg = logo.run("REPEAT 4 [FD 100 RT 90]")

    # Run a built-in demo
    svg = logo.run_demo("koch_snowflake")

    # Use the interpreter directly
    interp = logo.LogoInterpreter()
    interp.execute('''
        TO SPIRAL :SIZE :ANGLE
            IF :SIZE < 1 [STOP]
            FD :SIZE RT :ANGLE
            SPIRAL :SIZE * 0.98 :ANGLE
        END
        SPIRAL 200 91
    ''')
    svg = interp.to_svg()

    # Explore a microworld
    world = logo.fractal_microworld()
    world.run("SNOWFLAKE 300 3")
    svg = world.to_svg()

See ``logo.logo`` module docstring for historical context on Papert,
Piaget, constructionism, and the fate of LOGO in schools.
"""

from .logo import (
    # Core classes
    Turtle,
    TurtlePath,
    SVGRenderer,
    LogoInterpreter,
    LogoParser,
    LogoError,
    Procedure,
    # Microworlds
    Microworld,
    polygon_microworld,
    fractal_microworld,
    # Convenience
    run,
    run_demo,
    list_demos,
    DEMOS,
)

__all__ = [
    "Turtle",
    "TurtlePath",
    "SVGRenderer",
    "LogoInterpreter",
    "LogoParser",
    "LogoError",
    "Procedure",
    "Microworld",
    "polygon_microworld",
    "fractal_microworld",
    "run",
    "run_demo",
    "list_demos",
    "DEMOS",
]
