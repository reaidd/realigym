"""User preferences in session state.

Signed in: preferences live in the user's profile, so they follow them across devices.
Signed out: they're mirrored to the page URL, so refresh/bookmark still keeps them.
"""
import streamlit as st

from core.models import get_library
from ui import auth

DEFAULTS = {"lang": "en", "theme": "light", "program": None, "variant": None}
ALLOWED = {"lang": {"en", "zh"}, "theme": {"light", "dark"}}
PROFILE_COLUMN = {"lang": "language", "theme": "theme", "program": "program_id", "variant": "variant_id"}


def _valid(key, value, program=None) -> bool:
    if value is None:
        return True
    if key in ALLOWED:
        return value in ALLOWED[key]
    lib = get_library()
    if key == "program":
        return value in lib.programs
    if key == "variant":
        prog = lib.programs.get(program or st.session_state.get("program"))
        return bool(prog) and value in {v.id for v in prog.variants}
    return True


def init() -> None:
    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            value = st.query_params.get(key, default)
            st.session_state[key] = value if _valid(key, value) else default

    store = auth.store()
    if store and not st.session_state.get("_profile_loaded"):
        profile = store.profile() or {}
        for key, column in PROFILE_COLUMN.items():
            value = profile.get(column)
            if value is not None and _valid(key, value, profile.get("program_id")):
                st.session_state[key] = value
        st.session_state["_profile_loaded"] = True
    sync_url()


def set_pref(key: str, value) -> None:
    st.session_state[key] = value
    store = auth.store()
    if store:
        store.save_profile(**{PROFILE_COLUMN[key]: value})
    sync_url()


def sync_url() -> None:
    for key in DEFAULTS:
        value = st.session_state.get(key)
        if value is None:
            st.query_params.pop(key, None)
        elif st.query_params.get(key) != value:
            st.query_params[key] = value


def chosen():
    """(program, variant) the user has chosen, or (None, None)."""
    lib = get_library()
    prog = lib.programs.get(st.session_state.get("program"))
    if not prog:
        return None, None
    vid = st.session_state.get("variant")
    variant = next((v for v in prog.variants if v.id == vid), prog.variants[0])
    return prog, variant
