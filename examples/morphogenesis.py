"""
Morphogenesis — conceptual prototype
====================================

A turn in the proposition: from ORGANIZING A POPULATION to the
ONTOGENESIS OF A SINGLE ENTITY.

Everything before this file answered "where does an entity belong
among others?". This file answers a different question:

        "how does one entity grow from its own identity into a form,
         and how does that form become a new identity?"

There is no population, no comparison, no sorting here. There is one
seed and a law of growth. This is the framework's dynamic-identity
hypothesis given a concrete mechanism — a deterministic L-system
(Lindenmayer, 1968), the standard model of how plants and fractals
unfold from a single symbol.

Mapping to the Recognition Organization framework:

    Identity        : the axiom — the seed the organism starts from
    Internal Logic  : the growth rule — how each part rewrites itself
    Recognition     : each symbol recognizing what it becomes next
                      (self-application, never comparison to a neighbor)
    Universe        : a generation — the context that hosts one step
                      of unfolding
    Form            : the string produced by one generation
    New Identity    : that form, which becomes the seed of the next
                      universe

Form → Identity → Form. Ontogenesis as recursion: each generation is
a new universe calibrated for the organism as it has just become.

The 'growth' relation MAY be:
  - deterministic (an L-system) — implemented here, and testable;
  - context-sensitive (environment feeds back) — a hypothesis noted at
    the end, the reaction-diffusion direction.

Run:  python3 recognition_morphogenesis.py       (self-test included)
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ==========================================================
# ORGANISM — identity precedes form
# ==========================================================
@dataclass
class Organism:
    """
    A single entity defined entirely by its own identity:
      - axiom : the initial form (the seed)
      - rules : how each symbol rewrites itself while growing
    No other organism is ever consulted.
    """
    axiom: str
    rules: Dict[str, str]

    def growth_rule(self, symbol: str) -> str:
        """
        Internal logic: a symbol recognizes what it becomes.
        A symbol with no rule is terminal — it keeps itself
        (structural constants like '+', '-', '[', ']').
        """
        return self.rules.get(symbol, symbol)


# ==========================================================
# UNFOLDING — one universe = one generation
# ==========================================================
@dataclass
class Ontogenesis:
    organism: Organism
    history: List[str] = field(default_factory=list)

    def unfold(self, generations: int) -> str:
        """
        Grow the organism for N generations. Each generation is a
        fresh universe: the current form is read symbol by symbol,
        every symbol becomes what its own logic dictates, and the
        concatenated result is the new identity that seeds the next.
        """
        form = self.organism.axiom
        self.history = [form]
        for _ in range(generations):
            form = "".join(self.organism.growth_rule(s) for s in form)
            self.history.append(form)
        return form


# ==========================================================
# INTERPRETATION — reading a form as a shape (turtle geometry)
# ==========================================================
class TurtleReader:
    """
    A form is just a string until it is *interpreted*. The turtle
    gives the form a body: F draws forward, +/- turn, [ ] branch.
    Interpretation is another recognition rule over the grown identity.
    """

    def __init__(self, angle_degrees: float = 25.0, step: float = 1.0):
        self.angle = math.radians(angle_degrees)
        self.step = step

    def trace(self, form: str) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        x, y, heading = 0.0, 0.0, math.pi / 2   # start pointing up
        stack: List[Tuple[float, float, float]] = []
        segments = []
        for s in form:
            if s == "F":
                nx = x + self.step * math.cos(heading)
                ny = y + self.step * math.sin(heading)
                segments.append(((x, y), (nx, ny)))
                x, y = nx, ny
            elif s == "+":
                heading += self.angle
            elif s == "-":
                heading -= self.angle
            elif s == "[":
                stack.append((x, y, heading))
            elif s == "]":
                x, y, heading = stack.pop()
        return segments

    def render_ascii(self, form: str, width: int = 60, height: int = 24) -> str:
        segments = self.trace(form)
        if not segments:
            return "(empty form)"
        pts = [p for seg in segments for p in seg]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        sx = (width - 1) / (maxx - minx) if maxx > minx else 0.0
        sy = (height - 1) / (maxy - miny) if maxy > miny else 0.0
        grid = [[" "] * width for _ in range(height)]

        def plot(px, py):
            cx = int((px - minx) * sx)
            cy = height - 1 - int((py - miny) * sy)
            if 0 <= cx < width and 0 <= cy < height:
                grid[cy][cx] = "*"

        # sample each segment so the ascii curve stays connected
        for (x0, y0), (x1, y1) in segments:
            steps = max(1, int(math.hypot((x1 - x0) * sx, (y1 - y0) * sy)))
            for k in range(steps + 1):
                t = k / steps
                plot(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
        return "\n".join("".join(row) for row in grid)


# ==========================================================
# SELF-TEST
# ==========================================================
if __name__ == "__main__":

    # ---- Organism 1: an algae (Lindenmayer's original) ------------
    algae = Organism(axiom="A", rules={"A": "AB", "B": "A"})
    onto = Ontogenesis(algae)
    onto.unfold(7)

    print("=== Algae ontogenesis (A→AB, B→A) ===")
    lengths = [len(f) for f in onto.history]
    for gen, (form, n) in enumerate(zip(onto.history, lengths)):
        shown = form if len(form) <= 34 else form[:31] + "..."
        print(f"  gen {gen}: len={n:3d}  {shown}")

    # Lindenmayer's algae grows by the Fibonacci sequence — a fact
    # that emerges from the identity alone, testable without any oracle.
    fib = [1, 2, 3, 5, 8, 13, 21, 34]   # Fibonacci from the 2nd term
    assert lengths == fib, f"expected Fibonacci growth, got {lengths}"
    assert all(lengths[i] == lengths[i - 1] + lengths[i - 2]
               for i in range(2, len(lengths))), "not a Fibonacci recurrence"
    print("  -> generation lengths follow Fibonacci (emergent, verified)")

    # Determinism: identity fully determines form. Same seed, same organism.
    assert Ontogenesis(algae).unfold(7) == onto.history[-1]

    # ---- Organism 2: a fractal plant, given a body ----------------
    plant = Organism(
        axiom="X",
        rules={"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"},
    )
    form = Ontogenesis(plant).unfold(4)
    reader = TurtleReader(angle_degrees=25.0)
    print("\n=== Fractal plant, generation 4 (form interpreted as shape) ===")
    print(reader.render_ascii(form, width=60, height=24))

    # The grown identity has real structure: it branches.
    assert form.count("[") == form.count("]") > 0, "branching structure expected"
    assert len(reader.trace(form)) > 0, "form should trace a non-empty body"

    # ---- Form becomes a new identity ------------------------------
    # Generation k is literally the axiom of a shorter unfolding that
    # reaches the same place — identity and form are interchangeable.
    mid = Ontogenesis(algae).unfold(4)                 # form after 4 gens
    continued = Ontogenesis(Organism(mid, algae.rules)).unfold(3)
    assert continued == onto.history[-1], "form is not reusable as identity"
    print("\nForm-as-identity verified: gen4 form reseeded + 3 gens == gen7 form.")

    print("\nAll tests passed: one entity unfolds from its identity alone,")
    print("growth is deterministic, length growth is emergent (Fibonacci),")
    print("form gains a body, and each form is reusable as a new identity.")

    # ---- Hypothesis noted, not implemented ------------------------
    # Context-sensitive growth (a symbol's rewrite depends on the
    # universe around it -> reaction-diffusion / Turing patterns) is
    # the next direction. Here growth is context-free: the organism
    # unfolds purely from within.
