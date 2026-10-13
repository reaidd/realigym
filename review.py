import streamlit as st

from core.models import REVIEW_MARK, get_library, open_review_items
from ui.components import toolbar
from ui.strings import tr

lib = get_library()
toolbar()
st.markdown(f"## {REVIEW_MARK} {tr('review_title')}")
st.write(tr("review_intro"))

refs = open_review_items(lib)
for rid, item in lib.review_items.items():
    with st.container(border=True):
        st.markdown(f"#### {REVIEW_MARK} {item.title}")
        st.write(item.note)
        places = refs.get(rid, [])
        if places:
            with st.expander(tr("review_places", n=len(places))):
                st.code("\n".join(places), language=None)
