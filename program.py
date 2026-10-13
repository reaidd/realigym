from datetime import datetime

import streamlit as st
import yaml

from core import rules
from core.duration import estimate_minutes
from core.models import DATA_DIR, get_library, t
from ui import auth, state
from ui.components import TIMEZONE, esc, exercise_card, lang, review_markers, today_index, toolbar, week_strip
from ui.timer import rest_timer
from ui.strings import tr

lib = get_library()

# Navigation requests from other screens/buttons: (program, variant or None, day or None).
# Applied before any widget exists, so widget state can be reset safely.
goto = st.session_state.pop("_goto", None)
if goto:
    pid, vid_req, did_req = goto
    st.session_state["view_program"] = pid
    if vid_req:
        st.session_state[f"variant_{pid}"] = vid_req
    st.session_state["day"] = did_req
    for k in [k for k in st.session_state if str(k).startswith(f"day_{pid}_")]:
        del st.session_state[k]

toolbar()

chosen_prog, chosen_variant = state.chosen()
prog = lib.programs.get(st.session_state.get("view_program")) or chosen_prog
if not prog:
    st.info(tr("no_programme"))
    st.stop()


@st.cache_data
def warmup_content():
    return yaml.safe_load((DATA_DIR / "warmup.yaml").read_text(encoding="utf-8"))


# ---------------- sidebar: setup + day
with st.sidebar:
    st.markdown(f"### {t(prog.name, lang())}")
    variant_ids = [v.id for v in prog.variants]
    default_v = chosen_variant.id if (chosen_prog and chosen_prog.id == prog.id) else variant_ids[0]
    if len(variant_ids) > 1:
        vid = st.radio(tr("setup"), variant_ids, index=variant_ids.index(default_v),
                       format_func=lambda x: t(prog.variant(x).name, lang()), key=f"variant_{prog.id}")
        if chosen_prog and chosen_prog.id == prog.id and vid != chosen_variant.id:
            state.set_pref("variant", vid)
    else:
        vid = variant_ids[0]
    variant = prog.variant(vid)

    day_ids = [d.id for d in variant.days]
    wanted = st.session_state.get("day")
    if wanted not in day_ids:
        slot = variant.schedule[today_index()]
        wanted = slot if slot in day_ids and variant.day(slot).kind == "gym" else day_ids[0]

    def day_label(did):
        return t(variant.day(did).name, lang())

    day_id = st.radio(tr("day"), day_ids, index=day_ids.index(wanted), format_func=day_label,
                      key=f"day_{prog.id}_{vid}")
    st.session_state["day"] = day_id

day = variant.day(day_id)

# ---------------- header
st.caption(f"{t(prog.name, lang())}, {t(variant.name, lang())}")
if variant.note:
    st.caption(t(variant.note, lang()))
st.markdown(week_strip(variant), unsafe_allow_html=True)
st.markdown(f"## {t(day.name, lang())}")
if day.note:
    st.markdown(f'<div class="rg-note">{esc(t(day.note, lang()))}</div>', unsafe_allow_html=True)

if day.kind == "gym":
    full = estimate_minutes(day, lib)
    short = estimate_minutes(day, lib, isolation_sets=rules.SHORT_ON_TIME_ISOLATION_SETS)
    st.markdown(f"**{tr('about_min', n=full)}**")
    st.caption(tr("short_on_time", n=short))
    review_markers(["session-length"])

    # ---------------- warmup
    w = warmup_content()
    with st.expander(tr("warmup_title")):
        st.markdown(f"**{tr('warmup_general')}**")
        st.write(t(w["general"], lang()))
        st.markdown(f"**{tr('warmup_dynamic', reps=w['dynamic']['reps'])}**")
        c1, c2 = st.columns(2)
        c1.markdown(f"*{tr('upper_body')}*\n" + "\n".join(f"- {t(x, lang())}" for x in w["dynamic"]["upper"]))
        c2.markdown(f"*{tr('lower_body')}*\n" + "\n".join(f"- {t(x, lang())}" for x in w["dynamic"]["lower"]))
        st.markdown(f"**{tr('warmup_pyramid')}**")

# ---------------- session (signed in only)
store = auth.store()
active = None
log_data = None
if store is None:
    st.caption(tr("log_in_to_track"))
else:
    if st.session_state.pop("_just_finished", False):
        st.success(tr("session_finished"))
    open_s = store.open_session()
    here = (prog.id, variant.id, day.id)
    if open_s and (open_s["program_id"], open_s["variant_id"], open_s["day_id"]) == here:
        active = open_s
    elif open_s:
        other_prog = lib.programs.get(open_s["program_id"])
        try:
            other_day = t(other_prog.variant(open_s["variant_id"]).day(open_s["day_id"]).name, lang())
        except Exception:
            other_day = open_s["day_id"]
        st.info(tr("other_session", day=other_day))
        c1, c2 = st.columns(2)
        if c1.button(tr("go_to_session"), key="goto_session", use_container_width=True):
            st.session_state["_goto"] = (open_s["program_id"], open_s["variant_id"], open_s["day_id"])
            st.rerun()
        if c2.button(tr("finish_session"), key="finish_other", use_container_width=True):
            store.finish_session(open_s["id"])
            st.rerun()
    elif st.button(tr("start_session"), type="primary", key="start_session"):
        store.start_session(*here)
        st.rerun()

    ids = [i.exercise_id for i in day.items]
    current = store.session_sets(active["id"]) if active else {}
    last = store.last_sets(ids, exclude_session=active["id"] if active else None)
    log_data = {"session": active, "current": current, "last": last}

    if active:
        started = datetime.fromisoformat(str(active["started_at"]).replace("Z", "+00:00"))
        with st.container(border=True):
            st.markdown(f"**{tr('session_running', time=started.astimezone(TIMEZONE).strftime('%H:%M'))}**")
            st.caption(tr("logged_count", n=len(current), total=len(ids)))
            rest_timer(tr("timer"))
            c1, c2 = st.columns([2, 1])
            if c1.button(tr("finish_session"), type="primary", key="finish_session", use_container_width=True):
                store.finish_session(active["id"])
                st.session_state["_just_finished"] = True
                st.rerun()
            if c2.button(tr("discard_session"), key="discard_session", use_container_width=True):
                store.discard_session(active["id"])
                st.rerun()

# ---------------- exercises
for gi, group in enumerate(day.groups):
    st.markdown(f'<div class="rg-group">{esc(t(group.label, lang()))}</div>', unsafe_allow_html=True)
    if len(group.items) > 1 and day.kind == "gym":
        st.caption(tr(f"superset_{group.superset}"))
    for ii, item in enumerate(group.items):
        log = None
        if log_data is not None:
            log = {"session": log_data["session"], "last": log_data["last"].get(item.exercise_id),
                   "current": log_data["current"].get(item.exercise_id)}
        exercise_card(item, lib.exercise(item.exercise_id), key=f"{prog.id}_{vid}_{day.id}_{gi}_{ii}", log=log)
