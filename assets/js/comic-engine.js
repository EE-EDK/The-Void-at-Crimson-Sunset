/* Comic engine: inject per-beat panel clusters after their prose anchors. */
(function () {
  'use strict';

  var MANIFEST_URL = './assets/comic/act1.comic.json';

  function panelBackground(beat, rect) {
    // strip is full-width (strip_w); show one 16:9 cell by shifting vertically.
    var pct = beat.strip_h > rect.h ? (rect.y / (beat.strip_h - rect.h)) * 100 : 0;
    return {
      backgroundImage: 'url("./' + beat.strip + '")',
      backgroundPositionY: pct + '%'
    };
  }

  function buildCluster(beat) {
    if (beat.is_section_break) {
      var div = document.createElement('div');
      div.className = 'comic-divider';
      div.style.backgroundImage = 'url("./' + beat.strip + '")';
      div.setAttribute('role', 'img');
      div.setAttribute('aria-label', (beat.panels[0] && beat.panels[0].alt) || beat.beat);
      return div;
    }
    var cluster = document.createElement('div');
    cluster.className = 'comic-cluster';
    cluster.setAttribute('data-pacing', beat.pacing_role || 'standard');
    beat.panels.forEach(function (p) {
      var panel = document.createElement('div');
      panel.className = 'comic-panel';
      panel.setAttribute('role', 'img');
      panel.setAttribute('aria-label', p.alt || '');
      var bg = panelBackground(beat, p.rect);
      panel.style.backgroundImage = bg.backgroundImage;
      panel.style.backgroundPositionY = bg.backgroundPositionY;
      cluster.appendChild(panel);
    });
    (beat.dialogue || []).forEach(function (d) {
      var el = document.createElement('div');
      el.className = d.speaker === 'narrator' ? 'comic-caption' : 'comic-bubble';
      el.textContent = d.line;
      cluster.appendChild(el);
    });
    return cluster;
  }

  function render(manifest) {
    var beatsByName = new Map();
    var injected = [];
    manifest.beats.forEach(function (beat) {
      beatsByName.set(beat.beat, beat);
      var anchor = document.querySelector('[data-beat="' + beat.beat + '"]');
      if (!anchor) { return; }                 // unanchored beat: skip (manual placement pending)
      var cluster = buildCluster(beat);
      anchor.parentNode.insertBefore(cluster, anchor.nextSibling);
      injected.push(cluster);
    });
    // observe panels (and dividers) for entry animation
    var panels = [];
    injected.forEach(function (c) {
      if (c.classList.contains('comic-divider')) { panels.push(c); }
      else { c.querySelectorAll('.comic-panel').forEach(function (p) { panels.push(p); }); }
    });
    observePanels(panels);
    return beatsByName;
  }

  function observePanels(panels) {
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) { panels.forEach(function (p) { p.classList.add('is-visible'); }); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    panels.forEach(function (p) { io.observe(p); });
  }

  var ready = fetch(MANIFEST_URL)
    .then(function (r) { return r.json(); })
    .then(function (m) { return { beatsByName: render(m) }; })
    .catch(function (err) { console.error('ComicEngine failed:', err); return { beatsByName: new Map() }; });

  window.ComicEngine = { ready: ready };
})();
