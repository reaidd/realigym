-- RealiGym — Supabase (Postgres) schema for accounts and workout logging.
-- Not connected yet; paste into the Supabase SQL editor when we wire up logging.
-- Programme/exercise content stays in data/*.yaml; logs refer to it by id.

create table profiles (
  id            uuid primary key references auth.users on delete cascade,
  display_name  text,
  language      text not null default 'en' check (language in ('en', 'zh')),
  theme         text not null default 'light' check (theme in ('light', 'dark')),
  program_id    text,                 -- e.g. 'program_a'
  variant_id    text,                 -- e.g. 'standard' | 'limited'
  -- onboarding answers, kept so the recommendation can be re-run
  days_per_week int,
  experience    text check (experience in ('beginner', 'intermediate', 'advanced')),
  equipment     text check (equipment in ('commercial', 'limited')),
  minutes_per_session int,
  created_at    timestamptz not null default now()
);

create table sessions (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users on delete cascade,
  program_id  text not null,
  variant_id  text not null,
  day_id      text not null,          -- e.g. 'A', 'UB', 'CORE'
  started_at  timestamptz not null default now(),
  finished_at timestamptz
);

-- One row per exercise per session: the top set, as the guide says to track.
create table top_sets (
  id           uuid primary key default gen_random_uuid(),
  session_id   uuid not null references sessions on delete cascade,
  user_id      uuid not null references auth.users on delete cascade,
  exercise_id  text not null,         -- id from exercises.yaml (never rename ids!)
  weight_kg    numeric(6, 2),         -- null for bodyweight
  value        int not null,          -- reps, seconds or steps
  unit         text not null default 'reps' check (unit in ('reps', 'seconds', 'steps')),
  rir          int check (rir between 0 and 10),
  logged_at    timestamptz not null default now()
);

create index top_sets_user_exercise on top_sets (user_id, exercise_id, logged_at desc);

-- Each friend can only see and edit their own data.
alter table profiles enable row level security;
alter table sessions enable row level security;
alter table top_sets enable row level security;

create policy "own profile"  on profiles for all using (id = auth.uid())      with check (id = auth.uid());
create policy "own sessions" on sessions for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own sets"     on top_sets for all using (user_id = auth.uid()) with check (user_id = auth.uid());
