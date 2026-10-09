# RealiGym — *The realistic way to train*
I'm still testing, this was vibecoded, too barebones right now
## Run it
```
pip install -r requirements.txt
streamlit run app.py
python -m pytest -q        # 28 tests: data, logic, and every screen
```

Screens so far: home, find-your-programme (onboarding), programme pages, and a 🔍 To review page.
Language, theme and chosen programme are kept in the page URL, so refreshing or bookmarking
keeps them. Real accounts replace this when we add set logging.

```
app.py             entry point (page routing)
views/             home, onboarding, program, review screens
ui/                toolbar, week strip, exercise card, theme, EN/ZH strings
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
db/schema.sql      Supabase tables for accounts + set logging (not connected yet)
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
