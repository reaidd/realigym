import streamlit as st

from core.i18n import render
from core.models import get_library, t
from core.recommend import Answers, recommend
from ui import state
from ui.components import esc, lang, toolbar, week_strip
from ui.strings import tr

lib = get_library()
toolbar()
st.markdown(f"## {tr('ob_title')}")
st.write(tr("ob_intro"))

EXP = ["beginner", "intermediate", "advanced"]
EQUIP = ["commercial", "limited"]
TIMES = [45, 60, 90, 120, None]

with st.form("onboarding"):
    days = st.radio(tr("q_days"), [2, 3, 4, 5, 6], index=1, horizontal=True, key="ob_days")
    exp = st.radio(tr("q_exp"), EXP, format_func=lambda x: tr(f"exp_{x}"), key="ob_exp")
    equip = st.radio(tr("q_equip"), EQUIP, format_func=lambda x: tr(f"equip_{x}"), key="ob_equip")
    minutes = st.radio(tr("q_time"), TIMES, index=4, horizontal=True, key="ob_time",
                       format_func=lambda x: tr("time_none") if x is None else tr("minutes", n=x))
    health = st.radio(tr("q_health"), [False, True], horizontal=True, key="ob_health",
                      format_func=lambda x: tr("yes") if x else tr("no"))
    submitted = st.form_submit_button(tr("ob_submit"))

if submitted:
    st.session_state["rec"] = recommend(Answers(days, exp, equip, minutes, health), lib)

rec = st.session_state.get("rec")
if rec:
    prog = lib.programs[rec.program_id]
    variant = prog.variant(rec.variant_id)
    with st.container(border=True):
        st.caption(tr("ob_result"))
        st.markdown(f'<p class="rg-today">{esc(t(prog.name, lang()))}</p>', unsafe_allow_html=True)
        st.caption(t(variant.name, lang()))
        st.markdown(week_strip(variant, highlight_today=False), unsafe_allow_html=True)
        st.write(t(prog.summary, lang()))

        st.markdown(f"**{tr('why')}**")
        st.markdown("".join(f'<div class="rg-reason">{esc(render(r, lang()))}</div>' for r in rec.reasons),
                    unsafe_allow_html=True)
        if rec.warnings:
            st.markdown(f"**{tr('heads_up')}**")
            st.markdown("".join(f'<div class="rg-warn">{esc(render(w, lang()))}</div>' for w in rec.warnings),
                        unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        if c1.button(tr("start_programme"), type="primary", use_container_width=True, key="start"):
            state.set_pref("program", prog.id)
            state.set_pref("variant", variant.id)
            st.session_state["view_program"] = prog.id
            st.session_state["day"] = None
            st.switch_page("views/program.py")
        if c2.button(tr("browse_all"), use_container_width=True, key="browse"):
            st.switch_page("views/home.py")
