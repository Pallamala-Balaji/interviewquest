// Read story text aloud with the browser's speech synthesis. The text is always shown too.
(function (IQ) {
  var synth = window.speechSynthesis;
  if (!synth || !window.SpeechSynthesisUtterance) {
    document.documentElement.classList.add('no-speech');
    return;
  }

  var token = 0;          // changes every time speech starts or stops, so old callbacks are ignored
  var active = null;      // the Listen button that is speaking now

 function voice() {
    var all = synth.getVoices();
    function find(fn) { return all.filter(fn)[0]; }
    return (
      // 1. Best: Natural / Online Indian English voices (e.g., Neerja, Prabhat, Google)
      find(function (v) { return /^en-IN/i.test(v.lang) && /Natural|Online|Google/i.test(v.name); }) ||
      // 2. Any other Indian English voice installed on the device
      find(function (v) { return /^en-IN/i.test(v.lang); }) ||
      // 3. Fallback: Natural English voices (UK / US / AU)
      find(function (v) { return /^en/i.test(v.lang) && /Natural|Online|Google/i.test(v.name); }) ||
      // 4. Any English voice
      find(function (v) { return /^en/i.test(v.lang); }) ||
      null
    );
  }

  function rate() {
    var value = parseFloat(IQ.load('iq.rate') || '1');
    return value >= 0.7 && value <= 1.4 ? value : 1;
  }

  // Short pieces read more reliably than one long text.
  function sentences(text) {
    return text.replace(/\s+/g, ' ').trim().match(/[^.!?]+[.!?]*/g) || [];
  }

  function show(button, label, pressed) {
    button.textContent = label;
    button.setAttribute('aria-pressed', pressed ? 'true' : 'false');
  }

  function finish(button) {
    show(button, 'Listen', false);
    var stop = button.parentNode.querySelector('.listen-stop');
    if (stop) { stop.hidden = true; }
    if (active === button) { active = null; }
  }

  function stopAll() {
    token += 1;
    synth.cancel();
    if (active) { finish(active); }
  }

  function start(button) {
    var target = document.querySelector(button.getAttribute('data-target'));
    if (!target) { return; }
    stopAll();
    var mine = token;
    var parts = sentences(target.textContent);
    var chosen = voice();
    var index = 0;
    active = button;
    show(button, 'Pause', true);
    button.parentNode.querySelector('.listen-stop').hidden = false;

    function next() {
      if (mine !== token) { return; }
      if (index >= parts.length) { finish(button); return; }
      var utterance = new SpeechSynthesisUtterance(parts[index++].trim());
      if (chosen) { utterance.voice = chosen; utterance.lang = chosen.lang; } else { utterance.lang = 'en-IN'; }
      utterance.rate = rate();
      utterance.onend = next;
      utterance.onerror = function () { if (mine === token) { finish(button); } };
      synth.speak(utterance);
    }
    next();
  }

  document.addEventListener('click', function (event) {
    var button = event.target.closest && event.target.closest('.listen');
    if (button) {
      if (active === button && synth.speaking && !synth.paused) { synth.pause(); show(button, 'Resume', true); }
      else if (active === button && synth.paused) { synth.resume(); show(button, 'Pause', true); }
      else { start(button); }
      return;
    }
    if (event.target.closest && event.target.closest('.listen-stop')) { stopAll(); }
  });

  window.addEventListener('pagehide', function () { synth.cancel(); });
})(window.IQ);