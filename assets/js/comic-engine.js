/* Comic engine: one uniform image per beat, tied to a highlighted story sentence.
   - No caption boxes (the body prose is the text; no duplicates).
   - Each image is anchored after its [data-beat] paragraph; the sentence it
     illustrates is wrapped in <span class="comic-tie"> and lights up + is
     narrated when the image scrolls into view.
   - Images lazy-load (background set just before they enter view) so a large
     number of beats stays performant. */
(function () {
  'use strict';

  var MANIFEST_URL = './assets/comic/act1.comic.json';
  var ROLE_PRIORITY = ['establish', 'establishing', 'character-close', 'reveal', 'resolution'];

  function bgPosY(beat, rect) {
    // strip is full-width; show one 16:9 cell by shifting vertically.
    return beat.strip_h > rect.h ? (rect.y / (beat.strip_h - rect.h)) * 100 : 0;
  }

  function representativePanel(beat) {
    // one focused image per beat: prefer an establishing/character shot, else first.
    for (var i = 0; i < ROLE_PRIORITY.length; i++) {
      for (var j = 0; j < beat.panels.length; j++) {
        if ((beat.panels[j].role || '').indexOf(ROLE_PRIORITY[i]) === 0) { return beat.panels[j]; }
      }
    }
    return beat.panels[0];
  }

  function buildFigure(beat) {
    var p = representativePanel(beat);
    var fig = document.createElement('figure');
    fig.className = 'comic-figure' + (beat.is_section_break ? ' is-divider' : '');
    fig.setAttribute('role', 'img');
    fig.setAttribute('aria-label', (p && p.alt) || beat.beat);
    return { fig: fig, bg: 'url("./' + beat.strip + '")', posy: bgPosY(beat, p.rect) + '%' };
  }

  function tieLine(beat) {
    var d = (beat.dialogue || [])[0];
    return d && d.line ? d.line : null;
  }

  // Wrap the sentence matching `line` inside `anchor` in <span class="comic-tie">.
  // Returns the element to light (the span, or the anchor itself on fallback).
  function wrapTie(anchor, line) {
    if (!line) { return anchor; }
    var walker = document.createTreeWalker(anchor, NodeFilter.SHOW_TEXT, null);
    var segs = [], full = '', node;
    while ((node = walker.nextNode())) { segs.push({ node: node, start: full.length }); full += node.nodeValue; }
    if (!full) { return anchor; }

    var hay = full.toLowerCase();
    var probe = line.toLowerCase().replace(/\s+/g, ' ').trim().replace(/[^a-z0-9)à-ÿ]+$/, '');
    if (probe.length < 6) { return anchor; }
    var idx = hay.indexOf(probe);
    if (idx < 0) { return anchor; }

    var end = idx + probe.length;
    while (end < full.length && '.!?'.indexOf(full.charAt(end)) === -1) { end++; }
    if (end < full.length) { end++; } // include the terminator

    function locate(pos) {
      for (var k = segs.length - 1; k >= 0; k--) {
        if (pos >= segs[k].start) { return { node: segs[k].node, offset: pos - segs[k].start }; }
      }
      return { node: segs[0].node, offset: 0 };
    }

    try {
      var range = document.createRange();
      var s = locate(idx), e = locate(end);
      range.setStart(s.node, s.offset);
      range.setEnd(e.node, e.offset);
      var span = document.createElement('span');
      span.className = 'comic-tie';
      range.surroundContents(span); // throws if the range partially selects an element (e.g. <em>)
      return span;
    } catch (err) {
      return anchor; // fall back to highlighting the whole paragraph
    }
  }

  function render(manifest) {
    var beatsByName = new Map();
    var items = [];
    manifest.beats.forEach(function (beat) {
      beatsByName.set(beat.beat, beat);
      var anchor = document.querySelector('[data-beat="' + beat.beat + '"]');
      if (!anchor || !beat.panels || !beat.panels.length) { return; }
      var tie = wrapTie(anchor, tieLine(beat));
      var f = buildFigure(beat);
      anchor.parentNode.insertBefore(f.fig, anchor.nextSibling);
      items.push({ fig: f.fig, tie: tie, bg: f.bg, posy: f.posy, loaded: false });
    });
    observe(items);
    return beatsByName;
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

    // Viewer: fade the image in and light its tied sentence while in view.
    var viewer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var it = byFig.get(e.target);
        if (!it) { return; }
        if (e.isIntersecting) {
          load(it);
          it.fig.classList.add('is-visible');
          if (it.tie && it.tie.classList) { it.tie.classList.add('lit'); }
        } else if (it.tie && it.tie.classList) {
          it.tie.classList.remove('lit');
        }
      });
    }, { rootMargin: '0px 0px -30% 0px', threshold: 0.25 });
    items.forEach(function (it) { viewer.observe(it.fig); });
  }

  var ready = fetch(MANIFEST_URL)
    .then(function (r) { return r.json(); })
    .then(function (m) { return { beatsByName: render(m) }; })
    .catch(function (err) { console.error('ComicEngine failed:', err); return { beatsByName: new Map() }; });

  window.ComicEngine = { ready: ready };
})();
