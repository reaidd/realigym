"""Smoke tests for every screen, in both languages and themes."""
import pytest
from streamlit.testing.v1 import AppTest

T = 30


def run(page=None, **state):
    at = AppTest.from_file("../app.py", default_timeout=T)
    for k, v in state.items():
        at.session_state[k] = v
    if page:
        at.switch_page(page)
    return at.run()


@pytest.mark.parametrize("lang", ["en", "zh"])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_home_renders(lang, theme):
    at = run(lang=lang, theme=theme)
    assert not at.exception
    assert any("RealiGym" in m.value for m in at.markdown)


def test_home_with_programme_shows_today():
    at = run(program="program_a", variant="limited")
    assert not at.exception
    assert any(b.key == "open_today" for b in at.button)


def test_onboarding_recommends_and_starts():
    at = run("views/onboarding.py")
    at.radio(key="ob_days").set_value(5)
    at.radio(key="ob_exp").set_value("intermediate")
    at.button[-1].click()            # form submit is the last button rendered
    at = at.run()
    assert not at.exception
    assert at.session_state["rec"].program_id == "program_b"
    at.button(key="start").click().run()
    assert at.session_state["program"] == "program_b"


@pytest.mark.parametrize("prog,variant", [("program_a", "standard"), ("program_a", "limited"),
                                          ("program_b", "standard")])
def test_every_day_renders(prog, variant):
    at = run("views/program.py", view_program=prog, program=prog, variant=variant)
    assert not at.exception
    # click through every day by its id
    from core.models import load_library
    v = load_library().programs[prog].variant(variant)
    for d in v.days:
        at.sidebar.radio(key=f"day_{prog}_{variant}").set_value(d.id).run()
        assert not at.exception, d.id
        assert len(at.expander) >= len(d.items)


def test_warmup_calculator_in_card():
    at = run("views/program.py", view_program="program_a", program="program_a",
             variant="standard", day="B")
    key = "ww_program_a_standard_B_0_0"         # barbell squat
    at.number_input(key=key).set_value(80.0).run()
    assert not at.exception
    assert any("20 kg × 8" in m.value and "70 kg × 1" in m.value for m in at.markdown)


def test_review_page():
    at = run("views/review.py", lang="zh")
    assert not at.exception
