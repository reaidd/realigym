"""RealiGym look: gym chalk and bumper plates.

Chalk-white floor, slate ink, plate blue for actions and today's session,
plate yellow for 🔍 review markers and warnings. Barlow Condensed reads like gym
signage and carries the numbers (3 × 5–8); Barlow for body; Noto Sans TC for Chinese.
"""
import streamlit as st

TOKENS = {
    "light": {
        "bg": "#F2F4F3", "surface": "#FFFFFF", "ink": "#1C2529", "muted": "#5B676C",
        "line": "#D3D9D7", "blue": "#2D5BA6", "blue_ink": "#FFFFFF", "blue_soft": "#E3EAF6",
        "yellow": "#E0AE22", "yellow_soft": "#FBF1D3",
    },
    "dark": {
        "bg": "#12181B", "surface": "#1B2327", "ink": "#E6EBE9", "muted": "#9AA5A9",
        "line": "#2C363B", "blue": "#7EA2E6", "blue_ink": "#0E1A2E", "blue_soft": "#1E2B40",
        "yellow": "#E8BF4A", "yellow_soft": "#33301F",
    },
}

FONTS = "https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap"


def apply() -> None:
    c = TOKENS[st.session_state.get("theme", "light")]
    css = f"""
<style>
@import url('{FONTS}');
:root {{
  --rg-bg:{c['bg']}; --rg-surface:{c['surface']}; --rg-ink:{c['ink']}; --rg-muted:{c['muted']};
  --rg-line:{c['line']}; --rg-blue:{c['blue']}; --rg-blue-ink:{c['blue_ink']};
  --rg-blue-soft:{c['blue_soft']}; --rg-yellow:{c['yellow']}; --rg-yellow-soft:{c['yellow_soft']};
  --rg-body:'Barlow','Noto Sans TC',system-ui,sans-serif;
  --rg-display:'Barlow Condensed','Noto Sans TC',system-ui,sans-serif;
}}
.stApp, [data-testid="stHeader"] {{ background:var(--rg-bg); }}
[data-testid="stSidebar"] {{ background:var(--rg-surface); border-right:1px solid var(--rg-line); }}
.stApp p, .stApp li, .stApp label, .stApp button, .stApp input {{ font-family:var(--rg-body); color:var(--rg-ink); }}
[data-testid="stMarkdownContainer"] {{ color:var(--rg-ink); }}
[data-testid="stIconMaterial"] {{ font-family:'Material Symbols Rounded' !important; }}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{ font-family:var(--rg-display); color:var(--rg-ink); letter-spacing:.01em; }}
.stApp h2 {{ font-size:2rem; }} .stApp h3 {{ font-size:1.5rem; }} .stApp h4 {{ font-size:1.15rem; }}
[data-testid="stCaptionContainer"], .stApp small {{ color:var(--rg-muted) !important; }}
.block-container {{ max-width:860px; padding-top:3.2rem; }}

/* buttons */
.stButton button, .stFormSubmitButton button {{
  border-radius:6px; border:1px solid var(--rg-line); background:var(--rg-surface);
  color:var(--rg-ink); font-weight:500;
}}
.stButton button[kind="tertiary"] {{ border:none; background:transparent; padding-left:0; }}
.stButton button:hover {{ border-color:var(--rg-blue); color:var(--rg-blue); }}
.stButton button[kind="primary"], .stFormSubmitButton button {{
  background:var(--rg-blue); border-color:var(--rg-blue); color:var(--rg-blue-ink);
}}
.stButton button[kind="primary"] p, .stFormSubmitButton button p {{ color:var(--rg-blue-ink); }}
.stButton button:focus-visible {{ outline:2px solid var(--rg-blue); outline-offset:2px; }}

/* expanders = exercise rows */
[data-testid="stExpander"] details {{ background:var(--rg-surface); border:1px solid var(--rg-line); border-radius:6px; }}
[data-testid="stExpander"] summary:hover p {{ color:var(--rg-blue); }}

/* inputs in dark mode */
[data-baseweb="input"], [data-baseweb="select"] > div, .stNumberInput input {{
  background:var(--rg-surface) !important; color:var(--rg-ink) !important; border-color:var(--rg-line) !important;
}}

/* --- RealiGym components --- */
.rg-review, .rg-warn, .rg-reason, .rg-note, .rg-video, .rg-slot .rg-wd {{ font-family:var(--rg-body); }}
.stApp p.rg-wordmark {{ font-family:var(--rg-display) !important; font-weight:700; font-size:clamp(3.2rem,10vw,6rem) !important;
  line-height:.9 !important; letter-spacing:-.01em; margin:.6rem 0 0 !important; }}
.stApp p.rg-tagline {{ color:var(--rg-muted) !important; font-size:1.15rem !important; margin:.5rem 0 1.8rem !important; }}
.rg-panel {{ background:var(--rg-surface); border:1px solid var(--rg-line); border-radius:10px; padding:1.2rem 1.3rem; margin-bottom:.8rem; }}
.stApp p.rg-today {{ font-family:var(--rg-display) !important; font-weight:700; font-size:2.6rem !important; line-height:1 !important; margin:.1rem 0 .6rem !important; }}
.rg-week {{ display:grid; grid-template-columns:repeat(7,1fr); gap:6px; margin:.7rem 0 .4rem; }}
.rg-slot {{ text-align:center; border-radius:6px; padding:.45rem .1rem; border:1px solid var(--rg-line); }}
.rg-slot .rg-wd {{ font-size:.75rem; color:var(--rg-muted); display:block; }}
.rg-slot .rg-id {{ font-family:var(--rg-display) !important; font-weight:700; font-size:1.3rem; display:block; }}
.rg-slot.gym {{ background:var(--rg-blue-soft); border-color:transparent; }}
.rg-slot.core {{ border-style:dashed; }}
.rg-slot.rest .rg-id {{ color:var(--rg-muted); font-weight:600; }}
.rg-slot.today {{ background:var(--rg-blue); border-color:var(--rg-blue); }}
.rg-slot.today span {{ color:var(--rg-blue-ink) !important; }}
.rg-dose {{ font-family:var(--rg-display) !important; font-weight:700; font-size:1.6rem; color:var(--rg-blue); line-height:1; }}
.rg-review {{ background:var(--rg-yellow-soft); border-left:3px solid var(--rg-yellow); border-radius:4px;
  padding:.45rem .7rem; margin:.4rem 0; font-size:.92rem; }}
.rg-warn {{ background:var(--rg-yellow-soft); border-radius:6px; padding:.6rem .8rem; margin:.35rem 0; }}
.rg-reason {{ padding:.3rem 0 .3rem 1.4rem; position:relative; }}
.rg-reason::before {{ content:'✓'; position:absolute; left:0; color:var(--rg-blue); font-weight:700; }}
.rg-note {{ border-left:3px solid var(--rg-blue); padding:.2rem .7rem; margin:.3rem 0 .6rem; color:var(--rg-ink); }}
.rg-video {{ border:1px dashed var(--rg-line); border-radius:6px; padding:1.6rem; text-align:center; color:var(--rg-muted); }}
.rg-group {{ font-family:var(--rg-display) !important; font-weight:600; font-size:1.05rem; color:var(--rg-muted); margin:1.2rem 0 .1rem; }}
.rg-chip {{ display:inline-block; font-size:.8rem; padding:.05rem .5rem; border-radius:99px; border:1px solid var(--rg-line); color:var(--rg-muted); margin-left:.3rem; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; animation:none !important; }} }}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)
