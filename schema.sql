-- RealiGym — Supabase (Postgres) schema for accounts and workout logging.
-- Paste the whole file into Supabase → SQL Editor → New snippet → Run.
-- Safe to re-run: it drops and recreates the tables (this deletes any logged data).
--
-- How access works:
--   * People sign in with Google through Streamlit (st.login), not Supabase Auth.
--   * Only the app's server talks to the database, using the secret key from Streamlit secrets.
--   * Every query in core/store.py is filtered by the signed-in user's id.
--   * Row level security is ON with no policies, so the public (publishable/anon) key
--     can read and write nothing at all.

drop table if exists top_sets cascade;
drop table if exists sessions cascade;
drop table if exists profiles cascade;

create table profiles (
  user_id       text primary key,      -- Google account id ("sub")
  email         text not null,
  display_name  text,
  language      text check (language in ('en', 'zh')),
  theme         text check (theme in ('light', 'dark')),
  program_id    text,                  -- e.g. 'program_a'
  variant_id    text,                  -- e.g. 'standard' | 'limited'
  days_per_week int,                   -- onboarding answers
  experience    text check (experience in ('beginner', 'intermediate', 'advanced')),
  equipment     text check (equipment in ('commercial', 'limited')),
  minutes_per_session int,
  created_at    timestamptz not null default now()
);

create table sessions (
  id          uuid primary key default gen_random_uuid(),
  user_id     text not null references profiles (user_id) on delete cascade,
  program_id  text not null,
  variant_id  text not null,
  day_id      text not null,           -- e.g. 'A', 'UB', 'CORE'
  started_at  timestamptz not null default now(),
  finished_at timestamptz
);

-- One row per exercise per session: the top set, as the guide says to track.
create table top_sets (
  id           uuid primary key default gen_random_uuid(),
  session_id   uuid not null references sessions (id) on delete cascade,
  user_id      text not null references profiles (user_id) on delete cascade,
  exercise_id  text not null,          -- id from exercises.yaml (never rename ids!)
  weight_kg    numeric(6, 2),          -- null for bodyweight
  value        int not null,           -- reps, seconds or steps
  unit         text not null default 'reps' check (unit in ('reps', 'seconds', 'steps')),
  rir          int check (rir between 0 and 10),
  logged_at    timestamptz not null default now(),
  unique (session_id, exercise_id)     -- saving again in the same session overwrites
);

create index sessions_user on sessions (user_id, started_at desc);
create index top_sets_user_exercise on top_sets (user_id, exercise_id, logged_at desc);

alter table profiles enable row level security;
alter table sessions enable row level security;
alter table top_sets enable row level security;
-- No policies on purpose: only the server's secret key (which bypasses RLS) can access data.
