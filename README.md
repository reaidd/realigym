# RealiGym — *The realistic way to train*

## Run it
```
pip install -r requirements.txt
streamlit run app.py
python -m pytest -q        # 37 tests: data, logic, storage, every screen, logging flow
```

Screens: home, find-your-programme, programme pages with session logging and rest timer,
progress, and 🔍 To review. Signed in, preferences and logs are saved to your account;
signed out, preferences are kept in the page URL.

## Setting up sign-in and the database
All values go in **secrets**, never in the code. Template: `.streamlit/secrets.toml.example`.
- Local: copy it to `.streamlit/secrets.toml` (git-ignored).
- Online: Streamlit Community Cloud → app → Settings → Secrets → paste the same contents,
  with `redirect_uri` set to `https://YOUR-APP.streamlit.app/oauth2callback`.

Without `[auth]`, the app runs signed-out only. With `[auth]` but no `[supabase]`, logging works
but is kept in memory and lost on restart.

**First-run checklist**
1. Log in with Google → your first name appears top right.
2. Open a programme day → Start session → log a top set → it shows "Saved".
3. In Supabase → Table Editor, `top_sets` has a row.
4. Finish session, start another → the card shows "Last time" and a suggestion.
5. Progress page lists the exercise.

```
app.py             entry point (page routing)
views/             home, onboarding, program, review screens
ui/                toolbar, week strip, exercise card, rest timer, sign-in, theme, EN/ZH strings
data/
  exercises.yaml   every exercise once (EN/ZH names, type, equipment, muscles, alternatives, video slot)
  programs.yaml    Program A (standard + limited-equipment variant) and Program B
  review.yaml      🔍 things to check later
  warmup.yaml      cardio + dynamic stretch lists
core/
  models.py        loads + validates the YAML; t() picks EN/ZH with English fallback
  rules.py         numbers from the Main Guide (rest times, warmup %, protein…)
  training.py      pyramid warmup calculator + progressive overload suggestions
  duration.py      rough session length estimate
  recommend.py     onboarding answers → recommended programme + reasons/warnings
  i18n.py          EN/ZH text for those reasons/warnings
  store.py         logging storage, always scoped to one user (Supabase or in-memory)
db/schema.sql      Supabase tables (run once in the SQL editor)
tests/             python -m pytest -q
```

## Editing content
Your friend only needs to touch `data/*.yaml`. After any edit, run `python -m pytest -q` —
it catches typos like a misspelt exercise id or a schedule that doesn't add up.
Never rename an exercise `id` once people have logged sets against it.

## 🔍 Review markers
Add `review: [some-id]` to any exercise or programme item and the app will show 🔍 next to it.
Each id is explained in `data/review.yaml`. Exercises with no `form_cues` get the
`form-guide` marker automatically until the Form Guide is written.
