"""Reusable interface pieces."""
from __future__ import annotations

import html
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from core import rules
from core.models import REVIEW_MARK, Day, Exercise, Item, Variant, get_library, t
from core.training import TopSet, suggest_next, warmup_sets
from ui import auth, state
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
    home, prog, rev, lng, thm, acct = st.columns([1.3, 1.5, 1.8, 1.1, 1.1, 1.4],
                                                vertical_alignment="center")
    if home.button(tr("nav_home"), key="tb_home", type="tertiary"):
        st.switch_page("views/home.py")
    if prog.button(tr("nav_progress"), key="tb_progress", type="tertiary"):
        st.switch_page("views/progress.py")
    if rev.button(tr("nav_review"), key="tb_review", type="tertiary"):
        st.switch_page("views/review.py")
    if lng.button(tr("lang_switch"), key="tb_lang", use_container_width=True):
        state.set_pref("lang", "zh" if lang() == "en" else "en")
        st.rerun()
    dark = st.session_state.get("theme") == "dark"
    if thm.button(tr("theme_light") if dark else tr("theme_dark"), key="tb_theme",
                  use_container_width=True):
        state.set_pref("theme", "light" if dark else "dark")
        st.rerun()
    with acct:
        account_button()

    blocked = st.session_state.get("auth_blocked")
    if blocked:
        st.warning(tr("not_allowed", email=blocked))


def account_button() -> None:
    user = auth.user()
    if user:
        with st.popover(user.first_name, use_container_width=True):
            st.caption(tr("signed_in_as", email=user.email))
            if not auth.supabase_configured():
                st.caption(tr("memory_mode"))
            if auth.auth_configured() and st.button(tr("logout"), key="tb_logout"):
                st.logout()
    elif st.session_state.get("auth_blocked"):
        if st.button(tr("logout"), key="tb_logout_blocked", use_container_width=True):
            st.logout()
    elif auth.auth_configured():
        if st.button(tr("login_google"), key="tb_login", type="primary", use_container_width=True):
            st.login()
    else:
        st.button(tr("login"), key="tb_login", disabled=True, help=tr("login_unconfigured"),
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


def exercise_card(item: Item, ex: Exercise, key: str, log: dict | None = None) -> None:
    """log = {'session': row|None, 'last': row|None, 'current': row|None} when signed in."""
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

        suggestion = None
        if log is not None:
            suggestion = log_panel(item, ex, key, log)

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
            start_w = float(suggestion.weight) if suggestion and suggestion.weight else 0.0
            w = st.number_input(tr("working_weight"), min_value=0.0, max_value=500.0, value=start_w,
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


# ----------------------------------------------------------------- logging

def has_weight(ex: Exercise) -> bool:
    return ex.equipment != ("bodyweight",)


def fmt_set(row: dict) -> str:
    unit = tr(f"unit_{row['unit']}")
    sep = "" if row["unit"] == "seconds" else " "
    value = f"{row['value']}{sep}{unit}"
    text = f"{float(row['weight_kg']):g} kg × {value}" if row.get("weight_kg") not in (None, 0) else value
    if row.get("rir") is not None:
        text += f" (RIR {row['rir']})"
    return text


def log_panel(item: Item, ex: Exercise, key: str, log: dict):
    """Last time + suggestion, and (during a session) the form to log the top set."""
    last, current, session = log.get("last"), log.get("current"), log.get("session")
    suggestion = None
    if item.unit == "reps" and has_weight(ex):
        top = TopSet(float(last["weight_kg"] or 0), int(last["value"])) if last and last.get("weight_kg") else None
        suggestion = suggest_next(top, item.range)

    if last:
        st.markdown(f"**{tr('last_time', set=fmt_set(last))}**")
        if suggestion and suggestion.weight:
            msg = {"increase": "next_increase", "hold": "next_hold", "below_range": "next_below"}[suggestion.action]
            st.markdown(f'<div class="rg-note">{esc(tr(msg, weight=suggestion.weight, reps=suggestion.target_reps))}</div>',
                        unsafe_allow_html=True)
    elif item.unit == "reps" and has_weight(ex):
        st.caption(tr("first_time"))

    if not session:
        return suggestion

    if current:
        st.success(tr("saved_set", set=fmt_set(current)))

    lo, hi = item.range
    if current:
        d_weight, d_value, d_rir = float(current["weight_kg"] or 0), int(current["value"]), current["rir"]
    elif suggestion and suggestion.weight:
        d_weight, d_value, d_rir = float(suggestion.weight), suggestion.target_reps, rules.TARGET_RIR
    elif last:
        d_weight, d_value, d_rir = float(last["weight_kg"] or 0), int(last["value"]), last["rir"]
    else:
        d_weight, d_value, d_rir = 0.0, hi if item.unit != "reps" else lo, rules.TARGET_RIR

    with st.form(f"log_{key}", border=True):
        st.markdown(f"**{tr('log_title')}**")
        cols = st.columns(3 if has_weight(ex) else 2)
        i = 0
        weight = None
        if has_weight(ex):
            weight = cols[0].number_input(tr("weight_kg"), 0.0, 500.0, d_weight, 2.5, key=f"lw_{key}")
            i = 1
        value = cols[i].number_input(tr(f"value_{item.unit}"), 0, 1000, d_value, 1, key=f"lv_{key}")
        rir_options = [0, 1, 2, 3, 4, 5]
        rir = cols[i + 1].selectbox(tr("rir"), rir_options,
                                    index=rir_options.index(d_rir) if d_rir in rir_options else 1,
                                    help=tr("rir_help"), key=f"lr_{key}")
        if st.form_submit_button(tr("save_set"), use_container_width=True):
            if value > 0:
                auth.store().log_set(session["id"], ex.id, weight or None, int(value), item.unit, int(rir))
                st.rerun()
    return suggestion
