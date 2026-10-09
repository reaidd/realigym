"""Run with:  python -m pytest -q"""
import pytest

from core.i18n import MESSAGES, render
from core.models import load_library, open_review_items, t, validate
from core.recommend import Answers, recommend
from core.training import TopSet, suggest_next, warmup_sets


@pytest.fixture(scope="module")
def lib():
    return load_library()


# ------------------------------------------------------------ data integrity

def test_data_is_valid(lib):
    assert validate(lib) == []


def test_every_exercise_is_used_or_is_an_alternative(lib):
    used = {i.exercise_id for p in lib.programs.values() for v in p.variants
            for d in v.days for i in d.items}
    alts = {a for e in lib.exercises.values() for a in e.alternatives}
    assert set(lib.exercises) <= used | alts


def test_all_exercises_have_chinese_names(lib):
    assert all(e.name.get("zh") for e in lib.exercises.values())


def test_t_falls_back_to_english():
    assert t({"en": "Hello"}, "zh") == "Hello"


def test_review_markers_present(lib):
    refs = open_review_items(lib)
    assert refs["form-guide"]                # no form cues written yet
    assert refs["added-exercises"]


def test_program_a_has_three_gym_days_in_both_variants(lib):
    a = lib.programs["program_a"]
    assert {v.id for v in a.variants} == {"standard", "limited"}
    assert all(len(v.gym_days) == 3 for v in a.variants)


# ------------------------------------------------- guide examples, exactly

def test_warmup_compound_matches_guide():
    # Main Guide example 1: working up to an 80 kg squat
    sets = warmup_sets(80, "compound", min_weight=20)
    assert [(s.weight, s.reps) for s in sets] == [(20, 8), (40, 5), (60, 3), (70, 1)]
    assert sets[-1].optional


def test_warmup_isolation_matches_guide():
    # Main Guide example 2: working up to a 70 kg leg extension
    sets = warmup_sets(70, "isolation", increment=1)
    assert [(s.weight, s.reps) for s in sets] == [(35, 8), (49, 5), (63, 2)]


def test_warmup_light_weight_drops_duplicates():
    sets = warmup_sets(5, "compound")
    weights = [s.weight for s in sets]
    assert len(weights) == len(set(weights)) and all(w < 5 for w in weights)


def test_progression_matches_corrected_guide_example():
    # 35×5 → 35×6 → 35×7 → 35×8 → 37.5×5 → 37.5×6
    rng = (5, 8)
    assert suggest_next(TopSet(35, 5), rng).target_reps == 6
    assert suggest_next(TopSet(35, 7), rng).action == "hold"
    s = suggest_next(TopSet(35, 8), rng)
    assert (s.action, s.weight, s.target_reps) == ("increase", 37.5, 5)
    assert suggest_next(TopSet(37.5, 5), rng).target_reps == 6


def test_progression_first_time_and_below_range():
    assert suggest_next(None, (5, 8)).action == "start"
    s = suggest_next(TopSet(40, 3), (5, 8))
    assert (s.action, s.weight) == ("below_range", 40)


# ---------------------------------------------------------- recommender

def test_beginner_with_five_days_gets_program_a(lib):
    r = recommend(Answers(5, "beginner", "commercial"), lib)
    assert (r.program_id, r.variant_id) == ("program_a", "standard")
    assert "beginner_start_simple" in {x.code for x in r.reasons}


def test_intermediate_with_five_days_gets_program_b(lib):
    r = recommend(Answers(5, "intermediate", "commercial"), lib)
    assert r.program_id == "program_b"


def test_intermediate_with_three_days_gets_program_a(lib):
    assert recommend(Answers(3, "intermediate", "commercial"), lib).program_id == "program_a"


def test_limited_equipment_gets_clubhouse_variant(lib):
    r = recommend(Answers(5, "advanced", "limited"), lib)
    assert (r.program_id, r.variant_id) == ("program_a", "limited")


def test_too_few_days_and_time_warnings(lib):
    r = recommend(Answers(2, "beginner", "commercial", minutes_per_session=60, health_flags=True), lib)
    codes = {w.code for w in r.warnings}
    assert {"needs_more_days", "session_too_long", "health_check"} <= codes


def test_every_message_renders_in_both_languages(lib):
    r = recommend(Answers(2, "beginner", "limited", minutes_per_session=45, health_flags=True), lib)
    for reason in r.reasons + r.warnings:
        assert render(reason, "en") and render(reason, "zh")
    assert all({"en", "zh"} <= set(m) for m in MESSAGES.values())
