/* Comic engine: one best-fit frame per paragraph.
   - Each prose paragraph carries data-pidx="<n>"; act1.panelmap.json maps that
     index to a specific beat + panel (chosen by multi-agent caption matching).
   - The frame is drawn from the beat's sprite strip via background-position-y.
   - No caption boxes: the paragraph IS the text. The paragraph lights while its
     image is in view, and images lazy-load just before entering the viewport. */
(function () {
  'use strict';

  var MANIFEST_URL = './assets/comic/act1.comic.json';
  var PANELMAP_URL = './assets/comic/act1.panelmap.json';

  function bgPosY(strip_h, rect) {
    // strip is full-width; show one 16:9 cell by shifting vertically.
    return strip_h > rect.h ? (rect.y / (strip_h - rect.h)) * 100 : 0;
  }

  function indexManifest(manifest) {
    var beats = new Map();
    manifest.beats.forEach(function (beat) {
      var byFile = new Map();
      (beat.panels || []).forEach(function (p) { byFile.set(p.file, p); });
      beats.set(beat.beat, { beat: beat, panels: byFile });
    });
    return beats;
  }

  function buildFigure(beat, panel, alt) {
    var fig = document.createElement('figure');
    fig.className = 'comic-figure' + (beat.is_section_break ? ' is-divider' : '');
    fig.setAttribute('role', 'img');
    fig.setAttribute('aria-label', alt || panel.alt || beat.beat);
    return {
      fig: fig,
      bg: 'url("./' + beat.strip + '")',
      posy: bgPosY(beat.strip_h, panel.rect) + '%'
    };
  }

  function render(manifest, panelmap) {
    var beats = indexManifest(manifest);
    var items = [];
    document.querySelectorAll('[data-pidx]').forEach(function (anchor) {
      var entry = panelmap[anchor.getAttribute('data-pidx')];
      if (!entry) { return; }
      var b = beats.get(entry.beat);
      if (!b) { return; }
      var panel = b.panels.get(entry.file);
      if (!panel) { return; }
      var f = buildFigure(b.beat, panel, entry.alt);
      anchor.parentNode.insertBefore(f.fig, anchor.nextSibling);
      items.push({ fig: f.fig, lit: anchor, bg: f.bg, posy: f.posy, loaded: false });
    });
    observe(items);
    return items.length;
  }

  function load(it) {
    if (it.loaded) { return; }
    it.fig.style.backgroundImage = it.bg;
    it.fig.style.backgroundPositionY = it.posy;
    it.loaded = true;
  }

  function observe(items) {
    var byFig = new Map();
    items.forEach(function (it) { byFig.set(it.fig, it); });

    // Loader: set the background a bit before the image enters view.
    var loader = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { var it = byFig.get(e.target); if (it) { load(it); } loader.unobserve(e.target); }
      });
    }, { rootMargin: '600px 0px 600px 0px' });
    items.forEach(function (it) { loader.observe(it.fig); });

    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) { items.forEach(function (it) { load(it); it.fig.classList.add('is-visible'); }); return; }

    // Viewer: fade the image in and light its paragraph while in view.
    var viewer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var it = byFig.get(e.target);
        if (!it) { return; }
        if (e.isIntersecting) {
          load(it);
          it.fig.classList.add('is-visible');
          if (it.lit && it.lit.classList) { it.lit.classList.add('lit'); }
        } else if (it.lit && it.lit.classList) {
          it.lit.classList.remove('lit');
        }
      });
    }, { rootMargin: '0px 0px -30% 0px', threshold: 0.25 });
    items.forEach(function (it) { viewer.observe(it.fig); });
  }

  var ready = Promise.all([
    fetch(MANIFEST_URL).then(function (r) { return r.json(); }),
    fetch(PANELMAP_URL).then(function (r) { return r.json(); })
  ])
    .then(function (res) { return { count: render(res[0], res[1]) }; })
    .catch(function (err) { console.error('ComicEngine failed:', err); return { count: 0 }; });

  window.ComicEngine = { ready: ready };
})();
