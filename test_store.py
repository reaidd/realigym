"""Storage: behaviour, and the guarantee that a user only ever touches their own rows."""
import pytest

from core.store import MemoryStore, SupabaseStore


# ------------------------------------------------------------ MemoryStore

@pytest.fixture
def db():
    return {}


def test_session_and_sets_roundtrip(db):
    me = MemoryStore("u1", db)
    me.save_profile(email="a@x.com", display_name="A")
    s1 = me.start_session("program_a", "standard", "A")
    me.log_set(s1["id"], "machine_chest_press", 35, 7, rir=1)
    me.log_set(s1["id"], "machine_chest_press", 35, 8, rir=0)          # overwrite in same session
    assert len(me.session_sets(s1["id"])) == 1
    assert me.session_sets(s1["id"])["machine_chest_press"]["value"] == 8
    me.finish_session(s1["id"])
    assert me.open_session() is None

    s2 = me.start_session("program_a", "standard", "A")
    last = me.last_sets(["machine_chest_press"], exclude_session=s2["id"])
    assert last["machine_chest_press"]["value"] == 8
    me.log_set(s2["id"], "machine_chest_press", 37.5, 5)
    assert [r["value"] for r in me.history("machine_chest_press")] == [8, 5]
    assert me.logged_exercises() == ["machine_chest_press"]


def test_discard_removes_sets(db):
    me = MemoryStore("u1", db)
    s = me.start_session("program_a", "standard", "A")
    me.log_set(s["id"], "plank", None, 60, unit="seconds")
    me.discard_session(s["id"])
    assert me.open_session() is None and me.logged_exercises() == []


def test_users_are_isolated(db):
    alice, bob = MemoryStore("alice", db), MemoryStore("bob", db)
    s = alice.start_session("program_a", "standard", "A")
    alice.log_set(s["id"], "barbell_squat", 80, 6)
    assert bob.open_session() is None
    assert bob.last_sets(["barbell_squat"]) == {}
    assert bob.history("barbell_squat") == []
    with pytest.raises(PermissionError):
        bob.log_set(s["id"], "barbell_squat", 200, 10)                  # can't write into alice's session
    bob.discard_session(s["id"])                                          # can't delete it either
    assert alice.open_session() is not None


def test_unknown_profile_field_rejected(db):
    with pytest.raises(ValueError):
        MemoryStore("u1", db).save_profile(user_id="someone_else")


def test_store_needs_user():
    with pytest.raises(ValueError):
        MemoryStore("", {})


# ----------------------------------------- SupabaseStore against a fake client

class FakeQuery:
    def __init__(self, log, table):
        self.call = {"table": table, "op": None, "filters": [], "payload": None}
        log.append(self.call)

    def _op(self, op, payload=None):
        self.call["op"], self.call["payload"] = op, payload
        return self

    def select(self, *_): return self._op("select")
    def insert(self, row): return self._op("insert", row)
    def upsert(self, row, **_): return self._op("upsert", row)
    def update(self, row): return self._op("update", row)
    def delete(self): return self._op("delete")

    def _f(self, kind, col, val=None):
        self.call["filters"].append((kind, col, val))
        return self

    def eq(self, c, v): return self._f("eq", c, v)
    def neq(self, c, v): return self._f("neq", c, v)
    def in_(self, c, v): return self._f("in", c, v)
    def is_(self, c, v): return self._f("is", c, v)
    def order(self, *a, **k): return self
    def limit(self, *_): return self

    def execute(self):
        class R: pass
        r = R()
        p = self.call["payload"]
        r.data = [dict(p, id="row1")] if isinstance(p, dict) else [
            {"id": "s1", "exercise_id": "plank", "logged_at": "2026-10-01T00:00:00+00:00",
             "session_id": "s1", "user_id": "me"}]
        return r


class FakeClient:
    def __init__(self):
        self.log = []

    def table(self, name):
        return FakeQuery(self.log, name)


def test_every_supabase_call_is_scoped_to_the_user():
    client = FakeClient()
    s = SupabaseStore(client, "me")
    s.profile(); s.save_profile(theme="dark"); s.open_session()
    s.start_session("program_a", "standard", "A"); s.finish_session("s1"); s.discard_session("s1")
    s.recent_sessions(); s.log_set("s1", "plank", None, 60, "seconds", 1)
    s.session_sets("s1"); s.last_sets(["plank"], "s2"); s.history("plank"); s.logged_exercises()

    assert len(client.log) > 10
    for call in client.log:
        if call["op"] in ("insert", "upsert"):
            assert call["payload"]["user_id"] == "me", call
        else:
            assert ("eq", "user_id", "me") in call["filters"], call
