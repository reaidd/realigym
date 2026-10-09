"""RealiGym — run with:  streamlit run app.py"""
import streamlit as st

from ui import state, theme

st.set_page_config(page_title="RealiGym", page_icon="🏋️", layout="centered")
state.init()
theme.apply()

pages = [
    st.Page("views/home.py", title="Home", default=True),
    st.Page("views/onboarding.py", title="Find your programme"),
    st.Page("views/program.py", title="Programme"),
    st.Page("views/review.py", title="To review"),
]
st.navigation(pages, position="hidden").run()
