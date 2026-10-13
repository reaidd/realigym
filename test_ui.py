"""Smoke tests for every screen, signed out and signed in (test user, in-memory store)."""
import uuid

import pytest
from streamlit.testing.v1 import AppTest

from core.models import load_library
from ui.auth import TEST_USER_ENV

T = 30


def run(page=None, user=None, monkeypatch=None, **state):
    if monkeypatch is not None:
        if user:
            monkeypatch.setenv(TEST_USER_ENV, user)
        else:
            monkeypatch.delenv(TEST_USER_ENV, raising=False)
    at = AppTest.from_file("../app.py", default_timeout=T)
    for k, v in state.items():
        at.session_state[k] = v
    if page:
        at.switch_page(page)
    return at.run()


def new_user():
    uid = uuid.uuid4().hex[:8]
    return f"{uid}|{uid}@test.com|Test {uid}"


# ---------------------------------------------------------- signed out

@pytest.mark.parametrize("lang", ["en", "zh"])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_home_renders(lang, theme, monkeypatch):
    at = run(monkeypatch=monkeypatch, lang=lang, theme=theme)
    assert not at.exception
    assert any("RealiGym" in m.value for m in at.markdown)


def test_signed_out_programme_prompts_login(monkeypatch):
    at = run("views/program.py", monkeypatch=monkeypatch, view_program="program_a")
    assert not at.exception
    assert not any(b.key == "start_session" for b in at.button)


def test_onboarding_recommends_and_starts(monkeypatch):
    at = run("views/onboarding.py", monkeypatch=monkeypatch)
    at.radio(key="ob_days").set_value(5)
    at.radio(key="ob_exp").set_value("intermediate")
    at.button[-1].click()
    at = at.run()
    assert not at.exception
    assert at.session_state["rec"].program_id == "program_b"
    at.button(key="start").click().run()
    assert at.session_state["program"] == "program_b"


@pytest.mark.parametrize("prog,variant", [("program_a", "standard"), ("program_a", "limited"),
                                          ("program_b", "standard")])
def test_every_day_renders(prog, variant, monkeypatch):
    at = run("views/program.py", monkeypatch=monkeypatch, view_program=prog, program=prog, variant=variant)
    assert not at.exception
    v = load_library().programs[prog].variant(variant)
    for d in v.days:
        at.sidebar.radio(key=f"day_{prog}_{variant}").set_value(d.id).run()
        assert not at.exception, d.id
        assert len(at.expander) >= len(d.items)


def test_warmup_calculator_in_card(monkeypatch):
    at = run("views/program.py", monkeypatch=monkeypatch, view_program="program_a",
             program="program_a", variant="standard", day="B")
    at.number_input(key="ww_program_a_standard_B_0_0").set_value(80.0).run()
    assert not at.exception
    assert any("20 kg × 8" in m.value and "70 kg × 1" in m.value for m in at.markdown)


def test_review_page(monkeypatch):
    assert not run("views/review.py", monkeypatch=monkeypatch, lang="zh").exception


# ----------------------------------------------------------- signed in

def test_full_logging_flow(monkeypatch):
    user = new_user()
    at = run("views/program.py", user=user, monkeypatch=monkeypatch, view_program="program_a",
             program="program_a", variant="standard", day="A")
    assert not at.exception
    at.button(key="start_session").click().run()
    assert not at.exception
    assert any(b.key == "finish_session" for b in at.button)

    # log the first exercise (machine chest press): 35 kg × 8
    k = "program_a_standard_A_0_0"
    at.number_input(key=f"lw_{k}").set_value(35.0)
    at.number_input(key=f"lv_{k}").set_value(8)
    form_buttons = [b for b in at.button if b.proto.is_form_submitter and "log_" + k in b.proto.form_id]
    form_buttons[0].click().run()
    assert not at.exception
    assert any("35 kg × 8" in s.value for s in at.success)

    at.button(key="finish_session").click().run()
    assert not at.exception
    assert any(b.key == "start_session" for b in at.button)

    # next session suggests adding weight (hit top of 5–8)
    at.button(key="start_session").click().run()
    assert any("37.5" in m.value for m in at.markdown)
    assert at.number_input(key=f"lw_{k}").value == 37.5
    assert at.number_input(key=f"lv_{k}").value == 5

    # progress page shows the history
    at.switch_page("views/progress.py").run()
    assert not at.exception
    assert len(at.dataframe) == 1


def test_signed_in_prefs_saved_to_profile(monkeypatch):
    user = new_user()
    at = run(user=user, monkeypatch=monkeypatch)
    at.button(key="tb_theme").click().run()
    assert not at.exception
    store = at.session_state["store"]
    assert store.profile()["theme"] == "dark"


def test_progress_empty_and_signed_out(monkeypatch):
    assert not run("views/progress.py", user=new_user(), monkeypatch=monkeypatch).exception
    assert not run("views/progress.py", monkeypatch=monkeypatch).exception
