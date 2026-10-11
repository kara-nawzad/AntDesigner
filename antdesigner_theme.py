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
