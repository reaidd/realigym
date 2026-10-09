"""User preferences in session state, mirrored to the URL.

Until accounts exist, the URL is the 'save': refreshing or bookmarking the page keeps
the language, theme and chosen programme. Supabase replaces this later.
"""
import streamlit as st

from core.models import get_library

DEFAULTS = {"lang": "en", "theme": "light", "program": None, "variant": None}
ALLOWED = {"lang": {"en", "zh"}, "theme": {"light", "dark"}}


def _valid(key, value) -> bool:
    if value is None:
        return True
    if key in ALLOWED:
        return value in ALLOWED[key]
    lib = get_library()
    if key == "program":
        return value in lib.programs
    if key == "variant":
        prog = lib.programs.get(st.session_state.get("program"))
        return bool(prog) and value in {v.id for v in prog.variants}
    return True


def init() -> None:
    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            value = st.query_params.get(key, default)
            st.session_state[key] = value if _valid(key, value) else default
    sync_url()


def set_pref(key: str, value) -> None:
    st.session_state[key] = value
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
