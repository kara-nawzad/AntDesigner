(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const TAB_IDS = ['home', 'fwd', 'inv', 'hertz', 'meth'];
  const ENGINE_DEPENDENT_SELECTORS = ['#fwd-run', '#inv-run', '#self-test-run', '#ab-test-run', '#inverse-test-run', '#healthcheck-run', '#data-story-load'];
  const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const state = {
    activeTab: 'home',
    meta: null,
    health: null,
    forward: null,
    inverse: null,
    comparison: [],
    hertzMessages: [{ role: 'assistant', content: "Hi, I'm Hertz. Ask me about antenna design, parameters, or your results." }],
    hertzModel: null,
    designSpaceLoadedFor: null,
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function formatNumber(value, digits = 2, suffix = '') {
    const number = Number(value);
    return Number.isFinite(number) ? `${number.toFixed(digits)}${suffix}` : 'n/a';
  }

  function formatBooleanLoaded(value) {
    return value ? 'loaded' : 'missing';
  }

  async function api(path, options = {}) {
    const request = { ...options, headers: { ...(options.headers || {}) } };
    if (request.body && typeof request.body !== 'string') {
      request.headers['Content-Type'] = 'application/json';
      request.body = JSON.stringify(request.body);
    }
    let response;
    try {
      response = await fetch(path, request);
    } catch (_) {
      throw new Error('The server could not be reached. Please retry.');
    }

    const contentType = response.headers.get('content-type') || '';
    const payload = contentType.includes('application/json') ? await response.json() : null;
    if (!response.ok) {
      throw new Error(payload?.detail || 'The server could not complete that request.');
    }
    return payload;
  }

  function setButtonBusy(button, busy, label) {
    if (!button) return;
    if (busy) {
      button.dataset.label = button.innerHTML;
      button.dataset.busy = 'true';
      button.disabled = true;
      button.innerHTML = `${escapeHtml(label || 'Working…')}`;
    } else {
      const needsEngine = ENGINE_DEPENDENT_SELECTORS.some((selector) => button.matches(selector));
      button.disabled = needsEngine && !state.health?.engine_ready;
      button.innerHTML = button.dataset.label || button.innerHTML;
      delete button.dataset.label;
      delete button.dataset.busy;
    }
  }

  function showNotice(target, message, kind = 'info') {
    if (!target) return;
    if (!message) {
      target.innerHTML = '';
      return;
    }
    target.innerHTML = `<div class="notice ${kind}">${message}</div>`;
  }

  function setEngineBanner(message, isError = false) {
    const banner = $('#engine-banner');
    if (!message) {
      banner.hidden = true;
      banner.textContent = '';
      banner.classList.remove('error');
      return;
    }
    banner.hidden = false;
    banner.textContent = message;
    banner.classList.toggle('error', isError);
  }

  function updateIndicator() {
    const tabList = $('#tb');
    const active = $('.tab[aria-selected="true"]');
    const indicator = $('#ind');
    if (!tabList || !active || !indicator) return;
    indicator.style.left = `${active.offsetLeft}px`;
    indicator.style.width = `${active.offsetWidth}px`;
  }

  function tabFromHash() {
    const requested = window.location.hash.replace('#', '').trim();
    // Legacy hash redirect: #aeth -> #hertz
    if (requested === 'aeth') {
      if (history.replaceState) history.replaceState(null, '', '#hertz');
      else window.location.hash = 'hertz';
      return 'hertz';
    }
    return TAB_IDS.includes(requested) ? requested : 'home';
  }

  function activateTab(tabId, { scroll = true, updateHash = false } = {}) {
    const id = TAB_IDS.includes(tabId) ? tabId : 'home';
    state.activeTab = id;
    $$('.pane').forEach((pane) => {
      const selected = pane.id === id;
      pane.hidden = !selected;
      pane.classList.toggle('on', selected);
    });
    $$('.tab').forEach((tab) => {
      const selected = tab.dataset.tab === id;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });
    requestAnimationFrame(updateIndicator);
    if (scroll) window.scrollTo({ top: 0, behavior: REDUCED_MOTION ? 'auto' : 'smooth' });
    if (updateHash && window.location.hash !== `#${id}`) window.location.hash = id;
    if (id === 'home') observeRevealElements();
  }

  function bindTabs() {
    $$('.tab').forEach((button) => {
      button.addEventListener('click', () => activateTab(button.dataset.tab, { updateHash: true }));
      button.addEventListener('keydown', (event) => {
        const index = $$('.tab').indexOf(button);
        let nextIndex = null;
        if (event.key === 'ArrowRight') nextIndex = (index + 1) % TAB_IDS.length;
        if (event.key === 'ArrowLeft') nextIndex = (index - 1 + TAB_IDS.length) % TAB_IDS.length;
        if (event.key === 'Home') nextIndex = 0;
        if (event.key === 'End') nextIndex = TAB_IDS.length - 1;
        if (nextIndex !== null) {
          event.preventDefault();
          const next = $$('.tab')[nextIndex];
          next.focus();
          activateTab(next.dataset.tab, { updateHash: true });
        }
      });
    });
    $$('.go').forEach((button) => button.addEventListener('click', () => activateTab(button.dataset.go, { updateHash: true })));
    window.addEventListener('hashchange', () => activateTab(tabFromHash(), { scroll: false }));
    window.addEventListener('resize', updateIndicator, { passive: true });
    document.fonts?.ready?.then(updateIndicator);
    activateTab(tabFromHash(), { scroll: false });
  }

  let revealObserver;
  function observeRevealElements() {
    if (REDUCED_MOTION) {
      $$('.rv').forEach((element) => element.classList.add('in'));
      return;
    }
    if (!revealObserver) {
      revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in');
            revealObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15 });
    }
    $$('.rv:not(.in)').forEach((element) => revealObserver.observe(element));
  }

  function bindHeroParallax() {
    if (REDUCED_MOTION || !window.matchMedia('(pointer:fine)').matches) return;
    document.addEventListener('pointermove', (event) => {
      const x = event.clientX / window.innerWidth - 0.5;
      $$('.rl').forEach((ridge, index) => {
        ridge.parentNode.style.transform = `translateX(${x * -14 * (index + 1)}px)`;
      });
    }, { passive: true });
  }

  function setMetric(id, value, digits, suffix) {
    const element = $(`#${id}`);
    const target = Number(value);
    if (!element) return;
    if (!Number.isFinite(target)) {
      element.textContent = 'n/a';
      return;
    }
    const render = (number) => { element.textContent = `${number.toFixed(digits)}${suffix}`; };
    if (REDUCED_MOTION) {
      render(target);
      return;
    }
    const start = performance.now();
    const duration = 850;
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      render(target * eased);
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  function selectedShape() {
    const id = Number($('#fwd-shape').value);
    return state.meta?.shapes?.find((shape) => shape.id === id) || null;
  }

  function shapeLabel(shapeId) {
    return state.meta?.shapes?.find((shape) => shape.id === Number(shapeId))?.label || `Shape ${shapeId}`;
  }

  function setEngineDependentDisabled(disabled) {
    ENGINE_DEPENDENT_SELECTORS.forEach((selector) => {
      const control = $(selector);
      if (control && !control.dataset.busy) control.disabled = disabled;
    });
  }

  async function refreshHealth() {
    try {
      const health = await api('/health');
      state.health = health;
      $('#engine-rows').textContent = health.engine_ready ? `${Number(health.rows).toLocaleString()} rows` : '—';
      $('#engine-model').textContent = health.engine_ready ? formatBooleanLoaded(health.model_loaded) : 'warming';
      $('#engine-specialist').textContent = health.engine_ready ? 'CST + main brain' : 'warming';
      $('#engine-blending').textContent = 'aligned';

      const note = $('#engine-method-note');
      if (health.engine_ready) {
        note.textContent = 'The engine is ready (CST interpolation + main Keras surrogate). The dip specialist has been removed — predictions use CST anchoring with the main brain as fallback / neural refinement. Labels report the actual method used.';
        setEngineBanner('');
        setEngineDependentDisabled(false);
      } else if (health.status === 'error') {
        note.textContent = 'The engine could not initialize on this server. Check deployed model, CSV, and scaler assets.';
        setEngineBanner(health.message || 'The antenna engine is unavailable.', true);
        setEngineDependentDisabled(true);
      } else {
        note.textContent = 'The model and CST data are loading in the background. Validation and simulations unlock when ready.';
        setEngineBanner('The antenna engine is warming up. The page is ready; simulations will unlock automatically.');
        setEngineDependentDisabled(true);
      }

      const hertzNotice = $('#hertz-not-configured');
      const form = $('#hertz-form');
      if (!health.hertz_configured) {
        hertzNotice.hidden = false;
        hertzNotice.textContent = 'Set GROQ_API_KEY in the server environment to enable Hertz Assistant.';
        $('textarea', form).disabled = true;
        $('button', form).disabled = true;
      } else {
        hertzNotice.hidden = true;
        $('textarea', form).disabled = false;
        $('button', form).disabled = false;
      }
      return health;
    } catch (_) {
      setEngineBanner('Unable to check engine health. Please refresh or retry.', true);
      setEngineDependentDisabled(true);
      return null;
    }
  }

  async function pollHealthUntilReady() {
    const health = await refreshHealth();
    if (!health || !health.engine_ready) window.setTimeout(pollHealthUntilReady, 2500);
  }

  function populateMeta(meta) {
    state.meta = meta;
    const shapeSelect = $('#fwd-shape');
    shapeSelect.innerHTML = meta.shapes.map((shape) => `<option value="${shape.id}">${escapeHtml(shape.label)}</option>`).join('');
    shapeSelect.value = '1';

    const prioritySelect = $('#inv-priority');
    prioritySelect.innerHTML = meta.priorities.map((priority) => `<option value="${escapeHtml(priority)}">${escapeHtml(priority)}</option>`).join('');
    const familySelect = $('#inv-family');
    familySelect.innerHTML = Object.keys(meta.families).map((family) => `<option value="${escapeHtml(family)}">${escapeHtml(family)}</option>`).join('');

    const range = meta.slider_range_mm;
    ['#fwd-lp-number', '#fwd-lp-range', '#fwd-wp-number', '#fwd-wp-range'].forEach((selector) => {
      const input = $(selector);
      input.min = range.min;
      input.max = range.max;
      input.step = range.step;
    });
    const trained = meta.trained_range_mm;
    $('#fwd-trained-note').innerHTML = `Dimensions are limited to <strong>${range.min}–${range.max} mm</strong>, the range covered by both the CST dataset and trained model. This prevents unsupported extrapolation.`;
    const cstPct = Math.round((1 - meta.ml_blend_weight) * 100);
    const mlPct = Math.round(meta.ml_blend_weight * 100);
    $('#fwd-refine').nextElementSibling.textContent = `Use the trained neural model (${cstPct}/${mlPct} CST / model)`;
    $('#fwd-refine-note').textContent = `On: beyond ${meta.ml_blend_radius_mm} mm from a CST point the answer is ${cstPct}% CST interpolation + ${mlPct}% neural model. Within ${meta.ml_blend_radius_mm} mm the simulated curve is used as-is — it is ground truth, so there is nothing for the model to improve. Re-run Initiate Simulation after changing this. Use Engine Validation → Compare CST vs. model to see which is actually more accurate.`;
  }

  async function loadMeta() {
    const meta = await api('/api/meta');
    populateMeta(meta);
  }

  function clampDimension(value) {
    const range = state.meta?.slider_range_mm || { min: 10, max: 35 };
    const number = Number(value);
    if (!Number.isFinite(number)) return null;
    return Math.max(Number(range.min), Math.min(Number(range.max), number));
  }

  function bindDimensionPair(numberSelector, rangeSelector) {
    const number = $(numberSelector);
    const range = $(rangeSelector);
    const setValue = (value, origin) => {
      const clamped = clampDimension(value);
      if (clamped === null) return;
      const normalized = clamped.toFixed(2);
      if (origin !== number) number.value = normalized;
      if (origin !== range) range.value = normalized;
    };
    range.addEventListener('input', () => setValue(range.value, range));
    number.addEventListener('change', () => setValue(number.value, number));
    number.addEventListener('blur', () => setValue(number.value, number));
  }

  function bindForwardControls() {
    bindDimensionPair('#fwd-lp-number', '#fwd-lp-range');
    bindDimensionPair('#fwd-wp-number', '#fwd-wp-range');
    $('#fwd-run').addEventListener('click', runForward);
    $$('.subtab').forEach((button) => button.addEventListener('click', () => switchForwardVisual(button.dataset.view)));
    $('#compare-add').addEventListener('click', addComparison);
    $('#compare-clear').addEventListener('click', clearComparison);
    $('#report-download').addEventListener('click', downloadForwardReport);
    $('#design-space-load').addEventListener('click', loadDesignSpace);
  }

  async function runForward() {
    const button = $('#fwd-run');
    const lp = clampDimension($('#fwd-lp-number').value);
    const wp = clampDimension($('#fwd-wp-number').value);
    const shapeId = Number($('#fwd-shape').value);
    if (lp === null || wp === null) {
      showNotice($('#fwd-empty'), 'Enter valid Lp and Wp values between 10 and 35 mm.', 'warning');
      return;
    }
    setButtonBusy(button, true, 'Running simulation…');
    try {
      const result = await api('/api/forward', {
        method: 'POST',
        body: { shape_id: shapeId, lp, wp, use_ml_refine: $('#fwd-refine').checked },
      });
      state.forward = result;
      renderForward(result);
      await Promise.all([loadForwardAntenna(result), loadForwardResponse(result)]);
      await renderComparison();
    } catch (error) {
      showNotice($('#fwd-empty'), escapeHtml(error.message), 'warning');
      $('#fwd-empty').hidden = false;
    } finally {
      setButtonBusy(button, false);
    }
  }

  function renderForward(result) {
    $('#fwd-empty').hidden = true;
    $('#fwd-result').hidden = false;
    $('#fwd-status').textContent = `Status: ${result.status || 'n/a'}`;
    $('#fwd-engine').textContent = `Engine mode: ${result.engine || '—'}`;
    setMetric('metric-fr', result.fr, 3, ' GHz');
    setMetric('metric-bw', result.bw, 3, ' GHz');
    setMetric('metric-s11', result.s11, 2, ' dB');
    setMetric('metric-vswr', result.vswr_at_min, 3, '');
    setMetric('metric-gain', result.gain, 2, ' dBi');
    setMetric('metric-eff', Number(result.eff) * 100, 2, ' %');

    if (result.out_of_range) {
      const trained = state.meta.trained_range_mm;
      showNotice($('#fwd-warning'), `<strong>Outside the trained range.</strong> The model and the CST dataset were built from antennas <strong>${trained.min}–${trained.max} mm</strong>. At Lp = ${Number(result.lp).toFixed(2)} mm / Wp = ${Number(result.wp).toFixed(2)} mm the app is <strong>extrapolating</strong> — neither the neural network nor the interpolation has any real data here, so treat these numbers as a trend, not a prediction. Neural networks are especially unreliable outside their training range.`, 'warning');
    } else {
      showNotice($('#fwd-warning'), '');
    }

    const note = result.neural_note;
    if (note === 'active') {
      showNotice($('#fwd-neural'), 'Neural refinement: <strong>active</strong> — CSV anchor blended with the ML surrogate.', 'success');
    } else if (note === 'not_applied_near_cst' && result.near_row) {
      showNotice($('#fwd-neural'), `Neural refinement: <strong>not applied</strong> — geometry is within <strong>${state.meta.ml_blend_radius_mm} mm</strong> of a CST reference point (distance ${Number(result.near_row.dist).toFixed(3)} mm). Result uses CST data only.`, 'info');
    } else if (note === 'not_applied') {
      showNotice($('#fwd-neural'), 'Neural refinement: <strong>not applied</strong> for this run — see engine mode above. Try different Lp/Wp values farther from dataset points to engage the ML layer.', 'info');
    } else {
      showNotice($('#fwd-neural'), 'Neural refinement: <strong>off</strong> — CST physics / anchor path only.', 'info');
    }
    if (result.near_row) {
      const near = result.near_row;
      $('#fwd-anchor').textContent = `Nearest CSV anchor → Lp=${formatNumber(near.lp, 4)}, Wp=${formatNumber(near.wp, 4)}, fr=${formatNumber(near.fr, 3)} GHz, S11min=${formatNumber(near.s11, 2)} dB, dist=${formatNumber(near.dist, 4)} mm`;
    } else {
      $('#fwd-anchor').textContent = '';
    }
    $('#fwd-3d').innerHTML = '';
    delete $('#fwd-3d').dataset.loaded;
    $('#design-space-plot').innerHTML = '';
    state.designSpaceLoadedFor = null;
    switchForwardVisual('layout');
  }

  async function loadForwardAntenna(result) {
    const data = await api('/api/visual/antenna', {
      method: 'POST',
      body: { shape_id: result.shape_id, lp: result.lp, wp: result.wp, label: shapeLabel(result.shape_id) },
    });
    $('#fwd-antenna').srcdoc = data.html;
  }

  async function loadForwardResponse(result) {
    const data = await api('/api/visual/response', {
      method: 'POST',
      body: { f: result.f, c: result.c, v: result.v, fr: result.fr, bw: result.bw, title: 'Predicted Response' },
    });
    $('#fwd-response').srcdoc = data.html;
  }

  async function switchForwardVisual(view) {
    if (!state.forward) return;
    $$('.subtab').forEach((button) => button.classList.toggle('active', button.dataset.view === view));
    $('#fwd-layout-view').hidden = view !== 'layout';
    $('#fwd-structure-view').hidden = view !== 'structure';
    if (view === 'structure' && !$('#fwd-3d').dataset.loaded) {
      const holder = $('#fwd-3d');
      holder.innerHTML = '<div class="job-progress">Loading the real 3D structure…</div>';
      try {
        const data = await api('/api/visual/3d', {
          method: 'POST',
          body: { shape_id: state.forward.shape_id, lp: state.forward.lp, wp: state.forward.wp, label: shapeLabel(state.forward.shape_id) },
        });
        renderPlot(holder, data, 520);
        holder.dataset.loaded = 'true';
      } catch (error) {
        holder.innerHTML = `<div class="notice warning">${escapeHtml(error.message)}</div>`;
      }
    }
  }

  function renderPlot(holder, figure, height = null) {
    if (!holder) return;
    if (!window.Plotly) {
      holder.innerHTML = '<div class="notice warning">Interactive chart assets did not load.</div>';
      return;
    }
    const layout = { ...(figure.layout || {}) };
    if (height) layout.height = height;
    layout.autosize = true;
    window.Plotly.react(holder, figure.data || [], layout, {
      responsive: true,
      displayModeBar: false,
      displaylogo: false,
    });
  }

  async function addComparison() {
    if (!state.forward) return;
    const design = state.forward;
    const label = `${shapeLabel(design.shape_id).split('. ').slice(-1)[0]}  ${Number(design.lp).toFixed(1)}x${Number(design.wp).toFixed(1)} mm`;
    state.comparison = [...state.comparison, { label, f: design.f, c: design.c }].slice(-6);
    await renderComparison();
  }

  async function clearComparison() {
    state.comparison = [];
    await renderComparison();
  }

  async function renderComparison() {
    const clear = $('#compare-clear');
    const note = $('#compare-note');
    const holder = $('#comparison-plot');
    clear.disabled = state.comparison.length === 0;
    if (state.comparison.length < 2) {
      holder.hidden = true;
      holder.innerHTML = '';
      note.textContent = state.comparison.length ? 'Add a second design to overlay the curves.' : 'Add a second design to overlay the curves.';
      return;
    }
    note.textContent = `${state.comparison.length} real design${state.comparison.length === 1 ? '' : 's'} in the comparison set (latest 6 retained).`;
    holder.hidden = false;
    holder.innerHTML = '<div class="job-progress">Drawing comparison…</div>';
    try {
      const figure = await api('/api/visual/compare', { method: 'POST', body: { entries: state.comparison } });
      renderPlot(holder, figure, 430);
    } catch (error) {
      holder.innerHTML = `<div class="notice warning">${escapeHtml(error.message)}</div>`;
    }
  }

  function downloadText(filename, text, mime = 'text/plain') {
    const blob = new Blob([text], { type: `${mime};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function downloadForwardReport() {
    const design = state.forward;
    if (!design) return;
    const label = shapeLabel(design.shape_id);
    const rows = [
      'SPU Neural Antenna Synthesis - design report',
      '='.repeat(46),
      `Shape          : ${label} (id ${Number(design.shape_id)})`,
      `Lp             : ${Number(design.lp).toFixed(3)} mm`,
      `Wp             : ${Number(design.wp).toFixed(3)} mm`,
      `Status         : ${design.status}`,
      `Resonance fr   : ${Number(design.fr).toFixed(4)} GHz`,
      `Bandwidth      : ${Number(design.bw).toFixed(4)} GHz`,
      `S11 min        : ${Number(design.s11).toFixed(3)} dB`,
      `Gain           : ${Number(design.gain).toFixed(3)} dBi`,
      `Efficiency     : ${(Number(design.eff) * 100).toFixed(2)} %`,
      `Engine         : ${design.engine}`,
    ];
    if (design.near_row) {
      const near = design.near_row;
      rows.push(`Nearest CST anchor: Lp=${Number(near.lp).toFixed(4)} mm, Wp=${Number(near.wp).toFixed(4)} mm, fr=${Number(near.fr).toFixed(4)} GHz, dist=${Number(near.dist).toFixed(4)} mm`);
    }
    downloadText(`antenna_${Number(design.shape_id)}_${Number(design.lp).toFixed(1)}x${Number(design.wp).toFixed(1)}.txt`, rows.join('\n'));
  }

  async function loadDesignSpace() {
    if (!state.forward) return;
    const button = $('#design-space-load');
    const holder = $('#design-space-plot');
    if (state.designSpaceLoadedFor === state.forward.shape_id) return;
    setButtonBusy(button, true, 'Loading map…');
    try {
      const figure = await api(`/api/visual/design-space?shape_id=${encodeURIComponent(state.forward.shape_id)}`);
      if (!figure) {
        holder.innerHTML = '<div class="notice info">Not enough CST points for this shape to map the design space.</div>';
      } else {
        renderPlot(holder, figure, 430);
        state.designSpaceLoadedFor = state.forward.shape_id;
      }
    } catch (error) {
      holder.innerHTML = `<div class="notice warning">${escapeHtml(error.message)}</div>`;
    } finally {
      setButtonBusy(button, false);
    }
  }

  function bindDataStory() {
    $('#data-story-load').addEventListener('click', loadDataStory);
  }

  async function loadDataStory() {
    const button = $('#data-story-load');
    const target = $('#data-story-result');
    setButtonBusy(button, true, 'Reading CST data…');
    target.innerHTML = '<div class="job-progress">Preparing data-story charts from the CST dataset…</div>';
    try {
      const story = await api('/api/data-story');
      const scatter = story.scatter || {};
      const histogram = story.histogram || {};
      const edges = histogram.edges || [];
      const counts = histogram.counts || [];
      if (!scatter.lp?.length || edges.length < 2 || !counts.length) {
        throw new Error('The CST data story did not contain usable points.');
      }
      target.innerHTML = '<div id="story-scatter" class="plot-holder" aria-label="CST geometry distribution plot"></div><div id="story-histogram" class="plot-holder" aria-label="CST resonant-frequency histogram"></div>';
      renderPlot($('#story-scatter'), {
        data: [{
          x: scatter.lp, y: scatter.wp, type: 'scattergl', mode: 'markers', name: 'CST sample',
          marker: { size: 6, opacity: .68, color: scatter.fr, colorscale: 'Viridis', colorbar: { title: 'fr (GHz)' } },
          text: (scatter.shape_id || []).map((id) => `Shape ${id}`), hovertemplate: 'Lp %{x:.3f} mm<br>Wp %{y:.3f} mm<br>fr %{marker.color:.3f} GHz<br>%{text}<extra></extra>',
        }],
        layout: { title: { text: `CST geometry samples (${Number(story.rows).toLocaleString()} usable rows)`, x: .02, font: { color: '#14213D', size: 15 } }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', margin: { l: 58, r: 35, t: 54, b: 52 }, xaxis: { title: 'Patch length Lp (mm)', gridcolor: 'rgba(20,33,61,.10)' }, yaxis: { title: 'Patch width Wp (mm)', gridcolor: 'rgba(20,33,61,.10)' } },
      }, 390);
      const centers = counts.map((_count, index) => (Number(edges[index]) + Number(edges[index + 1])) / 2);
      const widths = counts.map((_count, index) => (Number(edges[index + 1]) - Number(edges[index])) * .94);
      renderPlot($('#story-histogram'), {
        data: [{ x: centers, y: counts, type: 'bar', width: widths, marker: { color: '#6366F1', line: { color: '#4F46E5', width: 1 } }, hovertemplate: 'fr %{x:.3f} GHz<br>%{y} CST rows<extra></extra>' }],
        layout: { title: { text: 'Resonant-frequency distribution', x: .02, font: { color: '#14213D', size: 15 } }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', margin: { l: 58, r: 20, t: 54, b: 52 }, xaxis: { title: 'Resonant frequency fr (GHz)', gridcolor: 'rgba(20,33,61,.10)' }, yaxis: { title: 'CST rows', gridcolor: 'rgba(20,33,61,.10)', rangemode: 'tozero' } },
      }, 390);
    } catch (error) {
      target.innerHTML = `<div class="notice warning">${escapeHtml(error.message)}</div>`;
    } finally {
      setButtonBusy(button, false);
    }
  }

  function bindInverseControls() {
    $('#inv-run').addEventListener('click', runInverse);
  }

  async function runInverse() {
    const targetFr = Number($('#inv-target').value);
    if (!Number.isFinite(targetFr) || targetFr < 1 || targetFr > 7) {
      showNotice($('#inv-empty'), 'Target Frequency must be between 1 and 7 GHz.', 'warning');
      return;
    }
    const button = $('#inv-run');
    setButtonBusy(button, true, 'Synthesizing…');
    try {
      const result = await api('/api/inverse', {
        method: 'POST',
        body: { target_fr: targetFr, priority: $('#inv-priority').value, family: $('#inv-family').value },
      });
      state.inverse = result;
      renderInverse(result);
      const visual = await api('/api/visual/antenna', {
        method: 'POST',
        body: { shape_id: result.shape_id, lp: result.lp, wp: result.wp, label: shapeLabel(result.shape_id) },
      });
      $('#inv-antenna').srcdoc = visual.html;
    } catch (error) {
      showNotice($('#inv-empty'), escapeHtml(error.message), 'warning');
      $('#inv-empty').hidden = false;
    } finally {
      setButtonBusy(button, false);
    }
  }

  function renderInverse(result) {
    $('#inv-empty').hidden = true;
    $('#inv-result').hidden = false;
    $('#inv-status').textContent = `Status: ${result.status || '—'}`;
    setMetric('inv-lp', result.lp, 3, ' mm');
    setMetric('inv-wp', result.wp, 3, ' mm');
    setMetric('inv-accuracy', 100 - Number(result.err_pct), 2, ' %');
    $('#inv-priority-result').textContent = result.priority;
    setMetric('inv-gain', result.gain, 2, ' dBi');
    setMetric('inv-bw', result.bw, 3, ' GHz');
    $('#inv-summary').textContent = `${shapeLabel(result.shape_id)} · target ${Number(result.target_fr).toFixed(3)} GHz · predicted ${Number(result.fr).toFixed(3)} GHz · frequency error ${Number(result.err).toFixed(4)} GHz.`;
  }

  function safeMarkdown(text) {
    let safe = escapeHtml(text);
    safe = safe.replace(/`([^`]+)`/g, '<code>$1</code>');
    safe = safe.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    safe = safe.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    return safe.replace(/\n/g, '<br>');
  }

  function renderHertz() {
    const container = $('#hertz-messages');
    if (!state.hertzMessages.length) {
      container.innerHTML = '<div class="chat-empty"><p class="serif">Ask about antenna design, parameters, result interpretation, or the project method.</p></div>';
      return;
    }
    container.innerHTML = state.hertzMessages.map((message) => `<article class="message ${message.role}"><span class="role">${message.role === 'user' ? 'You' : 'HERTZ'}</span><p>${safeMarkdown(message.content)}</p></article>`).join('');
    container.scrollTop = container.scrollHeight;
  }

  function bindHertz() {
    $('#hertz-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!state.health?.hertz_configured) return;
      const input = $('#hertz-input');
      const content = input.value.trim();
      if (!content) return;
      state.hertzMessages.push({ role: 'user', content });
      input.value = '';
      renderHertz();
      const button = $('#hertz-form button');
      setButtonBusy(button, true, 'Thinking…');
      try {
        const response = await api('/api/hertz', {
          method: 'POST',
          body: { messages: state.hertzMessages, preferred_model: state.hertzModel },
        });
        if (response.model) state.hertzModel = response.model;
        state.hertzMessages.push({ role: 'assistant', content: response.reply || 'Hertz did not return a reply.' });
      } catch (error) {
        state.hertzMessages.push({ role: 'assistant', content: `Hertz request failed: ${error.message}` });
      } finally {
        renderHertz();
        setButtonBusy(button, false);
      }
    });
  }

  function tableHtml(rows, columns) {
    if (!rows?.length) return '<div class="notice info">No metrics were produced.</div>';
    const headings = columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join('');
    const body = rows.map((row) => `<tr>${columns.map((column) => `<td>${escapeHtml(column.format ? column.format(row[column.key], row) : row[column.key] ?? '—')}</td>`).join('')}</tr>`).join('');
    return `<div class="data-table-wrap"><table class="data-table"><thead><tr>${headings}</tr></thead><tbody>${body}</tbody></table></div>`;
  }

  function metricCardsHtml(cards) {
    return `<div class="metrics compact-metrics">${cards.map((card) => `<div><span class="lbl">${escapeHtml(card.label)}</span><b class="${card.text ? 'metric-text' : 'mono'}">${escapeHtml(card.value)}</b></div>`).join('')}</div>`;
  }

  async function startValidation(endpoint, payload, resultElement, renderer) {
    resultElement.innerHTML = '<div class="job-progress">Queued for the single-worker validation engine…</div>';
    try {
      const started = await api(endpoint, { method: 'POST', body: payload });
      const job = await pollJob(started.job_id, resultElement);
      if (job.status !== 'completed') {
        resultElement.innerHTML = `<div class="notice warning">${escapeHtml(job.error || 'Validation did not complete.')}</div>`;
        return;
      }
      renderer(job.result, job, resultElement);
    } catch (error) {
      resultElement.innerHTML = `<div class="notice warning">${escapeHtml(error.message)}</div>`;
    }
  }

  async function pollJob(jobId, resultElement) {
    for (;;) {
      const job = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
      if (job.status === 'completed' || job.status === 'failed') return job;
      resultElement.innerHTML = `<div class="job-progress">${job.status === 'running' ? 'Running the real validation path…' : 'Waiting for the validation worker…'}</div>`;
      await new Promise((resolve) => window.setTimeout(resolve, 1000));
    }
  }

  function bindValidation() {
    const selfSlider = $('#self-test-size');
    selfSlider.addEventListener('input', () => { $('#self-test-size-value').textContent = selfSlider.value; });
    $('#self-test-run').addEventListener('click', () => startValidation('/api/validate/self-test', { sample_size: Number(selfSlider.value) }, $('#self-test-result'), renderSelfTest));
    $('#ab-test-run').addEventListener('click', () => startValidation('/api/validate/ab-test', { sample_size: 150 }, $('#ab-test-result'), renderAbTest));
    const inverseSlider = $('#inverse-test-size');
    inverseSlider.addEventListener('input', () => { $('#inverse-test-size-value').textContent = inverseSlider.value; });
    $('#inverse-test-run').addEventListener('click', () => startValidation('/api/validate/inverse-test', { per_family: Number(inverseSlider.value), fast_mode: $('#inverse-test-mode').value === 'quick' }, $('#inverse-test-result'), renderInverseTest));
    $('#healthcheck-run').addEventListener('click', () => startValidation('/api/validate/healthcheck', {}, $('#healthcheck-result'), renderHealthcheck));
  }

  function renderSelfTest(stats, _job, target) {
    if (!stats) {
      target.innerHTML = '<div class="notice info">Self-test completed but returned no metrics (check CSV frequency columns 1–7 GHz).</div>';
      return;
    }
    const cards = [
      { label: 'Held-out points', value: String(stats.n) },
      { label: 'fr MAE', value: `${formatNumber(stats.fr_mae_mhz, 1)} MHz` },
      { label: 'S11 MAE', value: `${formatNumber(stats.s11_mae_db, 2)} dB` },
      { label: 'BW MAE', value: `${formatNumber(stats.bw_mae_mhz, 1)} MHz` },
      { label: 'fr R²', value: formatNumber(stats.fr?.r2, 3) },
      { label: `fr within ±${Number(stats.fr_tol_pct).toFixed(0)}%`, value: `${formatNumber(stats.fr_pass_pct, 1)}%` },
    ];
    const names = { fr: ['Resonant frequency', 'MHz'], s11: ['S11 minimum', 'dB'], bw: ['Bandwidth', 'MHz'], gain: ['Gain at fr', 'dBi'], eff: ['Radiation efficiency', '%'] };
    const rows = Object.entries(names).filter(([key]) => stats[key]).map(([key, [label, unit]]) => ({ Quantity: label, Unit: unit, MAE: stats[key].mae, P90: stats[key].p90, Max: stats[key].max, 'R²': stats[key].r2, n: stats[key].n }));
    target.innerHTML = `${metricCardsHtml(cards)}<p class="hint">Interpolation modes used: ${Object.entries(stats.anchor_modes || {}).map(([key, count]) => `<code>${escapeHtml(key)}</code> ×${Number(count)}`).join(', ') || 'n/a'}.</p>${tableHtml(rows, [
      { key: 'Quantity', label: 'Quantity' }, { key: 'Unit', label: 'Unit' },
      { key: 'MAE', label: 'MAE', format: (value) => formatNumber(value, 4) }, { key: 'P90', label: 'P90', format: (value) => formatNumber(value, 4) },
      { key: 'Max', label: 'Max', format: (value) => formatNumber(value, 4) }, { key: 'R²', label: 'R²', format: (value) => formatNumber(value, 4) }, { key: 'n', label: 'n' },
    ])}<div id="self-test-scatter" class="plot-holder"></div><p class="hint">Points on the dashed line are exact. Spread above/below it is the interpolation error on geometries the engine has never seen.</p>`;
    const scatter = stats.scatter?.fr;
    if (scatter?.[0]?.length && window.Plotly) {
      const truth = scatter[0];
      const prediction = scatter[1];
      const all = [...truth, ...prediction].filter(Number.isFinite);
      const low = Math.min(...all); const high = Math.max(...all); const pad = (high - low) * 0.05 || 1;
      renderPlot($('#self-test-scatter'), {
        data: [
          { x: [low - pad, high + pad], y: [low - pad, high + pad], type: 'scatter', mode: 'lines', name: 'perfect', line: { color: '#5B6478', dash: 'dash' } },
          { x: truth, y: prediction, type: 'scatter', mode: 'markers', name: 'held-out points', marker: { color: '#4F46E5', size: 7, opacity: .75 } },
        ],
        layout: { title: { text: 'Resonant frequency — held-out parity', x: .01, font: { color: '#14213D', size: 14 } }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', margin: { l: 58, r: 20, t: 54, b: 50 }, xaxis: { title: 'CST ground truth (GHz)', range: [low - pad, high + pad], gridcolor: 'rgba(20,33,61,.10)' }, yaxis: { title: 'Engine prediction (GHz)', range: [low - pad, high + pad], gridcolor: 'rgba(20,33,61,.10)' } },
      }, 400);
    }
  }

  function renderAbTest(result, _job, target) {
    if (!result) {
      target.innerHTML = '<div class="notice info">No comparison available. No Keras model may be loaded.</div>';
      return;
    }
    const metrics = [['Resonant frequency', 'MHz', 'fr_mhz'], ['S11 minimum', 'dB', 's11_db'], ['Bandwidth', 'MHz', 'bw_mhz'], ['Gain at fr', 'dBi', 'gain_dbi']];
    let csvWins = 0; let modelWins = 0;
    const rows = metrics.map(([quantity, unit, key]) => {
      const csv = Number(result.csv?.[key]); const model = Number(result.model?.[key]);
      let winner = 'tie';
      if (Number.isFinite(csv) && Number.isFinite(model)) {
        if (csv < model) { winner = 'CST interpolation'; csvWins += 1; }
        if (model < csv) { winner = 'Trained model'; modelWins += 1; }
      }
      return { Quantity: quantity, Unit: unit, 'CST interpolation': csv, 'Trained model': model, 'Lower error': winner };
    });
    let conclusion = 'Neither path is clearly better. Decide on other grounds — generalisation far from the dataset favours the model.';
    let kind = 'info';
    if (modelWins > csvWins) { conclusion = 'The trained model is more accurate on held-out geometries. Consider making it the default answer (Option A).'; kind = 'success'; }
    if (csvWins > modelWins) { conclusion = 'CST interpolation is more accurate on held-out geometries. Keeping it as the default is justified (Option C) — but the UI should say so plainly instead of implying the model produced it.'; }
    target.innerHTML = `${tableHtml(rows, [
      { key: 'Quantity', label: 'Quantity' }, { key: 'Unit', label: 'Unit' },
      { key: 'CST interpolation', label: 'CST interpolation', format: (value) => formatNumber(value, 4) }, { key: 'Trained model', label: 'Trained model', format: (value) => formatNumber(value, 4) }, { key: 'Lower error', label: 'Lower error' },
    ])}<p class="hint">Scored on ${Number(result.n)} identical held-out geometries. Lower MAE wins. <strong>CST ${csvWins} — model ${modelWins}</strong>.</p><div class="notice ${kind}">${escapeHtml(conclusion)}</div>`;
  }

  function renderInverseTest(result, job, target) {
    if (!result?.summary) {
      target.innerHTML = '<div class="notice info">Inverse self-test completed but no metrics were produced.</div>';
      return;
    }
    const summary = result.summary;
    const cards = [
      { label: 'Tests', value: String(summary.tests) }, { label: 'Mean fr error', value: `${formatNumber(summary.mean_err_mhz, 1)} MHz` },
      { label: 'P90 fr error', value: `${formatNumber(summary.p90_err_mhz, 1)} MHz` }, { label: 'Max fr error', value: `${formatNumber(summary.max_err_mhz, 1)} MHz` },
    ];
    const table = tableHtml(result.family || [], [
      { key: 'family', label: 'Family' }, { key: 'mean_err_mhz', label: 'Mean fr error (MHz)', format: (value) => formatNumber(value, 4) },
    ]);
    const download = job.csv_ready ? `<div class="validation-actions"><a class="btn o" href="/api/jobs/${encodeURIComponent(job.job_id)}/inverse.csv">Download Inverse Test Table (CSV)</a></div>` : '';
    target.innerHTML = `${metricCardsHtml(cards)}${table}${download}`;
  }

  function renderHealthcheck(result, _job, target) {
    if (!result) {
      target.innerHTML = '<div class="notice info">No health-check output was produced.</div>';
      return;
    }
    const rows = (result.checks || []).map(([check, ok]) => ({ Check: check, Result: ok ? 'PASS' : 'FAIL' }));
    target.innerHTML = `<div class="notice ${result.ok ? 'success' : 'warning'}">Startup health check: <strong>${result.ok ? 'PASS' : 'FAIL'}</strong></div>${tableHtml(rows, [{ key: 'Check', label: 'Check' }, { key: 'Result', label: 'Result' }])}`;
  }

  async function boot() {
    bindTabs();
    bindHeroParallax();
    observeRevealElements();
    bindForwardControls();
    bindInverseControls();
    bindHertz();
    bindDataStory();
    bindValidation();
    renderHertz();
    try {
      await loadMeta();
    } catch (error) {
      setEngineBanner(`Unable to load interface metadata: ${error.message}`, true);
    }
    pollHealthUntilReady();
  }

  boot();
})();
