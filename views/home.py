import streamlit as st

from core.models import get_library, t
from ui import state
from ui.components import esc, lang, next_session, today_index, toolbar, week_strip
from ui.strings import tr

lib = get_library()
toolbar()

st.markdown('<p class="rg-wordmark">RealiGym</p>'
            f'<p class="rg-tagline">{esc(tr("tagline"))}</p>', unsafe_allow_html=True)

prog, variant = state.chosen()

# ---- your programme / find one
if prog:
    slot = variant.schedule[today_index()]
    today = variant.day(slot) if slot != "rest" else None
    with st.container(border=True):
        st.caption(f"{tr('your_programme')}: {t(prog.name, lang())}, {t(variant.name, lang())}")
        st.markdown(week_strip(variant), unsafe_allow_html=True)
        st.caption(tr("today"))
        if today:
            st.markdown(f'<p class="rg-today">{esc(t(today.name, lang()))}</p>', unsafe_allow_html=True)
        else:
            nxt = next_session(variant)
            st.markdown(f'<p class="rg-today">{esc(tr("rest_day"))}</p>', unsafe_allow_html=True)
            st.write(tr("rest_day_body", next=t(nxt.name, lang()) if nxt else "–"))
        c1, c2 = st.columns(2)
        if c1.button(tr("open_today") if today else tr("open_programme"), type="primary",
                     use_container_width=True, key="open_today"):
            st.session_state["day"] = today.id if today else None
            st.session_state["view_program"] = prog.id
            st.switch_page("views/program.py")
        if c2.button(tr("change_programme"), use_container_width=True, key="change"):
            st.switch_page("views/onboarding.py")
else:
    with st.container(border=True):
        st.markdown(f"### {tr('find_title')}")
        st.write(tr("find_body"))
        if st.button(tr("find_button"), type="primary", key="find"):
            st.switch_page("views/onboarding.py")

# ---- catalogue
st.markdown(f"## {tr('all_programmes')}")
for p in lib.programs.values():
    v0 = p.variants[0]
    with st.container(border=True):
        st.markdown(f"### {t(p.name, lang())}")
        levels = ", ".join(tr(f"level_{l}") for l in p.levels)
        st.caption(f"{tr('days_a_week', n=p.days_per_week)}, {levels}")
        if p.image:
            st.image(p.image, use_container_width=True)
        else:
            st.markdown(week_strip(v0, highlight_today=False), unsafe_allow_html=True)
        st.write(t(p.summary, lang()))
        if p.pros or p.cons:
            c1, c2 = st.columns(2)
            c1.markdown(f"**{tr('pros')}**\n" + "\n".join(f"- {t(x, lang())}" for x in p.pros))
            c2.markdown(f"**{tr('cons')}**\n" + "\n".join(f"- {t(x, lang())}" for x in p.cons))
        if st.button(tr("view_programme"), key=f"view_{p.id}"):
            st.session_state["view_program"] = p.id
            st.session_state["day"] = None
            st.switch_page("views/program.py")
