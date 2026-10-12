# ANTDESIGNER WARM REDESIGN - BUNDLE FOR AI ARENA

You are a careful senior front-end engineer working on an existing, working Streamlit app: "AI-Based CPW Microstrip Antenna Synthesis" (repo `kara-nawzad/Antenna-AI-Project`, main file `10_web_app.py`; engine `engine_v2.py`; drawing `antenna_viz.py`; charts `antenna_charts.py`). This is a VISUAL REDESIGN ONLY. Engineering behaviour must stay identical.

You received: this file, `reference_preview.html` (the approved design: open it in a browser and compare your screenshots with it), and the logos in `assets/`. PART B below contains 4 files you must create verbatim (they were tested outside Streamlit, not inside it).

## 1. THE DESIGN (approved by the owner - do not reinterpret)
Warm, light, human, with purposeful motion. NOT dark, NOT glowy, NOT "AI-startup". Palette: paper #F5F2EA, card #FFFDF8, ink/navy #14213D, muted #5B6478, lines rgba(20,33,61,.14), AntDesigner purple #6366F1 / #4F46E5 for actions and data. No green/orange/cyan. Fonts: Fraunces (headings), Inter (UI), JetBrains Mono (numbers). Motion that must work: headline words rise one by one; drifting mountain ridgelines + antenna mast with signal arcs on Home; tab underline slides; sections fade up on scroll; metric numbers count up; cards lift on hover; antenna drawing and S11/VSWR curves draw themselves; hover crosshair on the chart. All motion respects prefers-reduced-motion.
Logos: AntDesigner (charcoal+purple version `assets/antdesigner_logo_light.png`) in the top bar and `assets/antdesigner_favicon.png` as page icon; SPU logo in its ORIGINAL colours (`assets/spu_logo_nav.png`) in the team block. Copy the `assets/` files into the repo's `assets/` folder.

## 2. ABSOLUTE RULES (violating any = stop and report)
1. You may edit ONLY: `10_web_app.py` (UI/markup/layout parts only), `antdesigner_theme.py`, `antenna_viz.py`, `antenna_charts.py`, `.streamlit/config.toml` (merge, don't overwrite other keys), and add files under `assets/`. EVERYTHING ELSE IS READ-ONLY: `engine_v2.py`, `fly.toml`, `Dockerfile`, `requirements.txt`, `README.md`, data and model files. (A previous attempt changed those and committed a nested .patch file - do not repeat that.)
2. Do not change logic in: `forward_*`, `run_inverse_solver`, `run_engine_self_test`, `run_engine_ab_test`, `run_inverse_self_test`, `run_startup_healthcheck`, `load_brains`, `load_data`, `_download_hf`, validation functions, `clamp_5_40` / the four `sync_*` callbacks, AETHER/Groq code.
3. Do not rename/remove any `st.session_state` key or widget `key=` (`lp_slider, lp_input, wp_slider, wp_input, lp_val, wp_val, fwd_res, inv_res, self_test_stats, inv_test_summary, inv_test_family, messages, ...`). Do not change widget ranges, defaults, steps or what a label means. Do not change the 12 shapes' geometry (`patch_polygons`, `draw_antenna`).
4. KEEP ALL TEXT. Do not delete or reword any sentence of the Project Introduction, System Overview, limitations paragraph, credits, footer or captions. The only text changes allowed are those in PART B (hero, how-it-works, team block, footer wording is identical to the original). The team block replaces only the old "Prepared by / Supervised by" box and must contain exactly: Arwin Hunar, Dunya Anwar, Kara Nawzad, Khazan Jafaar, Ramyar Aram, Ranw Jamil; supervised by Dr. Halgurd N. Awl.
5. NEVER fabricate data. Charts/drawings use only the engine's real arrays and values. No placeholder numbers in the UI.
6. Work on a NEW branch `design/antdesigner-warm` from current `main`. Do not push to main, do not merge other branches, do not deploy, do not touch Hugging Face, do not print/commit secrets (GROQ_API_KEY).
7. CHECK BEFORE EVERY EDIT (read the exact code you will change) and AFTER EVERY EDIT (run the check listed for that step). If anything differs from this file or is ambiguous, STOP and ask. Anything you could not verify must be labelled NOT VERIFIED - never assumed.

## 3. STEP 0 - RECON (read-only; then show me the report)
a) Installed Streamlit version; confirm `st.tabs`, `st.set_page_config(page_icon=...)` accepts a file path/PIL image, and that `st.markdown(unsafe_allow_html=True)` passes inline `<svg>`/`<style>`.
b) Locate in `10_web_app.py`: the old CSS block, old navbar, old hero, Project Introduction, System Overview, Forward section, Engine Validation, Inverse section, Inverse Validation, AETHER, footer, and the trailing `components.html` JS. Give line numbers. Find the variable names that hold the forward result (curve frequency array, S11 array, VSWR array, fr, bw, shape id, lp, wp) and the inverse result; the animated functions need them.
c) List every hard-coded colour (CSS, matplotlib, plotly) outside PART B files.
d) Note how the hidden health-check div (`.health-hidden`) is currently hidden - it must stay hidden (the theme CSS keeps that rule; a previous redesign dropped it and the word "pass" showed on screen).
STOP after the report if anything differs from this file.

## 4. STEP 1 - BASELINE (before touching anything)
Run the app. Record to `baseline.json`: Forward Lp=22.5, Wp=18.0, default shape, default refine setting -> resonance, bandwidth, S11 min, VSWR, gain, efficiency, engine-mode string, nearest-anchor line. Inverse: 3.5 GHz, Balanced Profile, Rectangular -> optimal Lp, Wp, accuracy, gain, bandwidth. Save full-page screenshots (1440px and 390px) as `before_*.png`. If models cannot be downloaded in your sandbox, say so and record the fallback mode - do not fake values.

## 5. STEP 2 - ADD FILES
Create/replace the 4 files from PART B exactly as written. Copy logos into `assets/`. Check: `python -m py_compile antdesigner_theme.py antenna_viz.py antenna_charts.py`; Dockerfile `COPY` will include `assets/` and the new files (verify, don't assume; do NOT edit the Dockerfile - report if it would not).

## 6. STEP 3 - WIRE IT INTO 10_web_app.py (small, reviewable edits)
1. `import antdesigner_theme as adtheme` and `from antenna_viz import antenna_animated_html` / `from antenna_charts import s11_vswr_animated_html`. `st.set_page_config(page_title="AntDesigner — AI-Based CPW Antenna Synthesis", page_icon=<assets/antdesigner_favicon.png>, layout="wide")`.
2. Load `assets/antdesigner_logo_light.png` and `assets/spu_logo_nav.png` as base64 data URIs (`AD_LOGO_URI`, `SPU_LOGO_URI`) replacing the old logo-loading code.
3. Call `adtheme.apply_theme()`, then `st.markdown(adtheme.render_header(AD_LOGO_URI), unsafe_allow_html=True)`.
4. DELETE the old ~370-line CSS block, the old navbar markup, the old hero markup and the old trailing `components.html` scroll/nav script (the new script lives in `antdesigner_theme.py`). Keep the hidden health-check div.
5. Structure (use real `st.tabs`; do NOT conditionally render tabs, so widget state survives tab switches):
   `tabs = st.tabs(["Home", "Forward", "Inverse", "AETHER", "Method & Validation"])`
   - HOME: `render_hero()`, `render_how_it_works()`, then the ORIGINAL "Project Introduction" panel and "System Overview" cards with their text unchanged (remove only the old credits box inside the intro, replaced by the team block), then `render_team(SPU_LOGO_URI)`.
   - FORWARD: `section_title("Forward simulation", "Predict performance from patch dimensions")`; `left, right = st.columns([1, 2.6])`. LEFT: Lp slider + number input, Wp slider + number input, the 5-40 mm / trained-range caption, shape select, neural-refinement checkbox, "Initiate Simulation" button (same keys/callbacks/order of logic). RIGHT: status heading, the metrics in `st.columns(4)`, the existing warnings/infos/captions, then two columns: (a) `st.tabs(["2D layout","3D structure"])` where 2D = `components.html(antenna_animated_html(shape_id, lp, wp, "<n>. <shape name>"), height=620)` and 3D = the existing `patch_3d_fig`; (b) `components.html(s11_vswr_animated_html(f, c, v, fr, bw), height=600)` replacing the old S11/VSWR plotly chart. Keep "Add to comparison", the comparison chart, the report download and the design-space expander exactly as they are.
   - INVERSE: `section_title("Inverse design", "Find dimensions for a target frequency")`; left = the 3 inputs + "Synthesize Optimal Geometry"; right = existing result banner/metrics + `components.html(antenna_animated_html(...), height=620)` instead of the old matplotlib drawing.
   - AETHER: existing chat code unchanged.
   - METHOD & VALIDATION: existing method cards, engine components, Engine Validation (self-test, CST vs. model) and Inverse Validation (inverse self-test + CSV download), all logic unchanged; plotly parity charts keep working through `antenna_charts`.
   - After the tabs: `st.markdown(adtheme.render_footer(), unsafe_allow_html=True)` (same wording as the original footer).
6. Other charts (`compare_fig`, `design_space_fig`, `error_scatter_fig`, `patch_3d_fig`) are already restyled inside `antenna_charts.py`; keep calling them as before. The static matplotlib `draw_antenna` stays available as a fallback (also restyled).
Checks after each sub-step: `python -m py_compile 10_web_app.py antdesigner_theme.py antenna_viz.py antenna_charts.py`; app boots with no traceback; no browser-console errors.
If `st.tabs` list pinned into the top bar (CSS in the theme, `position:fixed`) misbehaves in the installed Streamlit version, keep the tab list in normal flow under the logo bar and tell me - do not drop the design silently.

## 7. STEP 4 - VERIFY (all must pass; show evidence for each)
1. REGRESSION: repeat the Step 1 inputs; every number and engine-mode string must equal `baseline.json`.
2. DIFF AUDIT: `git diff --stat` and `git diff`: only the allowed files changed; no logic changes; no session-state/widget-key changes; `engine_v2.py`, `fly.toml`, `Dockerfile`, `requirements.txt`, `README.md` untouched. List each changed file with a one-line reason.
3. VISUAL: screenshots of EVERY tab at 1440px and 390px (Home, Forward before and after a run, Inverse before and after a run, AETHER, Method & Validation) and compare with `reference_preview.html`. Fonts load, no horizontal scroll, text readable, no overlapping text, no stray words (e.g. "pass"), metric values not truncated, the tab bar usable on 390px.
4. MOTION: headline words animate, ridges drift, tab underline slides, scroll reveals work, metrics count up after a run, drawing + curves draw themselves, chart hover tooltip works, Replay buttons work; with `prefers-reduced-motion` everything is static and fully visible.
5. CLICK EVERYTHING: both hero buttons switch to Inverse / Forward; sliders and number boxes stay in sync; shape select; Initiate Simulation; ML-refine checkbox; Add to comparison; report download; design-space expander; Synthesize Optimal Geometry; Run Self-Test; Compare CST vs. model; Run Inverse Self-Test + CSV download; AETHER with and without a key (no key -> info box).
6. `docker build` succeeds (else NOT VERIFIED). Do not deploy.

## 8. STEP 5 - REPORT (required format)
Branch + commits; before/after screenshots; a PASS / FAIL / NOT VERIFIED table for every check in Step 4 with evidence; everything that differed from this file and how you handled it; known problems you noticed but did NOT fix (list them); rollback command (`git checkout main`). Finish only when every check is PASS, or explain each FAIL / NOT VERIFIED and wait for me.

======================================================================
PART B - FILES TO CREATE VERBATIM
======================================================================

### B1. `.streamlit/config.toml`
````toml
# Native Streamlit theme (warm, light). MERGE into an existing config.toml; never overwrite other settings.
[theme]
base = "light"
primaryColor = "#4F46E5"
backgroundColor = "#F5F2EA"
secondaryBackgroundColor = "#FFFDF8"
textColor = "#14213D"
font = "sans serif"

````

### B2. `antdesigner_theme.py`
````python
"""
antdesigner_theme.py - AntDesigner warm/light visual layer for the Streamlit antenna app.

PRESENTATION ONLY. Does not import or touch the engine, models, CSV, validation, AETHER logic
or session-state keys.

Call order in 10_web_app.py (right after st.set_page_config):
    import antdesigner_theme as adtheme
    adtheme.apply_theme()
    st.markdown(adtheme.render_header(AD_LOGO_URI), unsafe_allow_html=True)
    tabs = st.tabs(["Home", "Forward", "Inverse", "AETHER", "Method & Validation"])
    with tabs[0]:
        st.markdown(adtheme.render_hero(), unsafe_allow_html=True)
        st.markdown(adtheme.render_how_it_works(), unsafe_allow_html=True)
        ...original Project Introduction + System Overview text, restyled...
        st.markdown(adtheme.render_team(SPU_LOGO_URI), unsafe_allow_html=True)
    ...
    st.markdown(adtheme.render_footer(), unsafe_allow_html=True)
"""
import json
import math
import streamlit as st
import streamlit.components.v1 as components

TEAM = ["Arwin Hunar", "Dunya Anwar", "Kara Nawzad", "Khazan Jafaar", "Ramyar Aram", "Ranw Jamil"]
SUPERVISOR = "Dr. Halgurd N. Awl"
TAB_NAMES = ["Home", "Forward", "Inverse", "AETHER", "Method & Validation"]   # must match st.tabs labels


def _flat(html: str) -> str:
    """st.markdown treats indented / blank lines as markdown blocks -> flatten the HTML."""
    return "".join(line.strip() for line in html.splitlines())


# ----------------------------------------------------------------------------- CSS
THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--paper:#F5F2EA;--card:#FFFDF8;--ink:#14213D;--mu:#5B6478;--ln:rgba(20,33,61,.14);--p:#6366F1;--p2:#4F46E5;--e:cubic-bezier(.22,.8,.3,1)}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],section.main{background:var(--paper)!important;color:var(--ink)}
[data-testid="stMain"]{overflow-x:hidden}
[data-testid="stHeader"],[data-testid="stToolbar"],#MainMenu,footer{display:none!important}
.block-container{max-width:1200px;padding:84px 20px 3rem!important}
html,body,p,li,label,span,div{font-family:Inter,system-ui,sans-serif}
h1,h2,h3,h4{font-family:Fraunces,Georgia,serif!important;font-weight:400!important;color:var(--ink)!important;letter-spacing:-.01em}
:focus-visible{outline:2px solid var(--p)!important;outline-offset:3px;border-radius:6px}

/* ---- top bar (logo) + Streamlit tab list pinned into it ---- */
.ad-bar{position:fixed;top:0;left:0;right:0;height:60px;z-index:1000;background:rgba(245,242,234,.92);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid var(--ln)}
.ad-bar .in{max-width:1200px;margin:0 auto;padding:0 20px;height:100%;display:flex;align-items:center}
.ad-bar img{height:24px;display:block}
[data-baseweb="tab-list"]{position:fixed!important;top:0;right:max(20px,calc((100vw - 1200px)/2 + 20px));height:60px;z-index:1001;gap:4px!important;background:transparent!important;overflow-x:auto;scrollbar-width:none}
[data-baseweb="tab-list"]::-webkit-scrollbar{display:none}
button[data-baseweb="tab"]{background:transparent!important;color:var(--mu)!important;font:500 14px Inter,sans-serif!important;padding:0 12px!important;height:60px;transition:color .25s}
button[data-baseweb="tab"]:hover,button[data-baseweb="tab"][aria-selected="true"]{color:var(--ink)!important}
[data-baseweb="tab-highlight"]{background:var(--p)!important;height:3px!important;border-radius:3px 3px 0 0;transition:left .45s var(--e),width .45s var(--e)!important}
[data-baseweb="tab-border"]{display:none!important}
[data-baseweb="tab-panel"]{padding-top:0!important;animation:ad-pin .6s var(--e)}
@keyframes ad-pin{from{opacity:0;transform:translateY(14px)}}
@media(max-width:900px){[data-baseweb="tab-list"]{left:150px;right:0}}

/* ---- hero ---- */
.ad-hero{position:relative;min-height:700px;padding-top:56px;overflow:hidden;width:100vw;margin-left:calc(50% - 50vw)}
.ad-hero .tx{position:relative;z-index:2;max-width:1200px;margin:0 auto;padding:0 20px}.ad-hero .tx>*{max-width:640px}
.ad-eye{font:500 12px Inter;letter-spacing:.14em;text-transform:uppercase;color:var(--p2);margin:0 0 18px;opacity:0;animation:ad-up .8s .05s forwards}
.ad-h1{font:400 clamp(38px,6vw,72px)/1.04 Fraunces,Georgia,serif;letter-spacing:-.02em;margin:0 0 20px;color:var(--ink)}
.ad-h1 .w{display:inline-block;opacity:0;transform:translateY(24px);animation:ad-up .9s var(--e) forwards;animation-delay:calc(.15s*var(--n))}.ad-h1 em{color:var(--p2)}
@keyframes ad-up{to{opacity:1;transform:none}}
.ad-lead{color:var(--mu);font-size:17px;line-height:1.6;margin:0 0 28px;opacity:0;animation:ad-up .9s .9s var(--e) forwards}
.ad-cta{display:flex;gap:12px;flex-wrap:wrap;opacity:0;animation:ad-up .9s 1.1s var(--e) forwards}
.ad-btn{display:inline-flex;align-items:center;background:var(--p2);color:#fff!important;border-radius:10px;padding:12px 20px;font:500 15px Inter;min-height:44px;text-decoration:none!important;cursor:pointer;
box-shadow:0 1px 0 rgba(20,33,61,.2),0 6px 16px -8px rgba(79,70,229,.7);transition:transform .2s var(--e),box-shadow .2s,background .2s}
.ad-btn:hover{transform:translateY(-2px);box-shadow:0 1px 0 rgba(20,33,61,.2),0 12px 22px -10px rgba(79,70,229,.8)}.ad-btn:active{transform:translateY(1px) scale(.98)}
.ad-btn.o{background:transparent;color:var(--ink)!important;box-shadow:inset 0 0 0 1.5px var(--ink)}.ad-btn.o:hover{background:var(--ink);color:#fff!important}
.ad-art{position:absolute;left:0;right:0;bottom:0;height:330px;pointer-events:none}.ad-art svg{width:100%;height:100%;display:block}
.rl{animation:ad-drift var(--s) linear infinite,ad-rise 1.4s calc(.2s*var(--i)) var(--e) both}
@keyframes ad-drift{to{transform:translateX(-1200px)}}@keyframes ad-rise{from{opacity:0;translate:0 50px}}
.arc{opacity:0;animation:ad-arc 2.4s var(--d) ease-out infinite}@keyframes ad-arc{0%{opacity:0;transform:translateX(-6px)}30%{opacity:1}100%{opacity:0;transform:translateX(10px)}}
.mast{animation:ad-rise 1.4s .9s var(--e) both}

/* ---- content blocks ---- */
.ad-sec{padding:56px 0 8px}.ad-sec h2{font:400 30px/1.15 Fraunces,Georgia,serif;margin:0 0 6px}
.ad-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:22px}
.ad-step{background:var(--card);border:1px solid var(--ln);border-radius:14px;padding:22px;transition:transform .35s var(--e),box-shadow .35s}
.ad-step:hover{transform:translateY(-4px);box-shadow:0 18px 30px -22px rgba(20,33,61,.5)}
.ad-step b{font:italic 400 44px Fraunces,Georgia,serif;color:var(--p2);display:block;line-height:1}.ad-step h3{font:600 16px Inter!important;margin:10px 0 4px}.ad-step p{margin:0;color:var(--mu);font-size:14px}
.ad-team{display:grid;grid-template-columns:1.5fr 1fr 150px;gap:28px;align-items:center;background:var(--card);border:1px solid var(--ln);border-radius:14px;padding:26px;margin-top:22px}
.ad-team ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,1fr);gap:4px 14px;font:400 19px Fraunces,Georgia,serif}.ad-team .one{grid-template-columns:1fr}.ad-team img{width:100%}
.ad-lbl{font:500 11px Inter;letter-spacing:.12em;text-transform:uppercase;color:var(--mu);display:block;margin:0 0 8px}
.rv{opacity:0;transform:translateY(22px);transition:opacity .8s var(--e),transform .8s var(--e)}.rv.in{opacity:1;transform:none}
.ad-title{font:400 32px/1.15 Fraunces,Georgia,serif;margin:34px 0 4px;color:var(--ink)}.ad-sub{color:var(--mu);margin:0 0 18px}
.intro-panel,.info-card,.result-banner,.intro-credits{background:var(--card)!important;border:1px solid var(--ln)!important;border-radius:14px!important;color:var(--ink)!important;box-shadow:none!important}
.info-card{padding:22px!important;transition:transform .35s var(--e),box-shadow .35s}.info-card:hover{transform:translateY(-4px);box-shadow:0 18px 30px -22px rgba(20,33,61,.5)}
.status-heading{font-family:Fraunces,Georgia,serif;font-weight:400;color:var(--ink)}
.health-hidden{display:none!important}
.ad-foot{border-top:1px solid var(--ln);margin-top:46px;padding-top:18px;color:var(--mu);font-size:13px;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
@media(max-width:900px){.ad-steps,.ad-team{grid-template-columns:1fr}.ad-hero{min-height:600px}.ad-art{height:260px}.ad-team img{max-width:140px}}

/* ---- Streamlit widgets ---- */
.stButton>button,.stDownloadButton>button{background:var(--p2)!important;color:#fff!important;border:0!important;border-radius:10px!important;min-height:44px;padding:.6rem 1.3rem!important;font-weight:500!important;
box-shadow:0 1px 0 rgba(20,33,61,.2),0 6px 16px -8px rgba(79,70,229,.7);transition:transform .2s var(--e),box-shadow .2s!important}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-2px);box-shadow:0 1px 0 rgba(20,33,61,.2),0 12px 22px -10px rgba(79,70,229,.8)}.stButton>button:active{transform:translateY(1px) scale(.98)}
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"]>div{background:#fff!important;border:1.5px solid var(--ln)!important;border-radius:10px!important;transition:border-color .2s,box-shadow .2s}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within{border-color:var(--p2)!important;box-shadow:0 0 0 4px rgba(99,102,241,.15)!important}
input,textarea{color:var(--ink)!important;font-family:"JetBrains Mono",ui-monospace,monospace!important}
[data-testid="stMetric"]{background:var(--card);border:1px solid var(--ln);border-radius:14px;padding:14px 16px;transition:transform .3s var(--e),box-shadow .3s}
[data-testid="stMetric"]:hover{transform:translateY(-3px);box-shadow:0 16px 28px -22px rgba(20,33,61,.5)}
[data-testid="stMetricLabel"]{color:var(--mu)!important;text-transform:uppercase;letter-spacing:.1em;font-size:11px!important}
[data-testid="stMetricValue"]{color:var(--ink)!important;font-family:"JetBrains Mono",ui-monospace,monospace!important;font-weight:500!important}
[data-testid="stAlert"]{background:rgba(99,102,241,.08)!important;border:1px solid rgba(99,102,241,.3)!important;border-radius:12px!important;color:var(--ink)!important}
[data-testid="stChatMessage"]{background:var(--card)!important;border:1px solid var(--ln);border-radius:14px}[data-testid="stChatInput"]{background:#fff!important;border-radius:12px!important}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid var(--ln);border-radius:12px;overflow:hidden}
[data-testid="stExpander"]{background:var(--card);border:1px solid var(--ln)!important;border-radius:14px}
hr{border-color:var(--ln)!important}
@media(prefers-reduced-motion:reduce){*{animation-duration:.01ms!important;animation-delay:0s!important;animation-iteration-count:1!important;transition-duration:.01ms!important}.ad-eye,.ad-lead,.ad-cta,.ad-h1 .w,.rv{opacity:1;transform:none}}
"""

# ----------------------------------------------------------------------------- JS (runs in the PARENT page)
PARENT_JS = r"""
(function(){
 if(window.__adWarm===1) return; window.__adWarm=1;
 const d=document, W=window, rm=W.matchMedia('(prefers-reduced-motion: reduce)').matches;
 /* hero buttons -> click the matching Streamlit tab */
 d.addEventListener('click',function(ev){
  const a=ev.target.closest&&ev.target.closest('.ad-go'); if(!a) return; ev.preventDefault();
  const want=a.getAttribute('data-target');
  const tab=[...d.querySelectorAll('button[role="tab"]')].find(t=>t.textContent.trim()===want);
  if(tab){tab.click(); const m=d.querySelector('[data-testid="stMain"]'); if(m) m.scrollTo({top:0});}
 },true);
 /* scroll-reveal for .rv blocks */
 const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in'); io.unobserve(e.target);}}),{threshold:.15});
 function scan(){d.querySelectorAll('.rv:not(.in)').forEach(x=>io.observe(x));}
 /* metric count-up (once, when a value first appears) */
 function countUp(e){
  if(rm||e.dataset.adc) return; e.dataset.adc='1';
  const t=e.textContent.trim(), m=t.match(/^(-?\d[\d,]*\.?\d*)(.*)$/); if(!m) return;
  const raw=m[1].replace(/,/g,''), v=parseFloat(raw), dec=(raw.split('.')[1]||'').length, tail=m[2], t0=performance.now();
  (function f(n){const k=Math.min((n-t0)/900,1),q=1-Math.pow(1-k,3);e.textContent=(k<1?(v*q).toFixed(dec):m[1])+tail;if(k<1)requestAnimationFrame(f);})(t0);
 }
 const mo=new MutationObserver(()=>{scan(); d.querySelectorAll('[data-testid="stMetricValue"]').forEach(countUp);});
 mo.observe(d.body,{childList:true,subtree:true}); scan();
 /* ridge parallax (desktop pointer) */
 if(!rm&&W.matchMedia('(pointer:fine)').matches) d.addEventListener('pointermove',function(e){
  const x=e.clientX/W.innerWidth-.5; d.querySelectorAll('.ad-art .rl').forEach((g,i)=>{g.parentNode.style.transform='translateX('+(x*-14*(i+1))+'px)';});
 });
})();
"""


# ----------------------------------------------------------------------------- hero art
def _ridge(seed, base, amp, period=1200):
    """Closed, periodic ridge outline (so it can drift forever)."""
    pts = []
    for x in range(0, 2 * period + 1, 10):
        t = 2 * math.pi * x / period
        y = base - amp * (0.55 * abs(math.sin(t * (1 + seed % 2) + seed))
                          + 0.30 * math.sin(t * (3 + seed % 3) + seed * 1.7) + 0.15 * math.sin(t * 7 + seed * 2.3))
        pts.append((x, y))
    return "M" + "L".join(f"{x} {y:.1f}" for x, y in pts) + f"L{2 * period} 420L0 420Z"


def _art_svg():
    layers = [(1, 250, 110, "rgba(20,33,61,.07)", "rgba(20,33,61,.16)", 140),
              (2, 290, 95, "rgba(20,33,61,.10)", "rgba(20,33,61,.22)", 100),
              (3, 330, 80, "rgba(99,102,241,.10)", "rgba(79,70,229,.45)", 70),
              (4, 370, 60, "#EBE5D6", "rgba(20,33,61,.55)", 45)]
    ridges = "".join(f'<g class="rl" style="--s:{sp}s;--i:{i}"><path d="{_ridge(sd, b, am)}" fill="{fl}" stroke="{st}" '
                     f'stroke-width="1.4" vector-effect="non-scaling-stroke"/></g>' for i, (sd, b, am, fl, st, sp) in enumerate(layers))
    mast = ('<g class="mast"><path d="M-40 420C30 384 90 372 150 372S270 388 340 420Z" fill="#F5F2EA" stroke="rgba(20,33,61,.55)"/>'
            '<g transform="translate(150 372)"><path d="M0 0V-96" stroke="#14213D" stroke-width="2"/>'
            '<rect x="-16" y="-124" width="32" height="30" rx="2" fill="rgba(99,102,241,.3)" stroke="#4F46E5" stroke-width="2"/>'
            '<rect x="-11" y="-119" width="22" height="20" fill="#6366F1" opacity=".55"/>'
            '<g fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round">'
            '<path class="arc" style="--d:0s" d="M24 -150a40 40 0 0 1 0 52"/><path class="arc" style="--d:.8s" d="M36 -164a62 62 0 0 1 0 80"/>'
            '<path class="arc" style="--d:1.6s" d="M48 -178a84 84 0 0 1 0 108"/></g></g></g>')
    return f'<svg viewBox="0 0 1200 420" preserveAspectRatio="xMidYMax slice" aria-hidden="true">{ridges}<g transform="translate(860 0)">{mast}</g></svg>'


# ----------------------------------------------------------------------------- HTML blocks
def render_header(logo_data_uri: str = "") -> str:
    """Fixed top bar with the AntDesigner logo (charcoal+purple version for light backgrounds)."""
    img = f'<img src="{logo_data_uri}" alt="AntDesigner">' if logo_data_uri else '<b style="font:600 20px Inter">AntDesigner</b>'
    return _flat(f'<div class="ad-bar"><div class="in">{img}</div></div>')


def render_hero() -> str:
    words = ["We", "taught", "a", "neural", "network", "to", "<em>design</em>", "<em>antennas.</em>"]
    h1 = " ".join(f'<span class="w" style="--n:{i + 1}">{w}</span>' for i, w in enumerate(words))
    return _flat(f"""
    <section class="ad-hero"><div class="tx">
      <p class="ad-eye">Sulaymaniyah Polytechnic University &middot; Graduation project 2025&ndash;2026</p>
      <h1 class="ad-h1">{h1}</h1>
      <p class="ad-lead">Give it a patch size and it predicts how the antenna behaves. Give it a frequency between 1 and 7 GHz and it suggests the size to build. It learned from CST simulations, and it is tested against them.</p>
      <div class="ad-cta"><a class="ad-btn ad-go" href="#" data-target="Inverse">Design for a frequency</a><a class="ad-btn o ad-go" href="#" data-target="Forward">Predict from dimensions</a></div>
    </div><div class="ad-art">{_art_svg()}</div></section>""")


def render_how_it_works() -> str:
    return _flat("""
    <div class="ad-sec rv"><h2>How it works</h2><div class="ad-steps">
      <div class="ad-step"><b>1</b><h3>Choose</h3><p>Pick one of 12 patch shapes and type a size, or type the frequency you want to reach.</p></div>
      <div class="ad-step"><b>2</b><h3>Predict</h3><p>The engine returns the S11 and VSWR curves, the resonance and the bandwidth.</p></div>
      <div class="ad-step"><b>3</b><h3>Check</h3><p>Built-in self-tests compare the engine with held-out CST simulations.</p></div></div></div>""")


def render_team(spu_logo_data_uri: str = "") -> str:
    li = "".join(f"<li>{n}</li>" for n in TEAM)
    img = f'<img src="{spu_logo_data_uri}" alt="Sulaymaniyah Polytechnic University">' if spu_logo_data_uri else ""
    return _flat(f"""
    <div class="ad-sec rv"><h2>The team</h2><div class="ad-team">
      <div><span class="ad-lbl">Prepared by</span><ul>{li}</ul></div>
      <div><span class="ad-lbl">Supervised by</span><ul class="one"><li>{SUPERVISOR}</li></ul></div>{img}</div></div>""")


def section_title(title: str, subtitle: str = "") -> str:
    sub = f'<p class="ad-sub">{subtitle}</p>' if subtitle else ""
    return f'<h2 class="ad-title">{title}</h2>{sub}'


def render_footer() -> str:
    return _flat("""<div class="ad-foot"><span>Technical College of Engineering &mdash; Communication Department &middot; Sulaymaniyah Polytechnic University</span>
    <span>Academic year 2025&ndash;2026 &middot; AI-Based CPW Antenna Synthesis</span></div>""")


def apply_theme():
    """CSS + behaviour. Call once, right after st.set_page_config()."""
    st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)
    code = json.dumps(PARENT_JS)
    components.html(
        "<script>(function(){try{const d=window.parent.document;if(d.getElementById('ad-js'))return;"
        "const s=d.createElement('script');s.id='ad-js';s.textContent=" + code + ";d.head.appendChild(s);}"
        "catch(e){console.error('AntDesigner theme: cannot reach parent document',e);}})();</script>", height=0)

````

### B3. `antenna_viz.py`  (replaces the existing file; geometry unchanged)
````python
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def draw_antenna(antenna_id, lp, wp):
    # Set high resolution
    fig, ax = plt.subplots(figsize=(8, 10), dpi=100)
    fig.patch.set_facecolor('#FFFDF8'); ax.set_facecolor('#FFFDF8')
    
    # --- TECHNICAL DESIGN PALETTE ---
    substrate_color = '#EFEAD9' # FR-4 substrate (warm paper)
    copper_color = '#6F72F0'    # conductor (AntDesigner purple)
    shadow_color = '#14213D'    # soft ink shadow under the metal
    
    lf, wf, g, ws, ls = 15.0, 3.0, 0.5, 50.0, 60.0
    g_ymax = 12.0 # Grounds end at 12mm (lf-3)

    # 1. DRAW SUBSTRATE
    ax.add_patch(patches.Rectangle((-ws/2, 0), ws, ls, color=substrate_color, ec=(.08, .13, .24, .5), lw=1, zorder=1))
    # faint blueprint grid (every 5 mm)
    for _gx in np.arange(-25, 26, 5): ax.plot([_gx, _gx], [0, ls], color=(.08, .13, .24, .08), lw=.6, zorder=1.1)
    for _gy in np.arange(0, ls + 1, 5): ax.plot([-ws/2, ws/2], [_gy, _gy], color=(.08, .13, .24, .08), lw=.6, zorder=1.1)
    
    # 2. HELPER FUNCTION (Manual Shadow + Metal)
    def add_metal(patch_obj):
        # Create a manual shadow by shifting the shape
        if isinstance(patch_obj, patches.Rectangle):
            shadow = patches.Rectangle((patch_obj.get_x()+0.3, patch_obj.get_y()-0.3), 
                                      patch_obj.get_width(), patch_obj.get_height(), color=shadow_color, zorder=2)
        elif isinstance(patch_obj, patches.Polygon):
            shadow = patches.Polygon(patch_obj.get_xy() + [0.3, -0.3], color=shadow_color, zorder=2)
        elif isinstance(patch_obj, patches.Ellipse):
            shadow = patches.Ellipse((patch_obj.center[0]+0.3, patch_obj.center[1]-0.3), 
                                    patch_obj.width, patch_obj.height, color=shadow_color, zorder=2)
        
        shadow.set_alpha(0.16)
        ax.add_patch(shadow)
        patch_obj.set_facecolor(copper_color)
        patch_obj.set_edgecolor('#3B3DB0')
        patch_obj.set_linewidth(1)
        patch_obj.set_zorder(3)
        ax.add_patch(patch_obj)

    # 3. DRAW GROUNDS AND FEED
    gw = (ws/2) - (wf/2) - g
    add_metal(patches.Rectangle((-ws/2, 0), gw, g_ymax)) # Left
    add_metal(patches.Rectangle((wf/2 + g, 0), gw, g_ymax)) # Right
    add_metal(patches.Rectangle((-wf/2, 0), wf, lf)) # Feed

    # 4. THE 12 ANTENNA SHAPES (EXACT CST REPLICAS)
    if antenna_id == 1: # Rectangle
        add_metal(patches.Rectangle((-wp/2, lf), wp, lp))
        
    elif antenna_id == 2: # Stepped
        add_metal(patches.Rectangle((-7.5, lf), 15, lp/2))
        add_metal(patches.Rectangle((-wp/2, lf + lp/2), wp, lp/2))
        
    elif antenna_id == 3: # T-Shape
        add_metal(patches.Rectangle((-1.5, lf), 3, lp/2))
        add_metal(patches.Rectangle((-wp/2, lf + lp/2), wp, lp/2))
        
    elif antenna_id == 4: # Ellipse
        add_metal(patches.Ellipse((0, lf + lp/2), wp, lp))
        
    elif antenna_id == 5: # Semi-Ellipse
        theta = np.linspace(0, np.pi, 50)
        x = (wp/2) * np.cos(theta)
        y = lf + lp * np.sin(theta)
        pts = np.column_stack([x, y])
        pts = np.vstack([pts, [wp/2, lf], [-wp/2, lf]])
        add_metal(patches.Polygon(pts))

    elif antenna_id == 6: # Pie-Sector (Curved Fan)
        # 1. Create the arc for the top of the "fan"
        # theta goes from 0 (Right) to pi (Left)
        theta = np.linspace(0, np.pi, 50)
        
        # Width controlled by wp
        x_arc = (wp/2) * np.cos(theta)
        
        # Height controlled by lp (Top arc starts at 60% of lp height)
        y_arc = (lf + lp * 0.6) + (lp * 0.4) * np.sin(theta)
        pts_arc = np.column_stack([x_arc, y_arc])
        
        # 2. COMBINE POINTS IN CORRECT CIRCULAR ORDER
        # Order: Bottom-Right -> Arc (Right to Left) -> Bottom-Left
        # This prevents the lines from crossing (the hourglass error)
        pts = np.vstack([
            [1.5, lf],      # Bottom-Right: Connects to feed line top-right corner
            pts_arc,        # The entire curved top (50 points)
            [-1.5, lf]      # Bottom-Left: Connects to feed line top-left corner
        ])
        
        add_metal(patches.Polygon(pts))

    elif antenna_id == 7: # Triangle
        add_metal(patches.Polygon([[-wp/2, lf], [wp/2, lf], [0, lf+lp]]))

    elif antenna_id == 8: # Trapezoid
        add_metal(patches.Polygon([[-1.5, lf], [1.5, lf], [wp/2, lf+lp], [-wp/2, lf+lp]]))

    elif antenna_id == 9: # Diamond
        add_metal(patches.Polygon([[-1.5, lf], [1.5, lf], [wp/2, lf+lp/2], [0, lf+lp], [-wp/2, lf+lp/2]]))

    elif antenna_id == 10: # Hexagon
        y1, y2 = lf + lp/3, lf + 2*lp/3
        pts = [[-1.5, lf], [1.5, lf], [wp/2, y1], [wp/2, y2], [1.5, lf+lp], [-1.5, lf+lp], [-wp/2, y2], [-wp/2, y1]]
        add_metal(patches.Polygon(pts))

    elif antenna_id == 11: # Pentagon
        add_metal(patches.Polygon([[-wp/2, lf], [wp/2, lf], [wp/2, lf+lp/2], [0, lf+lp], [-wp/2, lf+lp/2]]))

    elif antenna_id == 12: # Cross
        add_metal(patches.Rectangle((-1.5, lf), 3, lp))
        add_metal(patches.Rectangle((-wp/2, lf + lp/2 - 1.5), wp, 3))

    # 5. PROFESSIONAL DIMENSIONS (Technical Boxes)
    def add_label(start, end, text, is_vert=True):
        col = '#14213D'
        if is_vert:
            ax.annotate('', xy=(start[0], start[1]), xytext=(end[0], end[1]), arrowprops=dict(arrowstyle='<->', color=col))
            ax.text(start[0]+2, (start[1]+end[1])/2, text, rotation=90, va='center', fontweight='bold', color='#14213D',
                    bbox=dict(boxstyle="round,pad=0.3", fc='#FFFDF8', ec=col, lw=1), fontsize=8)
        else:
            ax.annotate('', xy=(start[0], start[1]), xytext=(end[0], end[1]), arrowprops=dict(arrowstyle='<->', color='#4F46E5'))
            ax.text((start[0]+end[0])/2, start[1]-4, text, ha='center', fontweight='bold', color='#14213D',
                    bbox=dict(boxstyle="round,pad=0.3", fc='#FFFDF8', ec='#4F46E5', lw=1), fontsize=8)

    add_label((wp/2 + 8, lf), (wp/2 + 8, lf + lp), f"Lp: {lp}mm")
    add_label((-wp/2, lf - 8), (wp/2, lf - 8), f"Wp: {wp}mm", is_vert=False)

    # Final settings
    ax.set_xlim(-30, 30); ax.set_ylim(-5, 65)
    ax.set_aspect('equal'); ax.axis('off')
    plt.title(f"AI PREDICTED DESIGN: ANTENNA {antenna_id}", fontsize=12, fontweight='bold', pad=20, color='#14213D')
    return fig

if __name__ == "__main__":
    # Test the Stepped Rectangle (ID 2)
    draw_antenna(12, 15, 30)
    plt.show()

# ---------------------------------------------------------------------------
# Geometry as data
#
# The 12 patch outlines expressed as polygons, so they can be rendered by
# something other than matplotlib (see antenna_charts.patch_3d_fig). The
# constants and vertex definitions are identical to draw_antenna() above.
# ---------------------------------------------------------------------------
LF, WF, GAP, WS, LS = 15.0, 3.0, 0.5, 50.0, 60.0
G_YMAX = 12.0


def _rect(x, y, w, h):
    return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=float)


def patch_polygons(antenna_id, lp, wp):
    """Return the metal outlines for a given design.

    dict with keys:
      'patch'     list of (N,2) arrays -- the radiating element
      'grounds'   list of (N,2) arrays -- the two CPW ground planes
      'feed'      (N,2) array          -- the feed line
      'substrate' (width, length)      -- the FR-4 slab footprint
    """
    gw = (WS / 2) - (WF / 2) - GAP
    grounds = [_rect(-WS / 2, 0, gw, G_YMAX), _rect(WF / 2 + GAP, 0, gw, G_YMAX)]
    feed = _rect(-WF / 2, 0, WF, LF)

    lf, wp, lp = float(LF), float(wp), float(lp)
    aid = int(antenna_id)
    patch = []

    if aid == 1:                                     # Rectangle
        patch = [_rect(-wp / 2, lf, wp, lp)]
    elif aid == 2:                                   # Stepped
        patch = [_rect(-7.5, lf, 15, lp / 2), _rect(-wp / 2, lf + lp / 2, wp, lp / 2)]
    elif aid == 3:                                   # T-Shape
        patch = [_rect(-1.5, lf, 3, lp / 2), _rect(-wp / 2, lf + lp / 2, wp, lp / 2)]
    elif aid == 4:                                   # Ellipse
        t = np.linspace(0, 2 * np.pi, 90)
        patch = [np.column_stack([(wp / 2) * np.cos(t) + 0.0,
                                  lf + lp / 2 + (lp / 2) * np.sin(t)])]
    elif aid == 5:                                   # Semi-Ellipse
        t = np.linspace(0, np.pi, 50)
        pts = np.column_stack([(wp / 2) * np.cos(t), lf + lp * np.sin(t)])
        patch = [np.vstack([pts, [[wp / 2, lf], [-wp / 2, lf]]])]
    elif aid == 6:                                   # Pie-Sector
        t = np.linspace(0, np.pi, 50)
        arc = np.column_stack([(wp / 2) * np.cos(t),
                               (lf + lp * 0.6) + (lp * 0.4) * np.sin(t)])
        patch = [np.vstack([[1.5, lf], arc, [-1.5, lf]])]
    elif aid == 7:                                   # Triangle
        patch = [np.array([[-wp / 2, lf], [wp / 2, lf], [0, lf + lp]], dtype=float)]
    elif aid == 8:                                   # Trapezoid
        patch = [np.array([[-1.5, lf], [1.5, lf], [wp / 2, lf + lp], [-wp / 2, lf + lp]], dtype=float)]
    elif aid == 9:                                   # Diamond
        patch = [np.array([[-1.5, lf], [1.5, lf], [wp / 2, lf + lp / 2],
                           [0, lf + lp], [-wp / 2, lf + lp / 2]], dtype=float)]
    elif aid == 10:                                  # Hexagon
        y1, y2 = lf + lp / 3, lf + 2 * lp / 3
        patch = [np.array([[-1.5, lf], [1.5, lf], [wp / 2, y1], [wp / 2, y2],
                           [1.5, lf + lp], [-1.5, lf + lp], [-wp / 2, y2], [-wp / 2, y1]], dtype=float)]
    elif aid == 11:                                  # Pentagon
        patch = [np.array([[-wp / 2, lf], [wp / 2, lf], [wp / 2, lf + lp / 2],
                           [0, lf + lp], [-wp / 2, lf + lp / 2]], dtype=float)]
    elif aid == 12:                                  # Cross
        patch = [_rect(-1.5, lf, 3, lp), _rect(-wp / 2, lf + lp / 2 - 1.5, wp, 3)]

    return {"patch": patch, "grounds": grounds, "feed": feed,
            "substrate": (float(WS), float(LS))}

# ---------------------------------------------------------------------------
# Animated, interactive antenna drawing (AntDesigner warm/light style)
#
# Same geometry as draw_antenna() -- it is built from patch_polygons(), so every
# vertex comes from the real design. Use it in Streamlit with:
#     import streamlit.components.v1 as components
#     components.html(antenna_animated_html(aid, lp, wp, label), height=640)
# Motion: blueprint grid fades in, substrate + metal outlines draw themselves, the
# feed grows, dimension lines extend and their numbers count up, current flows along
# the feed, and (mouse) the board tilts in 3D. The expanding rings are DECORATIVE and
# are labelled "illustrative" on screen -- they are not an EM simulation.
# Honors prefers-reduced-motion.
# ---------------------------------------------------------------------------
def _ad_path(poly, kx, ky):
    pts = [(kx(x), ky(y)) for x, y in np.asarray(poly, dtype=float)]
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"


def antenna_animated_html(antenna_id, lp, wp, label="", height=640):
    g = patch_polygons(antenna_id, lp, wp)
    K = 8.0                                   # px per mm
    kx = lambda x: (x + 30.0) * K
    ky = lambda y: (65.0 - y) * K
    sw, sl = g["substrate"]
    sub = (f'<rect class="sub" x="{kx(-sw/2):.1f}" y="{ky(sl):.1f}" width="{sw*K:.1f}" height="{sl*K:.1f}" rx="6" pathLength="1"/>')
    grid = "".join(f'<path d="M{kx(x):.1f} {ky(0):.1f}V{ky(sl):.1f}"/>' for x in np.arange(-25, 26, 5)) + \
           "".join(f'<path d="M{kx(-sw/2):.1f} {ky(y):.1f}H{kx(sw/2):.1f}"/>' for y in np.arange(0, sl + 1, 5))
    grounds = "".join(f'<path class="gnd" style="--d:{.9+i*.15}s;--dx:{-14 if i==0 else 14}px" d="{_ad_path(p,kx,ky)}"/>' for i, p in enumerate(g["grounds"]))
    feed = f'<path class="feed" d="{_ad_path(g["feed"],kx,ky)}"/>'
    patch = "".join(f'<path class="patch" pathLength="1" style="--d:{1.5+i*.2}s" d="{_ad_path(p,kx,ky)}"/>' for i, p in enumerate(g["patch"]))
    allp = np.vstack(g["patch"]); cx, cy = kx(float(allp[:, 0].mean())), ky(float((allp[:, 1].min() + allp[:, 1].max()) / 2))
    top = float(allp[:, 1].max()); lf = 15.0
    flow = f'M{kx(0):.1f} {ky(0):.1f}V{ky(lf+ (top-lf)*0.55):.1f}'
    rings = "".join(f'<circle class="ring" style="--d:{i*1.3}s" cx="{cx:.1f}" cy="{cy:.1f}" r="20"/>' for i in range(3))
    # dimension lines (same positions as draw_antenna)
    xr = kx(wp / 2 + 8); y1, y2 = ky(lf), ky(lf + lp)
    xa, xb, yd = kx(-wp / 2), kx(wp / 2), ky(lf - 8)
    dims = f'''
<g class="dim" style="--d:2.4s"><path class="dl" pathLength="1" d="M{xr:.1f} {y1:.1f}V{y2:.1f}"/><path d="M{xr-6:.1f} {y1:.1f}h12M{xr-6:.1f} {y2:.1f}h12"/>
<text class="dt" x="{xr+12:.1f}" y="{(y1+y2)/2:.1f}" transform="rotate(90 {xr+12:.1f} {(y1+y2)/2:.1f})" text-anchor="middle">Lp = <tspan class="cnt" data-v="{lp}">0</tspan> mm</text></g>
<g class="dim" style="--d:2.7s"><path class="dl" pathLength="1" d="M{xa:.1f} {yd:.1f}H{xb:.1f}"/><path d="M{xa:.1f} {yd-6:.1f}v12M{xb:.1f} {yd-6:.1f}v12"/>
<text class="dt" x="{(xa+xb)/2:.1f}" y="{yd+22:.1f}" text-anchor="middle">Wp = <tspan class="cnt" data-v="{wp}">0</tspan> mm</text></g>'''
    title = (label or f"Antenna {antenna_id}").replace("<", "").replace(">", "")
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;height:100%;background:transparent;font-family:Inter,system-ui,sans-serif}}
.card{{position:relative;height:100%;border:1px solid rgba(20,33,61,.14);border-radius:14px;overflow:hidden;background:radial-gradient(60% 50% at 50% 100%,rgba(99,102,241,.07),transparent 70%),#FFFDF8;perspective:1100px}}
.stage{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;transition:transform .25s ease-out;transform-style:preserve-3d}}
svg{{height:92%;max-width:96%;overflow:visible}}
.cap{{position:absolute;left:18px;top:14px;color:#14213D;font:500 16px Fraunces,Georgia,serif}}.cap small{{display:block;color:#5B6478;font:11px Inter;letter-spacing:.14em;text-transform:uppercase;margin-bottom:4px}}
.ill{{position:absolute;right:16px;bottom:12px;color:#5B6478;font-size:11px;opacity:.8}}
.rp{{position:absolute;right:14px;top:12px;background:rgba(20,33,61,.04);color:#14213D;border:1px solid rgba(20,33,61,.18);border-radius:999px;padding:6px 12px;font:12px Inter;cursor:pointer}}
.rp:hover{{border-color:#6366F1}}
.grid path{{stroke:rgba(20,33,61,.08);stroke-width:.6;fill:none;opacity:0;animation:fi 1s .1s forwards}}
.sub{{fill:#EFEAD9;fill-opacity:0;stroke:rgba(20,33,61,.5);stroke-width:1.2;stroke-dasharray:1;stroke-dashoffset:1;animation:dr 1.3s .3s forwards,fillin .8s 1s forwards}}
.gnd{{fill:rgba(20,33,61,.12);stroke:#14213D;stroke-width:1.1;opacity:0;transform:translateX(var(--dx));animation:slide .8s var(--d) cubic-bezier(.22,.8,.3,1) forwards}}
.feed{{fill:#6366F1;stroke:#3B3DB0;stroke-width:1.1;transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:grow .9s 1.1s cubic-bezier(.22,.8,.3,1) forwards}}
.patch{{fill:rgba(99,102,241,.28);fill-opacity:0;stroke:#3B3DB0;stroke-width:1.5;stroke-dasharray:1;stroke-dashoffset:1;animation:dr 1.4s var(--d) forwards,pfill .9s calc(var(--d) + 1s) forwards,breathe 4.5s 4s ease-in-out infinite}}
.flow{{fill:none;stroke:#fff;stroke-width:2.4;stroke-linecap:round;stroke-dasharray:.07 .93;stroke-dashoffset:1;opacity:0;animation:fi .5s 2.4s forwards,fl 2.2s 2.4s linear infinite;filter:drop-shadow(0 0 5px #6366F1)}}
.ring{{display:none;fill:none;stroke:#6366F1;stroke-width:1.3;opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 4s var(--d) ease-out infinite;animation-delay:calc(3s + var(--d))}}
.dim .dl{{stroke:#4F46E5;stroke-width:1.3;fill:none;stroke-dasharray:1;stroke-dashoffset:1;animation:dr .9s var(--d) forwards}}
.dim path:not(.dl){{stroke:#4F46E5;stroke-width:1.3;fill:none;opacity:0;animation:fi .4s calc(var(--d) + .6s) forwards}}
.dt{{fill:#14213D;font:600 12px Inter,sans-serif;opacity:0;animation:fi .6s calc(var(--d) + .7s) forwards}}
@keyframes fi{{to{{opacity:1}}}}@keyframes dr{{to{{stroke-dashoffset:0}}}}@keyframes fillin{{to{{fill-opacity:.92}}}}@keyframes pfill{{to{{fill-opacity:1}}}}
@keyframes slide{{to{{opacity:1;transform:none}}}}@keyframes grow{{to{{transform:scaleY(1)}}}}@keyframes fl{{to{{stroke-dashoffset:0}}}}
@keyframes breathe{{50%{{filter:drop-shadow(0 0 9px rgba(99,102,241,.9))}}}}
@keyframes ring{{0%{{opacity:.55;transform:scale(1)}}100%{{opacity:0;transform:scale(11)}}}}
@media(prefers-reduced-motion:reduce){{*{{animation-duration:.01ms!important;animation-delay:0s!important;animation-iteration-count:1!important}}.ring,.flow{{display:none}}}}
</style></head><body><div class="card" id="c"><div class="cap"><small>Predicted geometry</small>{title}</div>
<button class="rp" id="rp" aria-label="Replay animation">&#8635; Replay</button>
<div class="stage" id="st"><svg id="s" viewBox="0 0 480 560" role="img" aria-label="{title}: patch length {lp} mm, patch width {wp} mm">
<g class="grid">{grid}</g><g>{rings}</g>{sub}{grounds}{feed}{patch}<path class="flow" pathLength="1" d="{flow}"/>{dims}</svg></div>
<div class="ill">Rings are illustrative, not a field simulation</div></div>
<script>
const rm=matchMedia('(prefers-reduced-motion: reduce)').matches;
function count(){{document.querySelectorAll('.cnt').forEach(e=>{{const v=+e.dataset.v,t0=performance.now()+(rm?-9999:2900);
(function f(n){{const k=Math.min(Math.max((n-t0)/900,0),1),q=1-Math.pow(1-k,3);e.textContent=(v*q).toFixed(2);if(k<1)requestAnimationFrame(f)}})(performance.now())}})}}
count();
document.getElementById('rp').onclick=()=>{{const s=document.getElementById('s'),p=s.parentNode;const n=s.cloneNode(true);p.replaceChild(n,s);n.id='s';count()}};
const st=document.getElementById('st');
if(!rm&&matchMedia('(pointer:fine)').matches)document.getElementById('c').addEventListener('pointermove',e=>{{const r=e.currentTarget.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;st.style.transform='rotateY('+(x*14)+'deg) rotateX('+(-y*10)+'deg)'}});
document.getElementById('c').addEventListener('pointerleave',()=>st.style.transform='');
</script></body></html>'''

````

### B4. `antenna_charts.py`  (replaces the existing file)
````python
"""
Interactive Plotly charts for the antenna synthesis app.

Replaces the static matplotlib PNGs in the forward-design section. The numbers come
from the engine unchanged -- this module only renders them. Plotly figures are
vector/SVG in the browser, so they cost far less bandwidth than the base64 raster
PNGs Streamlit was pushing on every rerun, and they give hover readouts of the exact
S11/VSWR at any frequency, which is what an RF engineer actually wants from a plot.

Note on Smith charts: a Smith chart needs complex S11 (magnitude AND phase). The CST
dataset stores magnitude in dB only, so a true Smith chart cannot be drawn from it
without fabricating phase. The VSWR trace below carries the same matching information
that is actually supported by the data.
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Shared dark palette, matched to the app's existing CSS.
BG = "rgba(0,0,0,0)"
PAPER = "rgba(0,0,0,0)"
GRID = "rgba(20,33,61,0.10)"
AXIS = "#5B6478"
TEXT = "#14213D"
S11_COLOR = "#4F46E5"                     # AntDesigner palette: purple + white/grey only
VSWR_COLOR = "#14213D"
ACCENT = "#14213D"                        # resonance marker / dimension lines
DANGER = "rgba(20,33,61,0.55)"         # threshold lines: white dashed (no red)
GOOD = "#6366F1"

SERIES = ["#4F46E5", "#14213D", "#6366F1", "#8B8DF7", "#5B6478", "#3B3DB0"]


def _style(fig, height=430):
    fig.update_layout(
        template=None,
        paper_bgcolor=PAPER,
        plot_bgcolor=BG,
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=TEXT),
        height=height,
        margin=dict(l=58, r=24, t=54, b=48),
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=12, bordercolor="#6366F1"),
        legend=dict(orientation="h", yanchor="bottom", y=1.005, x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    return fig


def _axes(fig, **kw):
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor="rgba(20,33,61,0.25)",
                     tickfont=dict(color=AXIS, size=11), **kw)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor="rgba(20,33,61,0.25)",
                     tickfont=dict(color=AXIS, size=11))
    return fig


def s11_vswr_fig(f, c, v, fr=None, bw=None, title="Predicted Response"):
    """S11 and VSWR on a shared frequency axis, with the -10 dB band shaded."""
    f = np.asarray(f, dtype=float)
    c = np.asarray(c, dtype=float)
    v = np.asarray(v, dtype=float)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # -10 dB matching band
    in_band = c <= -10.0
    if np.any(in_band):
        fig.add_trace(go.Scatter(
            x=f, y=np.where(in_band, c, np.nan),
            mode="lines", line=dict(color=GOOD, width=0),
            fill="tozeroy", fillcolor="rgba(99,102,241,0.16)",
            name="matched (&le; -10 dB)", hoverinfo="skip", showlegend=True,
        ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=f, y=c, name="S11 (dB)", mode="lines",
        line=dict(color=S11_COLOR, width=2.6),
        hovertemplate="%{x:.3f} GHz<br>S11 = %{y:.2f} dB<extra></extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=f, y=v, name="VSWR", mode="lines",
        line=dict(color=VSWR_COLOR, width=2.2, dash="dot"),
        hovertemplate="%{x:.3f} GHz<br>VSWR = %{y:.3f}<extra></extra>",
    ), secondary_y=True)

    fig.add_hline(y=-10, line=dict(color=DANGER, width=1.4, dash="dash"),
                  annotation_text="-10 dB", annotation_position="bottom right",
                  annotation_font=dict(color=DANGER, size=11), secondary_y=False)
    fig.add_hline(y=2, line=dict(color=DANGER, width=1.2, dash="dash"),
                  annotation_text="VSWR 2", annotation_position="top right",
                  annotation_font=dict(color=DANGER, size=11), secondary_y=True)

    if fr is not None and np.isfinite(fr):
        i = int(np.argmin(c))
        fig.add_vline(x=fr, line=dict(color=ACCENT, width=1.6),
                      annotation_text=f"fr {fr:.3f} GHz",
                      annotation_position="top left",
                      annotation_font=dict(color=ACCENT, size=11))
        fig.add_trace(go.Scatter(
            x=[f[i]], y=[c[i]], mode="markers", name="resonance",
            marker=dict(color=ACCENT, size=11, line=dict(color="#6366F1", width=2.4)),
            hovertemplate=f"fr = {fr:.4f} GHz<br>S11min = {c[i]:.2f} dB<extra></extra>",
        ), secondary_y=False)
        if bw and np.isfinite(bw) and bw > 0:
            fig.add_vrect(x0=fr - bw / 2, x1=fr + bw / 2,
                          fillcolor="rgba(129,140,248,0.08)", line_width=0, layer="below")

    fig.update_layout(title=dict(text=title, font=dict(size=14, color=TEXT), x=0.01))
    fig.update_xaxes(title_text="Frequency (GHz)")
    fig.update_yaxes(title_text="S11 (dB)", secondary_y=False)
    fig.update_yaxes(title_text="VSWR", secondary_y=True, range=[1, 6])
    return _axes(_style(fig, height=440))


def compare_fig(entries):
    """Overlay several designs' S11 curves. entries: list of dicts with
    keys label, f, c, and optionally fr."""
    fig = go.Figure()
    for i, e in enumerate(entries):
        col = SERIES[i % len(SERIES)]
        fig.add_trace(go.Scatter(
            x=np.asarray(e["f"], dtype=float), y=np.asarray(e["c"], dtype=float),
            mode="lines", name=str(e["label"]),
            line=dict(color=col, width=2.2),
            hovertemplate="%{x:.3f} GHz<br>S11 = %{y:.2f} dB<extra>" + str(e["label"]) + "</extra>",
        ))
    fig.add_hline(y=-10, line=dict(color=DANGER, width=1.3, dash="dash"),
                  annotation_text="-10 dB", annotation_font=dict(color=DANGER, size=11))
    fig.update_layout(title=dict(text="Design Comparison — S11", font=dict(size=14, color=TEXT), x=0.01))
    fig.update_xaxes(title_text="Frequency (GHz)")
    fig.update_yaxes(title_text="S11 (dB)")
    return _axes(_style(fig, height=430))


def design_space_fig(db, shape_id, shape_label=""):
    """Resonant frequency across the (Lp, Wp) design space for one shape.

    Built straight from the CST `fr (GHz)` column -- no model calls, so it is instant.
    Shows a user where the design space puts their target frequency before they commit
    to a geometry, which is the question the inverse solver answers one point at a time.
    """
    sub = db[db["Antenna_ID"] == shape_id]
    if sub.empty or "fr (GHz)" not in sub.columns:
        return None
    piv = sub.pivot_table(index="Wp", columns="Lp", values="fr (GHz)", aggfunc="mean")
    if piv.empty:
        return None
    fig = go.Figure(go.Heatmap(
        z=piv.to_numpy(dtype=float),
        x=[float(v) for v in piv.columns],
        y=[float(v) for v in piv.index],
        colorscale=[[0, "#F5F2EA"], [0.35, "#C7C9F5"], [0.7, "#6366F1"], [1, "#14213D"]],
        colorbar=dict(title=dict(text="fr (GHz)", font=dict(color=AXIS, size=11)),
                      tickfont=dict(color=AXIS, size=10), thickness=13, len=0.85),
        hovertemplate="Lp = %{x:.2f} mm<br>Wp = %{y:.2f} mm<br>fr = %{z:.3f} GHz<extra></extra>",
        connectgaps=True,
    ))
    fig.update_layout(title=dict(
        text=f"Design Space — resonant frequency{(' · ' + shape_label) if shape_label else ''}",
        font=dict(size=14, color=TEXT), x=0.01))
    fig.update_xaxes(title_text="Patch length Lp (mm)")
    fig.update_yaxes(title_text="Patch width Wp (mm)")
    return _axes(_style(fig, height=430))


def error_scatter_fig(true_vals, pred_vals, xlabel="CST (truth)", ylabel="Predicted",
                      title="Prediction vs. ground truth", unit=""):
    """Parity plot for the validation panel. Points on the diagonal are perfect."""
    t = np.asarray(true_vals, dtype=float)
    p = np.asarray(pred_vals, dtype=float)
    m = np.isfinite(t) & np.isfinite(p)
    t, p = t[m], p[m]
    if t.size < 2:
        return None
    lo = float(min(t.min(), p.min()))
    hi = float(max(t.max(), p.max()))
    pad = (hi - lo) * 0.05 or 1.0
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[lo - pad, hi + pad], y=[lo - pad, hi + pad], mode="lines",
        line=dict(color="#5B6478", width=1.4, dash="dash"), name="perfect", showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=t, y=p, mode="markers", name="held-out points",
        marker=dict(color=S11_COLOR, size=7, opacity=0.75,
                    line=dict(color="rgba(20,33,61,0.3)", width=0.6)),
        hovertemplate=f"truth %{{x:.3f}}{unit}<br>pred %{{y:.3f}}{unit}<extra></extra>",
    ))
    fig.update_layout(title=dict(text=title, font=dict(size=14, color=TEXT), x=0.01))
    fig.update_xaxes(title_text=xlabel, range=[lo - pad, hi + pad])
    fig.update_yaxes(title_text=ylabel, range=[lo - pad, hi + pad])
    return _axes(_style(fig, height=400))


# ---------------------------------------------------------------------------
# 3D structure view
# ---------------------------------------------------------------------------
SUBSTRATE_H = 1.6      # mm, typical FR-4 thickness
COPPER = "#6366F1"        # patch / feed conductor
GROUND = "#8B8DF7"        # CPW ground planes
FR4 = "#EFEAD9"           # substrate (charcoal)


def _box_mesh(w, l, h, color, opacity=0.55, name=""):
    """Triangulated box centred on x, spanning y in [0, l], z in [-h, 0]."""
    x = [-w / 2, w / 2, w / 2, -w / 2, -w / 2, w / 2, w / 2, -w / 2]
    y = [0, 0, l, l, 0, 0, l, l]
    z = [-h, -h, -h, -h, 0, 0, 0, 0]
    i = [0, 0, 4, 4, 1, 1, 2, 2, 3, 3, 4, 5]
    j = [1, 3, 5, 7, 2, 5, 6, 7, 0, 7, 6, 2]
    k = [2, 7, 6, 6, 6, 6, 5, 4, 4, 6, 2, 3]
    return go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=opacity,
                     name=name, flatshading=True, hoverinfo="skip", showlegend=False)


def _flat_mesh(poly, z, color, name="", opacity=1.0):
    """Fan-triangulate a 2D polygon and place it flat at height z."""
    p = np.asarray(poly, dtype=float)
    if len(p) < 3:
        return None
    n = len(p)
    i = [0] * (n - 2)
    j = list(range(1, n - 1))
    k = list(range(2, n))
    return go.Mesh3d(x=p[:, 0], y=p[:, 1], z=[z] * n, i=i, j=j, k=k,
                     color=color, opacity=opacity, name=name, flatshading=True,
                     hoverinfo="skip", showlegend=False)


def patch_3d_fig(antenna_id, lp, wp, shape_label=""):
    """The physical CPW structure: an FR-4 slab with the copper pattern on its top
    face. CPW is a planar technology -- ground, feed and patch all sit in the same
    plane -- so the third dimension is the substrate thickness and the viewing angle,
    which is what makes the layering and the feed gap legible."""
    from antenna_viz import patch_polygons
    g = patch_polygons(antenna_id, lp, wp)
    sw, sl = g["substrate"]

    fig = go.Figure()
    fig.add_trace(_box_mesh(sw, sl, SUBSTRATE_H, FR4, opacity=0.9, name="FR-4 substrate"))
    for poly in g["grounds"]:
        m = _flat_mesh(poly, 0.0, GROUND, "CPW ground")
        if m: fig.add_trace(m)
    m = _flat_mesh(g["feed"], 0.0, COPPER, "feed line")
    if m: fig.add_trace(m)
    for poly in g["patch"]:
        m = _flat_mesh(poly, 0.0, COPPER, "patch")
        if m: fig.add_trace(m)

    # Lp / Wp dimension markers floating above the patch
    lf = 15.0
    fig.add_trace(go.Scatter3d(
        x=[-wp / 2 - 6, -wp / 2 - 6], y=[lf, lf + lp], z=[3, 3],
        mode="lines+text", line=dict(color=ACCENT, width=5),
        text=[None, f"Lp {lp:.2f} mm"], textposition="top center",
        textfont=dict(color=ACCENT, size=12), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter3d(
        x=[-wp / 2, wp / 2], y=[lf + lp + 5, lf + lp + 5], z=[3, 3],
        mode="lines+text", line=dict(color=ACCENT, width=5),
        text=[None, f"Wp {wp:.2f} mm"], textposition="top center",
        textfont=dict(color=ACCENT, size=12), hoverinfo="skip", showlegend=False))

    fig.update_layout(
        paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(family="Inter, system-ui, sans-serif", color=TEXT),
        margin=dict(l=0, r=0, t=48, b=0), height=470,
        title=dict(text=f"CPW structure{(' — ' + shape_label) if shape_label else ''}",
                   font=dict(size=14, color=TEXT), x=0.01),
        scene=dict(
            xaxis=dict(title="x (mm)", color=AXIS, gridcolor=GRID, backgroundcolor="rgba(0,0,0,0)",
                       showbackground=False, tickfont=dict(size=10, color=AXIS)),
            yaxis=dict(title="y (mm)", color=AXIS, gridcolor=GRID, backgroundcolor="rgba(0,0,0,0)",
                       showbackground=False, tickfont=dict(size=10, color=AXIS)),
            zaxis=dict(title="z (mm)", color=AXIS, gridcolor=GRID, backgroundcolor="rgba(0,0,0,0)",
                       showbackground=False, tickfont=dict(size=10, color=AXIS)),
            aspectmode="manual", aspectratio=dict(x=1.1, y=1.3, z=0.45),
            camera=dict(eye=dict(x=1.5, y=-1.7, z=0.85)),
        ),
    )

    # Slow orbit: press "Orbit" to start, "Pause" to stop (user-initiated, never autoplays).
    r0, z0 = float(np.hypot(1.5, -1.7)), 0.85
    a0 = float(np.arctan2(-1.7, 1.5))
    fig.frames = [go.Frame(layout=dict(scene_camera=dict(eye=dict(
        x=r0 * float(np.cos(a0 + 2 * np.pi * k / 90)), y=r0 * float(np.sin(a0 + 2 * np.pi * k / 90)), z=z0))))
        for k in range(90)]
    fig.update_layout(updatemenus=[dict(
        type="buttons", showactive=False, x=0.02, y=0.04, xanchor="left", yanchor="bottom",
        bgcolor="rgba(17,22,36,0.9)", bordercolor="#6366F1", font=dict(color=TEXT, size=12),
        buttons=[
            dict(label="Orbit", method="animate", args=[None, dict(
                frame=dict(duration=45, redraw=True), transition=dict(duration=0),
                fromcurrent=True, mode="immediate")]),
            dict(label="Pause", method="animate", args=[[None], dict(
                frame=dict(duration=0, redraw=False), transition=dict(duration=0), mode="immediate")]),
        ])])
    return _style(fig, height=520)


# ---------------------------------------------------------------------------
# Animated S11 / VSWR chart (HTML + SVG, no extra dependencies)
#
# Drop-in alternative to s11_vswr_fig for the forward-design result:
#     import streamlit.components.v1 as components
#     components.html(s11_vswr_animated_html(f, c, v, fr, bw), height=560)
# It plots ONLY the arrays passed in (the engine's real output). Everything shown
# (S11 minimum, the -10 dB band edges, hover values) is read from those arrays.
# Motion: grid + axes fade in, both curves draw themselves left to right, the matched
# band wipes in, the resonance marker pops and pulses, and hovering gives a synced
# crosshair + tooltip on both panels. "Replay" restarts the sequence.
# ---------------------------------------------------------------------------
_AD_CHART_TEMPLATE = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{margin:0;height:100%;background:transparent;font-family:Inter,system-ui,sans-serif;color:#14213D}
.card{position:relative;height:100%;border:1px solid rgba(20,33,61,.14);border-radius:20px;background:#FFFDF8;overflow:hidden}
.hd{position:absolute;left:18px;right:16px;top:12px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;z-index:2}
.hd h3{margin:0 auto 0 0;font:500 16px Fraunces,Georgia,serif}
.chip{font-size:12px;color:#5B6478;border:1px solid rgba(20,33,61,.18);border-radius:999px;padding:5px 11px;background:rgba(255,255,255,.8)}.chip b{color:#14213D;font-weight:600}
.rp{background:rgba(20,33,61,.04);color:#14213D;border:1px solid rgba(20,33,61,.18);border-radius:999px;padding:6px 12px;font:12px Inter;cursor:pointer}.rp:hover{border-color:#6366F1}
svg{position:absolute;inset:0;width:100%;height:100%}
.tip{position:absolute;pointer-events:none;background:#FFFFFF;border:1px solid #6366F1;border-radius:10px;padding:8px 10px;font-size:12px;line-height:1.5;opacity:0;transition:opacity .15s;z-index:3;white-space:nowrap}
.fi{opacity:0;animation:fi .8s forwards}.dr{stroke-dasharray:1;stroke-dashoffset:1;animation:dr 1.8s cubic-bezier(.3,.6,.3,1) forwards}
.wipe{transform-box:fill-box;transform-origin:left center;transform:scaleX(0);animation:wp 1.1s cubic-bezier(.3,.6,.3,1) forwards}
.pop{transform-box:fill-box;transform-origin:center;transform:scale(0);animation:pp .5s cubic-bezier(.3,1.6,.5,1) forwards}
.pulse{transform-box:fill-box;transform-origin:center;opacity:0;animation:pl 2.2s ease-out infinite}
@keyframes fi{to{opacity:1}}@keyframes dr{to{stroke-dashoffset:0}}@keyframes wp{to{transform:scaleX(1)}}@keyframes pp{to{transform:scale(1)}}@keyframes pl{0%{opacity:.7;transform:scale(1)}100%{opacity:0;transform:scale(4)}}
.rm *{animation-duration:.01ms!important;animation-delay:0s!important;animation-iteration-count:1!important}.rm .pulse{display:none}
text{font-family:Inter,sans-serif}
</style></head><body><div class="card" id="cd"><div class="hd"><h3>__TITLE__</h3><span class="chip" id="c1"></span><span class="chip" id="c2"></span><span class="chip" id="c3"></span><button class="rp" id="rp" aria-label="Replay animation">&#8635; Replay</button></div>
<svg id="sv" role="img" aria-label="__TITLE__: S11 and VSWR versus frequency"></svg><div class="tip" id="tp"></div></div>
<script>
const D=__DATA__;const NS='http://www.w3.org/2000/svg';
const rm=matchMedia('(prefers-reduced-motion: reduce)').matches;if(rm)document.getElementById('cd').classList.add('rm');
const sv=document.getElementById('sv'),tp=document.getElementById('tp'),cd=document.getElementById('cd');
const E=(n,a,p)=>{const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);(p||sv).appendChild(e);return e};
const f=D.f,c=D.c,v=D.v,N=f.length;let imin=0;for(let i=1;i<N;i++)if(c[i]<c[imin])imin=i;
let lo=imin,hi=imin;const hasBand=c[imin]<=-10;
if(hasBand){while(lo>0&&c[lo-1]<=-10)lo--;while(hi<N-1&&c[hi+1]<=-10)hi++}
const edge=(i,j)=>{const a=c[i],b=c[j];return b===a?f[i]:f[i]+(f[j]-f[i])*((-10-a)/(b-a))};
const fl=hasBand?(lo>0?edge(lo-1,lo):f[lo]):null,fh=hasBand?(hi<N-1?edge(hi,hi+1):f[hi]):null;
const bwv=D.bw!=null?D.bw:(hasBand?(fh-fl):null);
document.getElementById('c1').innerHTML='fr <b>'+(D.fr!=null?D.fr:f[imin]).toFixed(3)+' GHz</b>';
document.getElementById('c2').innerHTML='S11 min <b>'+c[imin].toFixed(2)+' dB</b>';
document.getElementById('c3').innerHTML=bwv!=null?'-10 dB band <b>'+(bwv*1000).toFixed(0)+' MHz</b>':'no -10 dB band';
function draw(){
 sv.innerHTML='';const W=cd.clientWidth,H=cd.clientHeight;sv.setAttribute('viewBox','0 0 '+W+' '+H);
 const L=56,R=22,T=document.querySelector('.hd').offsetHeight+24,B=48,gap=26,pw=W-L-R,ph1=Math.round((H-T-B-gap)*.64),ph2=H-T-B-gap-ph1,y2=T+ph1+gap;
 const f0=f[0],f1=f[N-1],X=x=>L+(x-f0)/(f1-f0)*pw;
 const cmin=Math.min(...c),ylo=Math.floor((cmin-3)/5)*5,yhi=0,Y1=y=>T+(yhi-y)/(yhi-ylo)*ph1;
 const Y2=y=>y2+(6-y)/5*ph2;
 const defs=E('defs',{});const cp=E('clipPath',{id:'cp'},defs);E('rect',{x:L,y:y2,width:pw,height:ph2},cp);
 const g=E('g',{class:'fi'});
 for(let x=Math.ceil(f0);x<=f1;x++){E('path',{d:'M'+X(x)+' '+T+'V'+(y2+ph2),stroke:'rgba(20,33,61,.08)','stroke-width':1},g);const t=E('text',{x:X(x),y:H-28,fill:'#5B6478','font-size':11,'text-anchor':'middle'},g);t.textContent=x}
 for(let y=ylo;y<=yhi;y+=5){E('path',{d:'M'+L+' '+Y1(y)+'H'+(L+pw),stroke:'rgba(20,33,61,.08)'},g);const t=E('text',{x:L-8,y:Y1(y)+4,fill:'#5B6478','font-size':11,'text-anchor':'end'},g);t.textContent=y}
 for(let y=1;y<=6;y++){E('path',{d:'M'+L+' '+Y2(y)+'H'+(L+pw),stroke:'rgba(20,33,61,.08)'},g);const t=E('text',{x:L-8,y:Y2(y)+4,fill:'#5B6478','font-size':11,'text-anchor':'end'},g);t.textContent=y}
 [['S11 (dB)',T+ph1/2],['VSWR',y2+ph2/2]].forEach(a=>{const t=E('text',{x:14,y:a[1],fill:'#5B6478','font-size':11,'text-anchor':'middle',transform:'rotate(-90 14 '+a[1]+')'},g);t.textContent=a[0]});
 const xt=E('text',{x:L+pw/2,y:H-10,fill:'#5B6478','font-size':11,'text-anchor':'middle'},g);xt.textContent='Frequency (GHz)';
 if(hasBand){const bx=X(fl),bw=X(fh)-X(fl);[[T,ph1],[y2,ph2]].forEach(a=>E('rect',{class:'wipe',x:bx,y:a[0],width:bw,height:a[1],fill:'rgba(99,102,241,.12)',style:'animation-delay:1.3s'}))}
 const th=E('g',{class:'fi',style:'animation-delay:1.2s'});
 E('path',{d:'M'+L+' '+Y1(-10)+'H'+(L+pw),stroke:'rgba(20,33,61,.55)','stroke-dasharray':'6 4'},th);
 let t=E('text',{x:L+pw-4,y:Y1(-10)-5,fill:'rgba(20,33,61,.7)','font-size':11,'text-anchor':'end'},th);t.textContent='-10 dB';
 E('path',{d:'M'+L+' '+Y2(2)+'H'+(L+pw),stroke:'rgba(20,33,61,.55)','stroke-dasharray':'2 4'},th);
 t=E('text',{x:L+pw-4,y:Y2(2)-5,fill:'rgba(20,33,61,.7)','font-size':11,'text-anchor':'end'},th);t.textContent='VSWR = 2';
 const path=(arr,Y)=>arr.map((q,i)=>(i?'L':'M')+X(f[i]).toFixed(1)+' '+Y(q).toFixed(1)).join('');
 E('path',{d:path(c,Y1),pathLength:1,class:'dr',fill:'none',stroke:'#4F46E5','stroke-width':2.6,'stroke-linejoin':'round',style:'filter:drop-shadow(0 0 6px rgba(99,102,241,.6))'});
 E('path',{d:path(v,Y2),pathLength:1,class:'dr',fill:'none',stroke:'#14213D','stroke-width':2.2,'clip-path':'url(#cp)',style:'animation-delay:.25s'});
 const mx=X(f[imin]),my=Y1(c[imin]);
 const m=E('g',{class:'fi',style:'animation-delay:1.9s'});
 E('path',{d:'M'+mx+' '+T+'V'+(y2+ph2),stroke:'rgba(20,33,61,.3)','stroke-dasharray':'3 4'},m);
 E('circle',{class:'pulse',cx:mx,cy:my,r:6,fill:'none',stroke:'#4F46E5','stroke-width':1.5,style:'animation-delay:2.2s'},m);
 E('circle',{class:'pop',cx:mx,cy:my,r:6,fill:'#14213D',stroke:'#6366F1','stroke-width':2.4,style:'animation-delay:1.9s'},m);
 const lab=E('text',{x:Math.min(mx+12,W-150),y:my-12,fill:'#14213D','font-size':12,'font-weight':600},m);lab.textContent='fr '+(D.fr!=null?D.fr:f[imin]).toFixed(3)+' GHz · '+c[imin].toFixed(1)+' dB';
 const cr=E('path',{stroke:'rgba(20,33,61,.4)',opacity:0},sv),d1=E('circle',{r:4.5,fill:'#4F46E5',stroke:'#fff',opacity:0},sv),d2=E('circle',{r:4.5,fill:'#14213D',stroke:'#fff',opacity:0},sv);
 const ov=E('rect',{x:L,y:T,width:pw,height:H-T-B,fill:'transparent'},sv);
 ov.addEventListener('pointermove',e=>{const r=sv.getBoundingClientRect(),px=e.clientX-r.left,i=Math.max(0,Math.min(N-1,Math.round((px-L)/pw*(N-1))));
  const x=X(f[i]);cr.setAttribute('d','M'+x+' '+T+'V'+(y2+ph2));cr.setAttribute('opacity',1);d1.setAttribute('cx',x);d1.setAttribute('cy',Y1(c[i]));d1.setAttribute('opacity',1);
  d2.setAttribute('cx',x);d2.setAttribute('cy',Y2(Math.min(v[i],6)));d2.setAttribute('opacity',1);
  tp.innerHTML='<b>'+f[i].toFixed(3)+' GHz</b><br>S11 '+c[i].toFixed(2)+' dB<br>VSWR '+v[i].toFixed(3);tp.style.opacity=1;
  tp.style.left=Math.min(x+14,W-130)+'px';tp.style.top=(T+10)+'px'});
 ov.addEventListener('pointerleave',()=>{tp.style.opacity=0;cr.setAttribute('opacity',0);d1.setAttribute('opacity',0);d2.setAttribute('opacity',0)});
}
draw();document.getElementById('rp').onclick=draw;let rt;addEventListener('resize',()=>{clearTimeout(rt);rt=setTimeout(draw,150)});
</script></body></html>"""


def s11_vswr_animated_html(f, c, v, fr=None, bw=None, title="Predicted Response"):
    """Animated S11 + VSWR chart as a self-contained HTML string (see block comment above)."""
    import json
    f = np.asarray(f, dtype=float); c = np.asarray(c, dtype=float); v = np.asarray(v, dtype=float)
    ok = np.isfinite(f) & np.isfinite(c) & np.isfinite(v)
    f, c, v = f[ok], c[ok], v[ok]
    data = dict(f=np.round(f, 5).tolist(), c=np.round(c, 4).tolist(), v=np.round(v, 4).tolist(),
                fr=None if fr is None or not np.isfinite(fr) else float(fr),
                bw=None if bw is None or not np.isfinite(bw) or bw <= 0 else float(bw))
    safe_title = str(title).replace("<", "").replace(">", "").replace('"', "'")
    return (_AD_CHART_TEMPLATE.replace("__DATA__", json.dumps(data)).replace("__TITLE__", safe_title))

````
