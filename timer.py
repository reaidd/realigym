"""Rest timer that counts down in the browser, so it keeps running between Streamlit reruns."""
import streamlit as st
import streamlit.components.v1 as components

from ui.theme import TOKENS


def rest_timer(label: str, presets=(1, 2, 3, 4, 5)) -> None:
    c = TOKENS[st.session_state.get("theme", "light")]
    buttons = "".join(f'<button onclick="start({m * 60})">{m} min</button>' for m in presets)
    components.html(f"""
<div class="t" role="timer" aria-live="polite">
  <span class="lbl">{label}</span>
  <span id="clock">0:00</span>
  <div class="btns">{buttons}<button class="stop" onclick="stop()">✕</button></div>
</div>
<style>
  body {{ margin:0; font-family:'Barlow',system-ui,sans-serif; }}
  .t {{ display:flex; align-items:center; gap:.8rem; flex-wrap:wrap; background:{c['surface']};
        border:1px solid {c['line']}; border-radius:8px; padding:.5rem .8rem; color:{c['ink']}; }}
  .lbl {{ font-size:.85rem; color:{c['muted']}; }}
  #clock {{ font-family:'Barlow Condensed',system-ui,sans-serif; font-weight:700; font-size:1.9rem;
           min-width:4.2rem; font-variant-numeric:tabular-nums; }}
  #clock.done {{ color:{c['blue']}; }}
  .btns {{ display:flex; gap:.35rem; flex-wrap:wrap; }}
  button {{ font:inherit; font-size:.9rem; padding:.35rem .6rem; border-radius:6px; cursor:pointer;
           border:1px solid {c['line']}; background:{c['bg']}; color:{c['ink']}; }}
  button:hover {{ border-color:{c['blue']}; }}
  button:focus-visible {{ outline:2px solid {c['blue']}; outline-offset:2px; }}
</style>
<script>
  let end = null, tick = null;
  const clock = document.getElementById('clock');
  const fmt = s => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
  function beep() {{
    try {{
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      [0, .35, .7].forEach(t => {{
        const o = ctx.createOscillator(); o.frequency.value = 880; o.connect(ctx.destination);
        o.start(ctx.currentTime + t); o.stop(ctx.currentTime + t + .2);
      }});
    }} catch (e) {{}}
    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
  }}
  function draw() {{
    const left = Math.max(0, Math.round((end - Date.now()) / 1000));
    clock.textContent = fmt(left);
    if (left === 0) {{ clearInterval(tick); tick = null; clock.classList.add('done'); beep(); }}
  }}
  function start(secs) {{ end = Date.now() + secs * 1000; clock.classList.remove('done');
                          if (tick) clearInterval(tick); tick = setInterval(draw, 250); draw(); }}
  function stop() {{ if (tick) clearInterval(tick); tick = null; clock.textContent = '0:00';
                     clock.classList.remove('done'); }}
</script>
""", height=78)
