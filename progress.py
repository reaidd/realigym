from datetime import datetime

import pandas as pd
import streamlit as st

from core.models import get_library, t
from ui import auth
from ui.components import TIMEZONE, fmt_set, lang, toolbar
from ui.strings import tr

lib = get_library()
toolbar()
st.markdown(f"## {tr('progress_title')}")

store = auth.store()
if store is None:
    st.info(tr("progress_login"))
    st.stop()


def local(ts) -> datetime:
    return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(TIMEZONE)


logged = [e for e in store.logged_exercises() if e in lib.exercises]
if not logged:
    st.info(tr("progress_empty"))
    st.stop()

ex_id = st.selectbox(tr("progress_pick"), logged, key="progress_ex",
                     format_func=lambda e: t(lib.exercise(e).name, lang()))
rows = store.history(ex_id)

weighted = [r for r in rows if r.get("weight_kg") not in (None, 0)]
if len(weighted) >= 2:
    chart = pd.DataFrame({
        tr("progress_table_date"): [local(r["logged_at"]) for r in weighted],
        tr("progress_chart"): [float(r["weight_kg"]) for r in weighted],
    }).set_index(tr("progress_table_date"))
    st.line_chart(chart, height=240)

table = pd.DataFrame({
    tr("progress_table_date"): [local(r["logged_at"]).strftime("%Y-%m-%d") for r in reversed(rows)],
    tr("progress_table_set"): [fmt_set(r) for r in reversed(rows)],
})
st.dataframe(table, hide_index=True, use_container_width=True)

st.markdown(f"### {tr('recent_sessions')}")
for s in store.recent_sessions(10):
    prog = lib.programs.get(s["program_id"])
    try:
        name = t(prog.variant(s["variant_id"]).day(s["day_id"]).name, lang())
    except Exception:
        name = s["day_id"]
    when = local(s["started_at"]).strftime("%a %d %b, %H:%M")
    status = "" if s.get("finished_at") else f" ({tr('in_progress')})"
    st.markdown(f"- {when}: {name}{status}")
