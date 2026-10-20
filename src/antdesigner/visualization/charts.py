"""
Interactive Plotly charts for the antenna synthesis app.

Replaces the static matplotlib PNGs in the forward-design section. The numbers come
from the engine unchanged -- this module only renders them. Plotly figures are
vector/SVG in the browser, so they cost far less bandwidth than the base64 raster
PNGs the old interface was pushing on every rerun, and they give hover readouts of the exact
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
    from antdesigner.visualization.antenna import patch_polygons
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
