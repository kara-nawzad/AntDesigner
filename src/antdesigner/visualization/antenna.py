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
# vertex comes from the real design. Use it from the application with:
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
<div class="stage" id="st"><svg id="s" viewBox="0 0 480 560" role="img" aria-label="{title}: patch length {lp} mm, patch width {wp} mm">
<g class="grid">{grid}</g><g>{rings}</g>{sub}{grounds}{feed}{patch}<path class="flow" pathLength="1" d="{flow}"/>{dims}</svg></div>
<div class="ill">Rings are illustrative, not a field simulation</div></div>
<script>
const rm=matchMedia('(prefers-reduced-motion: reduce)').matches;
function count(){{document.querySelectorAll('.cnt').forEach(e=>{{const v=+e.dataset.v,t0=performance.now()+(rm?-9999:2900);
(function f(n){{const k=Math.min(Math.max((n-t0)/900,0),1),q=1-Math.pow(1-k,3);e.textContent=(v*q).toFixed(2);if(k<1)requestAnimationFrame(f)}})(performance.now())}})}}
count();
const st=document.getElementById('st');
if(!rm&&matchMedia('(pointer:fine)').matches)document.getElementById('c').addEventListener('pointermove',e=>{{const r=e.currentTarget.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;st.style.transform='rotateY('+(x*14)+'deg) rotateX('+(-y*10)+'deg)'}});
document.getElementById('c').addEventListener('pointerleave',()=>st.style.transform='');
</script></body></html>'''
