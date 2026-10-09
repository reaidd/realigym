"""Reusable interface pieces."""
from __future__ import annotations

import html
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from core import rules
from core.models import REVIEW_MARK, Day, Exercise, Item, Variant, get_library, t
from core.training import warmup_sets
from ui import state
from ui.strings import tr

TIMEZONE = ZoneInfo("Asia/Hong_Kong")   # where "today" is decided


def lang() -> str:
    return st.session_state.get("lang", "en")


def today_index() -> int:
    """0 = Sunday … 6 = Saturday, matching programme schedules."""
    return (datetime.now(TIMEZONE).weekday() + 1) % 7


def esc(text: str) -> str:
    return html.escape(text or "")


# ---------------------------------------------------------------- toolbar

def toolbar() -> None:
    left, a, b, c, d = st.columns([3, 1.7, 1.2, 1.1, 1.1], vertical_alignment="center")
    with left:
        if st.button(tr("nav_home"), key="tb_home", type="tertiary"):
            st.switch_page("views/home.py")
    with a:
        if st.button(tr("nav_review"), key="tb_review", type="tertiary"):
            st.switch_page("views/review.py")
    with b:
        if st.button(tr("lang_switch"), key="tb_lang", use_container_width=True):
            state.set_pref("lang", "zh" if lang() == "en" else "en")
            st.rerun()
    with c:
        dark = st.session_state.get("theme") == "dark"
        if st.button(tr("theme_light") if dark else tr("theme_dark"), key="tb_theme",
                     use_container_width=True):
            state.set_pref("theme", "light" if dark else "dark")
            st.rerun()
    with d:
        st.button(tr("login"), key="tb_login", disabled=True, help=tr("login_help"),
                  use_container_width=True)


# ------------------------------------------------------------- week strip

def week_strip(variant: Variant, highlight_today: bool = True) -> str:
    days = {d.id: d for d in variant.days}
    names = tr("weekdays")
    today = today_index()
    slots = []
    for i, slot in enumerate(variant.schedule):
        if slot == "rest":
            cls, label = "rest", "–"
        else:
            cls = "core" if days[slot].kind == "rest_core" else "gym"
            label = tr("core_short") if days[slot].kind == "rest_core" else slot
        if highlight_today and i == today:
            cls += " today"
        slots.append(f'<div class="rg-slot {cls}"><span class="rg-wd">{names[i]}</span>'
                     f'<span class="rg-id">{esc(label)}</span></div>')
    return f'<div class="rg-week" role="img" aria-label="Weekly schedule">{"".join(slots)}</div>'


def next_session(variant: Variant) -> Day | None:
    days = {d.id: d for d in variant.days}
    today = today_index()
    for step in range(1, 8):
        slot = variant.schedule[(today + step) % 7]
        if slot != "rest" and days[slot].kind == "gym":
            return days[slot]
    return None


# --------------------------------------------------------- review markers

def review_markers(ids) -> None:
    lib = get_library()
    for rid in ids:
        item = lib.review_items.get(rid)
        if item:
            st.markdown(f'<div class="rg-review">{REVIEW_MARK} <strong>{esc(item.title)}</strong></div>',
                        unsafe_allow_html=True)


# ----------------------------------------------------------- exercise card

def dose(item: Item) -> str:
    lo, hi = item.range
    unit = tr(f"unit_{item.unit}")
    span = f"{lo}" if lo == hi else f"{lo}–{hi}"
    sep = "" if item.unit == "seconds" else " "
    return f"{item.sets} × {span}{sep}{unit}"


def exercise_card(item: Item, ex: Exercise, key: str) -> None:
    lib = get_library()
    marks = set(item.review) | set(ex.review_ids)
    extra = f", {tr('optional')}" if item.optional else ""
    label = f"{t(ex.name, lang())}  ({dose(item)}{extra})"
    if marks:
        label += f"  {REVIEW_MARK}"

    with st.expander(label):
        st.markdown(f'<div class="rg-dose">{esc(dose(item))}</div>', unsafe_allow_html=True)
        rest_key = ex.type
        lo, hi = rules.REST_MIN[rest_key]
        st.caption(f"{tr('rest', lo=lo, hi=hi)}. {tr('effort')}")

        if item.note:
            st.markdown(f'<div class="rg-note">{esc(t(item.note, lang()))}</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        col1.markdown(f"**{tr('muscles')}**  \n" + ", ".join(m.replace("_", " ") for m in ex.muscles))
        col2.markdown(f"**{tr('equipment')}**  \n" + ", ".join(ex.equipment))

        if ex.video_url:
            st.video(ex.video_url)
        else:
            st.markdown(f'<div class="rg-video">▶ {tr("video_placeholder")}</div>', unsafe_allow_html=True)

        if ex.form_cues:
            st.markdown(f"**{tr('form_cues')}**")
            for cue in ex.form_cues:
                st.markdown(f"- {t(cue, lang())}")

        if item.unit == "reps" and "bodyweight" not in ex.equipment:
            st.markdown(f"**{tr('warmup_calc')}**")
            w = st.number_input(tr("working_weight"), min_value=0.0, max_value=500.0, value=0.0,
                                step=2.5, key=f"ww_{key}")
            if w > 0:
                sets = warmup_sets(w, ex.type, min_weight=20 if "barbell" in ex.equipment else 0)
                if sets:
                    parts = [f"{s.weight:g} kg × {s.reps}" + (f" {tr('warmup_optional_note')}" if s.optional else "")
                             for s in sets]
                    st.markdown("  →  ".join(parts) + f"  →  **{w:g} kg**")
                else:
                    st.caption(tr("warmup_none"))

        if ex.alternatives:
            names = [t(lib.exercise(a).name, lang()) for a in ex.alternatives]
            st.caption(f"{tr('alternatives')}: " + ", ".join(names))

        review_markers(sorted(marks))
