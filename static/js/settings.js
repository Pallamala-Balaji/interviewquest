// The settings panel: theme, sound, and reading speed.
(function (IQ) {
  var note = document.getElementById('settingsNote');
  var soundToggle = document.getElementById('soundToggle');
  var soundTest = document.getElementById('soundTest');
  var rate = document.getElementById('rate');
  var themes = document.querySelectorAll('input[name="theme"]');
  if (!soundToggle) { return; }

  function say(text) { if (note) { note.textContent = text; } }

  // Theme
  var theme = document.documentElement.getAttribute('data-theme') || 'system';
  Array.prototype.forEach.call(themes, function (radio) {
    radio.checked = radio.value === theme;
    radio.addEventListener('change', function () {
      IQ.setTheme(radio.value);
      IQ.store('iq.theme', radio.value);
      IQ.savePrefs({ theme: radio.value }).then(function (saved) {
        say(IQ.loggedIn ? (saved ? 'Saved.' : 'Could not save. It will apply on this device.') : 'Log in to keep this on every device.');
      });
    });
  });

  // Sound: a logged-in player's choice comes from the server, a visitor's from this browser.
  var stored = IQ.load('iq.sound');
  var soundOn = IQ.loggedIn ? document.body.getAttribute('data-sound') === '1' : stored !== '0';
  soundToggle.checked = soundOn;
  IQ.sound.setEnabled(soundOn);
  soundToggle.addEventListener('change', function () {
    IQ.sound.setEnabled(soundToggle.checked);
    IQ.store('iq.sound', soundToggle.checked ? '1' : '0');
    IQ.savePrefs({ sound_on: soundToggle.checked }).then(function (saved) {
      say(IQ.loggedIn ? (saved ? 'Saved.' : 'Could not save. It will apply on this device.') : 'Log in to keep this on every device.');
    });
    if (soundToggle.checked) { IQ.sound.play('correct'); }
  });
  if (soundTest) {
    soundTest.addEventListener('click', function () {
      if (!IQ.sound.isEnabled()) { say('Turn sound effects on first.'); return; }
      IQ.sound.play('levelup');
    });
  }

  // Reading speed
  if (rate) {
    rate.value = IQ.load('iq.rate') || '1';
    if (!rate.value) { rate.value = '1'; }
    rate.addEventListener('change', function () { IQ.store('iq.rate', rate.value); });
  }
})(window.IQ);