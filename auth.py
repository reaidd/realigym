"""Who is signed in, whether they're allowed, and which store to use.

Secrets (see .streamlit/secrets.toml.example):
  [auth]      Google sign-in for st.login()
  [supabase]  url + secret_key — without it, logs are kept in memory (lost on restart)
  [access]    allowed_emails — optional friends list; empty = any Google account
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st

from core.store import MemoryStore, SupabaseStore

TEST_USER_ENV = "REALIGYM_TEST_USER"     # "id|email|name", only used when [auth] isn't configured


@dataclass(frozen=True)
class User:
    id: str
    email: str
    name: str

    @property
    def first_name(self) -> str:
        return (self.name or self.email).split()[0]


def _secrets_section(name: str) -> dict:
    try:
        return dict(st.secrets[name]) if name in st.secrets else {}
    except Exception:          # no secrets file at all
        return {}


def auth_configured() -> bool:
    return bool(_secrets_section("auth"))


def current_user() -> User | None:
    if not auth_configured():
        raw = os.environ.get(TEST_USER_ENV)
        if raw:
            uid, email, name = (raw.split("|") + ["", ""])[:3]
            return User(uid, email, name)
        return None
    if not st.user.is_logged_in:
        return None
    email = st.user.get("email") or ""
    return User(st.user.get("sub") or email, email, st.user.get("name") or email)


def is_allowed(user: User) -> bool:
    allowed = [e.strip().lower() for e in _secrets_section("access").get("allowed_emails", [])]
    return not allowed or user.email.lower() in allowed


def supabase_configured() -> bool:
    sb = _secrets_section("supabase")
    return bool(sb.get("url") and sb.get("secret_key"))


@st.cache_resource
def _supabase_client():
    from supabase import create_client
    sb = _secrets_section("supabase")
    return create_client(sb["url"], sb["secret_key"])


@st.cache_resource
def _memory_tables() -> dict:
    return {}


def store_for(user: User):
    if supabase_configured():
        return SupabaseStore(_supabase_client(), user.id)
    return MemoryStore(user.id, _memory_tables())


def setup() -> None:
    """Run once per page load: put the signed-in, allowed user and their store in session state."""
    user = current_user()
    st.session_state["auth_blocked"] = None
    if user and not is_allowed(user):
        st.session_state["auth_blocked"] = user.email
        user = None
    st.session_state["user"] = user
    st.session_state["store"] = store_for(user) if user else None
    if user and not st.session_state.get("_profile_checked") == user.id:
        store = st.session_state["store"]
        if store.profile() is None:
            store.save_profile(email=user.email, display_name=user.name)
        st.session_state["_profile_checked"] = user.id
        st.session_state["_profile_loaded"] = False


def user() -> User | None:
    return st.session_state.get("user")


def store():
    return st.session_state.get("store")
