// Sound effects made with the browser's Web Audio API: no files to download and no licences.
(function (IQ) {
  var context = null;
  var enabled = true;

  function audio() {
    if (!context) {
      var Maker = window.AudioContext || window.webkitAudioContext;
      if (!Maker) { return null; }
      context = new Maker();
    }
    if (context.state === 'suspended') { context.resume(); }
    return context;
  }

  // One short note. freq is in hertz; endFreq makes the note slide.
  function tone(freq, start, length, type, volume, endFreq) {
    var c = audio();
    if (!c) { return; }
    var osc = c.createOscillator();
    var gain = c.createGain();
    var t = c.currentTime + start;
    osc.type = type || 'sine';
    osc.frequency.setValueAtTime(freq, t);
    if (endFreq) { osc.frequency.exponentialRampToValueAtTime(endFreq, t + length); }
    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.exponentialRampToValueAtTime(volume || 0.15, t + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + length);
    osc.connect(gain);
    gain.connect(c.destination);
    osc.start(t);
    osc.stop(t + length + 0.02);
  }

  var sounds = {
    tap: function () { tone(520, 0, 0.06, 'triangle', 0.1); },
    correct: function () { tone(523, 0, 0.12); tone(659, 0.1, 0.12); tone(784, 0.2, 0.22); },
    wrong: function () { tone(180, 0, 0.25, 'sawtooth', 0.1, 90); },
    heart: function () { tone(330, 0, 0.3, 'square', 0.08, 110); },
    hit: function () { tone(150, 0, 0.1, 'square', 0.12, 70); },
    levelup: function () { tone(523, 0, 0.12); tone(659, 0.12, 0.12); tone(784, 0.24, 0.12); tone(1047, 0.36, 0.3); },
    win: function () { tone(392, 0, 0.15); tone(523, 0.15, 0.15); tone(659, 0.3, 0.15); tone(784, 0.45, 0.45); },
    badge: function () { tone(988, 0, 0.1); tone(1319, 0.1, 0.25); }
  };

  IQ.sound = {
    names: Object.keys(sounds),
    setEnabled: function (value) { enabled = !!value; },
    isEnabled: function () { return enabled; },
    // Call this from a click or key press. Browsers block sound until the player has interacted.
    play: function (name) {
      if (!enabled || !sounds[name]) { return; }
      try { sounds[name](); } catch (e) { /* sound is optional */ }
    }
  };

  // A soft tap when the player presses a map node, a button, or an avatar.
  document.addEventListener('click', function (event) {
    if (event.target.closest && event.target.closest('a.node, a.wnode, .avatar-card, .btn')) {
      IQ.sound.play('tap');
    }
  });
})(window.IQ);