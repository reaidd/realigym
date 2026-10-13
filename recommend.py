"""Recommend a programme from onboarding answers.

Programmes carry tags (days_per_week, levels, variant equipment), so adding a new
programme to programs.yaml needs no changes here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import rules
from .duration import estimate_minutes
from .models import Library


@dataclass(frozen=True)
class Answers:
    days_per_week: int
    experience: str                    # beginner | intermediate | advanced
    equipment: str                     # commercial | limited
    minutes_per_session: int | None = None
    health_flags: bool = False         # injuries / heart or blood pressure issues etc.


@dataclass(frozen=True)
class Reason:
    code: str
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Recommendation:
    program_id: str
    variant_id: str
    reasons: tuple[Reason, ...]
    warnings: tuple[Reason, ...]
    others: tuple[str, ...]            # other programmes the user can still browse


def _score(prog, a: Answers) -> float:
    level = 2.0 if a.experience in prog.levels else 0.0
    usage = prog.days_per_week / max(a.days_per_week, 1)   # use more of the available days
    return level + usage


def recommend(a: Answers, lib: Library) -> Recommendation:
    progs = list(lib.programs.values())
    warnings: list[Reason] = []
    reasons: list[Reason] = []

    fits = [p for p in progs if p.days_per_week <= a.days_per_week and p.variant_for(a.equipment)]
    if not fits:
        # Nothing fits both constraints — relax days first, then equipment.
        fits = [p for p in progs if p.variant_for(a.equipment)]
        if fits:
            fits = [min(fits, key=lambda p: p.days_per_week)]
            warnings.append(Reason("needs_more_days", {"days": fits[0].days_per_week}))
        else:
            fits = [min(progs, key=lambda p: p.days_per_week)]
            warnings.append(Reason("equipment_mismatch"))

    best = max(fits, key=lambda p: _score(p, a))
    variant = best.variant_for(a.equipment) or best.variants[0]

    if best.days_per_week <= a.days_per_week:
        reasons.append(Reason("fits_days", {"days": best.days_per_week, "available": a.days_per_week}))
    if a.experience in best.levels:
        reasons.append(Reason("level_match", {"level": a.experience}))
    if a.experience == "beginner" and best.days_per_week < a.days_per_week:
        reasons.append(Reason("beginner_start_simple"))
    if variant.equipment == "limited":
        reasons.append(Reason("limited_variant"))

    if a.minutes_per_session:
        longest = max(estimate_minutes(d, lib) for d in variant.gym_days)
        if longest > a.minutes_per_session:
            trimmed = max(
                estimate_minutes(d, lib, isolation_sets=rules.SHORT_ON_TIME_ISOLATION_SETS)
                for d in variant.gym_days
            )
            warnings.append(Reason("session_too_long", {
                "estimate": longest, "available": a.minutes_per_session, "trimmed": trimmed,
            }))

    if a.health_flags:
        warnings.append(Reason("health_check"))

    others = tuple(p.id for p in progs if p.id != best.id)
    return Recommendation(best.id, variant.id, tuple(reasons), tuple(warnings), others)
