"""Warmup calculator and progressive overload — straight from the Main Guide."""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import rules


def round_to(x: float, increment: float) -> float:
    """Round to the nearest available weight increment (half rounds up)."""
    return round(math.floor(x / increment + 0.5) * increment, 3)


# ------------------------------------------------------------------ warmup

@dataclass(frozen=True)
class WarmupSet:
    weight: float
    reps: int
    optional: bool = False


def warmup_sets(
    working_weight: float,
    exercise_type: str,
    increment: float = rules.DEFAULT_INCREMENT_KG,
    min_weight: float = 0.0,
    include_optional: bool = True,
) -> list[WarmupSet]:
    """Pyramid warmup sets leading up to the working weight.

    Compound: 25 / 50 / 75 % (+ optional 87.5 %) for 8 / 5 / 3 (/ 1) reps.
    Isolation: 50 / 70 / 90 % for 8 / 5 / 2 reps.
    `min_weight` is e.g. 20 for an empty barbell. Duplicate or too-heavy sets are dropped,
    so very light working weights simply get fewer warmup sets.
    """
    if working_weight <= 0:
        return []
    out: list[WarmupSet] = []
    seen: set[float] = set()
    for frac, reps, optional in rules.WARMUP_PYRAMID[exercise_type]:
        if optional and not include_optional:
            continue
        w = max(min_weight, round_to(working_weight * frac, increment))
        if w <= 0 or w >= working_weight or w in seen:
            continue
        seen.add(w)
        out.append(WarmupSet(w, reps, optional))
    return out


# ------------------------------------------------------ progressive overload

@dataclass(frozen=True)
class TopSet:
    weight: float
    reps: int
    rir: int | None = None


@dataclass(frozen=True)
class Suggestion:
    action: str            # start | increase | hold | below_range
    weight: float | None   # suggested weight next session (None = find it with a warmup)
    target_reps: int


def suggest_next(
    last: TopSet | None,
    rep_range: tuple[int, int],
    increment: float = rules.DEFAULT_INCREMENT_KG,
) -> Suggestion:
    """Double progression: add reps each week until the top of the range, then add weight.

    Guide example (5–8 reps): 35×5 → 35×6 → 35×7 → 35×8 → 37.5×5 → 37.5×6 …
    """
    lo, hi = rep_range
    if last is None:
        return Suggestion("start", None, lo)
    if last.reps >= hi:
        return Suggestion("increase", round(last.weight + increment, 3), lo)
    if last.reps >= lo:
        return Suggestion("hold", last.weight, last.reps + 1)
    # Below the range: the guide is against sudden jumps, so keep the weight and build up.
    return Suggestion("below_range", last.weight, lo)
