"""Data models and loader for the RealiGym content files in data/."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

REVIEW_MARK = "🔍"
UNITS = {"reps", "seconds", "steps"}
SUPERSET = {"must", "optional", "never"}
DAY_KINDS = {"gym", "rest_core"}
EX_TYPES = {"compound", "isolation"}
EQUIPMENT_SETUPS = {"commercial", "limited"}
LEVELS = {"beginner", "intermediate", "advanced"}


def t(text: dict | None, lang: str = "en") -> str:
    """Pick a language from an {en, zh} dict, falling back to English."""
    if not text:
        return ""
    return text.get(lang) or text.get("en", "")


@dataclass(frozen=True)
class ReviewItem:
    id: str
    title: str
    note: str


@dataclass(frozen=True)
class Exercise:
    id: str
    name: dict
    type: str
    equipment: tuple[str, ...]
    muscles: tuple[str, ...]
    alternatives: tuple[str, ...] = ()
    video_url: str | None = None
    form_cues: tuple[dict, ...] = ()
    review: tuple[str, ...] = ()

    @property
    def review_ids(self) -> tuple[str, ...]:
        """Explicit review ids, plus 'form-guide' while form cues are missing."""
        ids = list(self.review)
        if not self.form_cues and "form-guide" not in ids:
            ids.append("form-guide")
        return tuple(ids)


@dataclass(frozen=True)
class Item:
    exercise_id: str
    sets: int
    range: tuple[int, int]
    unit: str = "reps"
    note: dict | None = None
    optional: bool = False
    review: tuple[str, ...] = ()


@dataclass(frozen=True)
class Group:
    label: dict
    items: tuple[Item, ...]
    superset: str = "optional"


@dataclass(frozen=True)
class Day:
    id: str
    name: dict
    groups: tuple[Group, ...]
    kind: str = "gym"
    note: dict | None = None

    @property
    def items(self) -> tuple[Item, ...]:
        return tuple(i for g in self.groups for i in g.items)


@dataclass(frozen=True)
class Variant:
    id: str
    name: dict
    equipment: str
    schedule: tuple[str, ...]
    days: tuple[Day, ...]
    note: dict | None = None

    def day(self, day_id: str) -> Day:
        return next(d for d in self.days if d.id == day_id)

    @property
    def gym_days(self) -> tuple[Day, ...]:
        return tuple(d for d in self.days if d.kind == "gym")


@dataclass(frozen=True)
class Program:
    id: str
    name: dict
    summary: dict
    days_per_week: int
    levels: tuple[str, ...]
    variants: tuple[Variant, ...]
    pros: tuple[dict, ...] = ()
    cons: tuple[dict, ...] = ()
    image: str | None = None       # optional intro image path/URL; the app draws the week if empty

    def variant(self, variant_id: str) -> Variant:
        return next(v for v in self.variants if v.id == variant_id)

    def variant_for(self, equipment: str) -> Variant | None:
        return next((v for v in self.variants if v.equipment == equipment), None)


@dataclass(frozen=True)
class Library:
    exercises: dict[str, Exercise]
    programs: dict[str, Program]
    review_items: dict[str, ReviewItem] = field(default_factory=dict)

    def exercise(self, exercise_id: str) -> Exercise:
        return self.exercises[exercise_id]


# ---------------------------------------------------------------- parsing

def _item(raw: dict) -> Item:
    lo, hi = raw["range"]
    return Item(
        exercise_id=raw["ex"],
        sets=int(raw["sets"]),
        range=(int(lo), int(hi)),
        unit=raw.get("unit", "reps"),
        note=raw.get("note"),
        optional=bool(raw.get("optional", False)),
        review=tuple(raw.get("review", ())),
    )


def _day(raw: dict) -> Day:
    return Day(
        id=raw["id"],
        name=raw["name"],
        kind=raw.get("kind", "gym"),
        note=raw.get("note"),
        groups=tuple(
            Group(
                label=g["label"],
                superset=g.get("superset", "optional"),
                items=tuple(_item(i) for i in g["items"]),
            )
            for g in raw["groups"]
        ),
    )


def _program(raw: dict) -> Program:
    return Program(
        id=raw["id"],
        name=raw["name"],
        summary=raw["summary"],
        days_per_week=int(raw["days_per_week"]),
        levels=tuple(raw["levels"]),
        pros=tuple(raw.get("pros", ())),
        cons=tuple(raw.get("cons", ())),
        image=raw.get("image"),
        variants=tuple(
            Variant(
                id=v["id"],
                name=v["name"],
                equipment=v["equipment"],
                note=v.get("note"),
                schedule=tuple(v["schedule"]),
                days=tuple(_day(d) for d in v["days"]),
            )
            for v in raw["variants"]
        ),
    )


def load_library(data_dir: Path = DATA_DIR) -> Library:
    exercises_raw = yaml.safe_load((data_dir / "exercises.yaml").read_text(encoding="utf-8"))
    programs_raw = yaml.safe_load((data_dir / "programs.yaml").read_text(encoding="utf-8"))
    review_raw = yaml.safe_load((data_dir / "review.yaml").read_text(encoding="utf-8")) or []

    exercises: dict[str, Exercise] = {}
    for e in exercises_raw:
        if e["id"] in exercises:
            raise ValueError(f"Duplicate exercise id: {e['id']}")
        exercises[e["id"]] = Exercise(
            id=e["id"],
            name=e["name"],
            type=e["type"],
            equipment=tuple(e["equipment"]),
            muscles=tuple(e["muscles"]),
            alternatives=tuple(e.get("alternatives", ())),
            video_url=e.get("video_url"),
            form_cues=tuple(e.get("form_cues", ())),
            review=tuple(e.get("review", ())),
        )

    programs = {p["id"]: _program(p) for p in programs_raw["programs"]}
    review = {r["id"]: ReviewItem(r["id"], r["title"], r["note"].strip()) for r in review_raw}
    return Library(exercises=exercises, programs=programs, review_items=review)


@lru_cache(maxsize=1)
def get_library() -> Library:
    """Cached library for the app. Call get_library.cache_clear() after editing data."""
    return load_library()


# ------------------------------------------------------------- validation

def validate(lib: Library) -> list[str]:
    """Return a list of human-readable problems in the data (empty list = all good)."""
    errors: list[str] = []
    review_ids = set(lib.review_items)

    def check_review(ids, where):
        for r in ids:
            if r not in review_ids:
                errors.append(f"{where}: unknown review id '{r}'")

    for ex in lib.exercises.values():
        where = f"exercise {ex.id}"
        if ex.type not in EX_TYPES:
            errors.append(f"{where}: bad type '{ex.type}'")
        if not ex.name.get("en"):
            errors.append(f"{where}: missing English name")
        for alt in ex.alternatives:
            if alt not in lib.exercises:
                errors.append(f"{where}: unknown alternative '{alt}'")
            if alt == ex.id:
                errors.append(f"{where}: lists itself as an alternative")
        check_review(ex.review_ids, where)

    for p in lib.programs.values():
        if not set(p.levels) <= LEVELS:
            errors.append(f"program {p.id}: bad levels {p.levels}")
        for v in p.variants:
            vw = f"{p.id}/{v.id}"
            if v.equipment not in EQUIPMENT_SETUPS:
                errors.append(f"{vw}: bad equipment '{v.equipment}'")
            day_ids = [d.id for d in v.days]
            if len(day_ids) != len(set(day_ids)):
                errors.append(f"{vw}: duplicate day ids")
            if len(v.schedule) != 7:
                errors.append(f"{vw}: schedule must have 7 slots (Sun→Sat)")
            for slot in v.schedule:
                if slot != "rest" and slot not in day_ids:
                    errors.append(f"{vw}: schedule slot '{slot}' is not a day")
            gym_in_schedule = [s for s in v.schedule if s in {d.id for d in v.gym_days}]
            if len(gym_in_schedule) != p.days_per_week:
                errors.append(
                    f"{vw}: schedule has {len(gym_in_schedule)} gym days, "
                    f"program says {p.days_per_week}"
                )
            for d in v.days:
                dw = f"{vw}/{d.id}"
                if d.kind not in DAY_KINDS:
                    errors.append(f"{dw}: bad kind '{d.kind}'")
                for g in d.groups:
                    if g.superset not in SUPERSET:
                        errors.append(f"{dw}: bad superset '{g.superset}'")
                    if g.superset == "must" and len(g.items) != 2:
                        errors.append(f"{dw}: a 'must' superset needs exactly 2 exercises")
                    for it in g.items:
                        iw = f"{dw}/{it.exercise_id}"
                        if it.exercise_id not in lib.exercises:
                            errors.append(f"{iw}: unknown exercise")
                        if it.unit not in UNITS:
                            errors.append(f"{iw}: bad unit '{it.unit}'")
                        lo, hi = it.range
                        if not (0 < lo <= hi):
                            errors.append(f"{iw}: bad range {it.range}")
                        if it.sets < 1:
                            errors.append(f"{iw}: sets must be ≥ 1")
                        check_review(it.review, iw)
    return errors


def open_review_items(lib: Library) -> dict[str, list[str]]:
    """Map each review id → list of places that reference it (for a 🔍 checklist page)."""
    refs: dict[str, list[str]] = {r: [] for r in lib.review_items}
    for ex in lib.exercises.values():
        for r in ex.review_ids:
            refs.setdefault(r, []).append(f"exercise:{ex.id}")
    for p in lib.programs.values():
        for v in p.variants:
            for d in v.days:
                for it in d.items:
                    for r in it.review:
                        refs.setdefault(r, []).append(f"{p.id}/{v.id}/{d.id}/{it.exercise_id}")
    return refs
