"""Rough session length estimates, so the app (and recommender) can be realistic about time."""
from __future__ import annotations

from . import rules
from .models import Day, Library

SET_WORK_MIN = 0.75        # ~6 reps × ~6 s tempo, plus setup
WARMUP_SET_MIN = 1.25      # a warmup set plus loading weights
TRANSITION_MIN = 1.0       # moving between exercises
DYNAMIC_STRETCH_MIN = 8    # the guide's dynamic stretch list
COOLDOWN_MIN = 5           # a few static stretches
STEP_SECONDS = 1.0         # carries


def _mid(rng: tuple[float, float]) -> float:
    return (rng[0] + rng[1]) / 2


def estimate_minutes(
    day: Day,
    lib: Library,
    isolation_sets: int | None = None,
    warmup_every_exercise: bool = True,
) -> int:
    """Estimate total minutes for a day, including warmup and cooldown.

    isolation_sets: override sets for isolation exercises (the guide's short-on-time option is 2).
    warmup_every_exercise: the guide's routine; False = only the first exercise of each group.
    """
    total = rules.GENERAL_WARMUP_MIN + DYNAMIC_STRETCH_MIN + COOLDOWN_MIN
    for group in day.groups:
        for idx, item in enumerate(group.items):
            ex = lib.exercise(item.exercise_id)
            sets = item.sets
            if isolation_sets is not None and ex.type == "isolation":
                sets = min(sets, isolation_sets)

            if item.unit == "seconds":
                work = item.range[1] / 60
            elif item.unit == "steps":
                work = item.range[1] * STEP_SECONDS / 60
            else:
                work = SET_WORK_MIN

            rest = _mid(rules.REST_MIN[ex.type])
            total += sets * work + (sets - 1) * rest + TRANSITION_MIN

            needs_warmup = item.unit == "reps" and "bodyweight" not in ex.equipment
            if needs_warmup and (warmup_every_exercise or idx == 0):
                n = len([w for w in rules.WARMUP_PYRAMID[ex.type] if not w[2]])
                total += n * WARMUP_SET_MIN
    return round(total)
