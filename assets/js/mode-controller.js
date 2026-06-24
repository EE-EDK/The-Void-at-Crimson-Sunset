/* Mode controller: Read / Read+Atmosphere / Narrated (per-shot audio). */
(function () {
  'use strict';

  var MODES = ['read', 'atmosphere', 'narrated'];
  var LABELS = { read: 'Read', atmosphere: 'Atmosphere', narrated: 'Narrated' };
  var NARR_URL = './assets/comic/act1.narration.json';
  var STORAGE = 'void-mode';

  var state = { mode: 'read', narration: null, sounds: {}, currentShot: null };

  function setBodyMode(mode) {
    MODES.forEach(function (m) { document.body.classList.remove('mode-' + m); });
    document.body.classList.add('mode-' + mode);
  }

  function buildSwitch(onPick, narrationReady) {
    var nav = document.createElement('nav');
    nav.className = 'comic-mode-switch';
    nav.setAttribute('aria-label', 'Reading mode');
    MODES.forEach(function (m) {
      var b = document.createElement('button');
      b.textContent = LABELS[m];
      b.setAttribute('aria-pressed', String(m === state.mode));
      if (m === 'narrated' && !narrationReady) { b.disabled = true; b.title = 'Narration coming soon'; }
      b.addEventListener('click', function () { onPick(m); });
      nav.appendChild(b);
    });
    document.body.appendChild(nav);
    return nav;
  }

  function refreshButtons(nav) {
    Array.prototype.forEach.call(nav.querySelectorAll('button'), function (b) {
      b.setAttribute('aria-pressed', String(b.textContent === LABELS[state.mode]));
    });
  }

  function shotForBeat(beat) {
    return state.narration ? state.narration.beat_to_shot[beat] : null;
  }
  function shotMeta(shotId) {
    return state.narration.shots.filter(function (s) { return s.shot === shotId; })[0];
  }

  function playShot(shotId) {
    if (!shotId || shotId === state.currentShot) { return; }
    var meta = shotMeta(shotId);
    if (!meta || meta.status !== 'ready') { return; }   // pending shot: stay silent (Atmosphere continues)
    Object.keys(state.sounds).forEach(function (k) { state.sounds[k].stop(); });
    if (!state.sounds[shotId]) {
      state.sounds[shotId] = new window.Howl({ src: ['./' + meta.audio], html5: true, volume: 0.9 });
    }
    state.sounds[shotId].play();
    state.currentShot = shotId;
  }

  function watchBeatsForNarration() {
    var io = new IntersectionObserver(function (entries) {
      if (state.mode !== 'narrated') { return; }
      entries.forEach(function (e) {
        if (e.isIntersecting) { playShot(shotForBeat(e.target.getAttribute('data-beat'))); }
      });
    }, { rootMargin: '0px 0px -45% 0px', threshold: 0.1 });
    document.querySelectorAll('[data-beat]').forEach(function (n) { io.observe(n); });
  }

  function stopAllAudio() {
    Object.keys(state.sounds).forEach(function (k) { state.sounds[k].stop(); });
    state.currentShot = null;
  }

  function applyMode(mode) {
    state.mode = mode;
    setBodyMode(mode);
    localStorage.setItem(STORAGE, mode);
    if (mode !== 'narrated') { stopAllAudio(); }
    // Atmosphere/Read: the existing horror engine runs on scroll regardless; Read users can mute
    // via the page's existing audio controls. No teardown needed here.
  }

  function init() {
    state.mode = localStorage.getItem(STORAGE) || 'read';
    fetch(NARR_URL).then(function (r) { return r.json(); }).catch(function () { return null; })
      .then(function (narr) {
        state.narration = narr;
        var ready = !!(narr && narr.shots.some(function (s) { return s.status === 'ready'; }));
        if (state.mode === 'narrated' && !ready) { state.mode = 'read'; }
        var nav = buildSwitch(function (m) { applyMode(m); refreshButtons(nav); }, ready);
        setBodyMode(state.mode);
        watchBeatsForNarration();
      });
  }

  if (window.ComicEngine && window.ComicEngine.ready) {
    window.ComicEngine.ready.then(init);
  } else {
    document.addEventListener('DOMContentLoaded', init);
  }
})();
