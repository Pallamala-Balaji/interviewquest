// Shared behaviour: dismissible messages and the show/hide password button.
(function () {
  document.querySelectorAll('.flash').forEach(function (flash) {
    var close = flash.querySelector('.flash-close');
    if (close) {
      close.hidden = false;
      close.addEventListener('click', function () { flash.remove(); });
    }
    if (flash.classList.contains('success')) {
      setTimeout(function () { flash.remove(); }, 6000);
    }
  });

  document.querySelectorAll('.input-wrap').forEach(function (wrap) {
    var input = wrap.querySelector('input');
    var button = wrap.querySelector('.reveal');
    if (!input || !button) { return; }
    button.hidden = false;
    button.addEventListener('click', function () {
      var show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      button.textContent = show ? 'Hide' : 'Show';
      button.setAttribute('aria-pressed', show ? 'true' : 'false');
      button.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    });
  });
})();
