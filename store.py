"""Workout logging storage, always scoped to ONE user.

The app creates a store for the signed-in user and never passes user ids around,
so a screen can't accidentally read someone else's data.

SupabaseStore  — real database (server-side, secret key)
MemoryStore    — same behaviour in memory, for tests and local use without Supabase
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

PROFILE_FIELDS = {
    "email", "display_name", "language", "theme", "program_id", "variant_id",
    "days_per_week", "experience", "equipment", "minutes_per_session",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _latest_per_exercise(rows: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in sorted(rows, key=lambda r: r["logged_at"], reverse=True):
        out.setdefault(r["exercise_id"], r)
    return out


class _Base:
    def __init__(self, user_id: str):
        if not user_id:
            raise ValueError("A store needs a user id")
        self.uid = user_id

    @staticmethod
    def _clean_profile(fields: dict) -> dict:
        unknown = set(fields) - PROFILE_FIELDS
        if unknown:
            raise ValueError(f"Unknown profile fields: {unknown}")
        return fields


# ======================================================================
class SupabaseStore(_Base):
    def __init__(self, client, user_id: str):
        super().__init__(user_id)
        self.db = client

    def _mine(self, table: str, columns: str = "*"):
        """SELECT … WHERE user_id = me. Every read starts here."""
        return self.db.table(table).select(columns).eq("user_id", self.uid)

    # ---- profile
    def profile(self) -> dict | None:
        rows = self._mine("profiles").limit(1).execute().data
        return rows[0] if rows else None

    def save_profile(self, **fields) -> None:
        row = {"user_id": self.uid, **self._clean_profile(fields)}
        self.db.table("profiles").upsert(row, on_conflict="user_id").execute()

    # ---- sessions
    def open_session(self) -> dict | None:
        rows = (self._mine("sessions").is_("finished_at", "null")
                .order("started_at", desc=True).limit(1).execute().data)
        return rows[0] if rows else None

    def start_session(self, program_id: str, variant_id: str, day_id: str) -> dict:
        row = {"user_id": self.uid, "program_id": program_id,
               "variant_id": variant_id, "day_id": day_id}
        return self.db.table("sessions").insert(row).execute().data[0]

    def finish_session(self, session_id: str) -> None:
        (self.db.table("sessions").update({"finished_at": now_iso()})
         .eq("id", session_id).eq("user_id", self.uid).execute())

    def discard_session(self, session_id: str) -> None:
        self.db.table("sessions").delete().eq("id", session_id).eq("user_id", self.uid).execute()

    def recent_sessions(self, limit: int = 10) -> list[dict]:
        return self._mine("sessions").order("started_at", desc=True).limit(limit).execute().data

    # ---- sets
    def _owns_session(self, session_id: str) -> bool:
        return bool(self._mine("sessions", "id").eq("id", session_id).limit(1).execute().data)

    def log_set(self, session_id: str, exercise_id: str, weight_kg: float | None,
                value: int, unit: str = "reps", rir: int | None = None) -> dict:
        if not self._owns_session(session_id):
            raise PermissionError("That session doesn't belong to this user")
        row = {"session_id": session_id, "user_id": self.uid, "exercise_id": exercise_id,
               "weight_kg": weight_kg, "value": int(value), "unit": unit, "rir": rir,
               "logged_at": now_iso()}
        return (self.db.table("top_sets").upsert(row, on_conflict="session_id,exercise_id")
                .execute().data[0])

    def session_sets(self, session_id: str) -> dict[str, dict]:
        rows = self._mine("top_sets").eq("session_id", session_id).execute().data
        return {r["exercise_id"]: r for r in rows}

    def last_sets(self, exercise_ids: list[str], exclude_session: str | None = None) -> dict[str, dict]:
        """Most recent top set per exercise, from sessions other than `exclude_session`."""
        if not exercise_ids:
            return {}
        q = self._mine("top_sets").in_("exercise_id", list(set(exercise_ids)))
        if exclude_session:
            q = q.neq("session_id", exclude_session)
        rows = q.order("logged_at", desc=True).limit(300).execute().data
        return _latest_per_exercise(rows)

    def history(self, exercise_id: str, limit: int = 100) -> list[dict]:
        rows = (self._mine("top_sets").eq("exercise_id", exercise_id)
                .order("logged_at", desc=True).limit(limit).execute().data)
        return list(reversed(rows))

    def logged_exercises(self) -> list[str]:
        rows = self._mine("top_sets", "exercise_id").execute().data
        return sorted({r["exercise_id"] for r in rows})


# ======================================================================
class MemoryStore(_Base):
    """In-memory twin of SupabaseStore. `tables` can be shared between users like a real DB."""

    def __init__(self, user_id: str, tables: dict | None = None):
        super().__init__(user_id)
        self.t = tables if tables is not None else {}
        for name in ("profiles", "sessions", "top_sets"):
            self.t.setdefault(name, [])

    def _mine(self, table):
        return [r for r in self.t[table] if r["user_id"] == self.uid]

    def profile(self):
        rows = self._mine("profiles")
        return dict(rows[0]) if rows else None

    def save_profile(self, **fields):
        fields = self._clean_profile(fields)
        rows = self._mine("profiles")
        if rows:
            rows[0].update(fields)
        else:
            self.t["profiles"].append({"user_id": self.uid, "created_at": now_iso(), **fields})

    def open_session(self):
        rows = [r for r in self._mine("sessions") if r["finished_at"] is None]
        return dict(max(rows, key=lambda r: r["started_at"])) if rows else None

    def start_session(self, program_id, variant_id, day_id):
        row = {"id": str(uuid.uuid4()), "user_id": self.uid, "program_id": program_id,
               "variant_id": variant_id, "day_id": day_id, "started_at": now_iso(),
               "finished_at": None}
        self.t["sessions"].append(row)
        return dict(row)

    def finish_session(self, session_id):
        for r in self._mine("sessions"):
            if r["id"] == session_id:
                r["finished_at"] = now_iso()

    def discard_session(self, session_id):
        self.t["sessions"] = [r for r in self.t["sessions"]
                              if not (r["id"] == session_id and r["user_id"] == self.uid)]
        self.t["top_sets"] = [r for r in self.t["top_sets"]
                              if not (r["session_id"] == session_id and r["user_id"] == self.uid)]

    def recent_sessions(self, limit=10):
        return [dict(r) for r in sorted(self._mine("sessions"), key=lambda r: r["started_at"],
                                        reverse=True)[:limit]]

    def log_set(self, session_id, exercise_id, weight_kg, value, unit="reps", rir=None):
        if not any(r["id"] == session_id for r in self._mine("sessions")):
            raise PermissionError("That session doesn't belong to this user")
        row = {"id": str(uuid.uuid4()), "session_id": session_id, "user_id": self.uid,
               "exercise_id": exercise_id, "weight_kg": weight_kg, "value": int(value),
               "unit": unit, "rir": rir, "logged_at": now_iso()}
        self.t["top_sets"] = [r for r in self.t["top_sets"]
                              if not (r["session_id"] == session_id and r["exercise_id"] == exercise_id)]
        self.t["top_sets"].append(row)
        return dict(row)

    def session_sets(self, session_id):
        return {r["exercise_id"]: dict(r) for r in self._mine("top_sets") if r["session_id"] == session_id}

    def last_sets(self, exercise_ids, exclude_session=None):
        ids = set(exercise_ids)
        rows = [r for r in self._mine("top_sets")
                if r["exercise_id"] in ids and r["session_id"] != exclude_session]
        return {k: dict(v) for k, v in _latest_per_exercise(rows).items()}

    def history(self, exercise_id, limit=100):
        rows = sorted((r for r in self._mine("top_sets") if r["exercise_id"] == exercise_id),
                      key=lambda r: r["logged_at"])
        return [dict(r) for r in rows[-limit:]]

    def logged_exercises(self):
        return sorted({r["exercise_id"] for r in self._mine("top_sets")})
