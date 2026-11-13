// Landing page: type the sample query once, then show the result and reward.
(function () {
  var code = document.getElementById('demoCode');
  var result = document.getElementById('demoResult');
  var reward = document.getElementById('demoReward');
  if (!code || !result || !reward) { return; }
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { return; }

  var full = code.getAttribute('data-full');
  var i = 0;
  code.textContent = '';
  result.hidden = true;
  reward.hidden = true;
  code.classList.add('typing');

  function type() {
    i += 1;
    code.textContent = full.slice(0, i);
    if (i < full.length) {
      setTimeout(type, 36);
      return;
    }
    code.classList.remove('typing');
    setTimeout(function () {
      result.hidden = false;
      result.classList.add('rise');
      setTimeout(function () {
        reward.hidden = false;
        reward.classList.add('pop');
      }, 500);
    }, 400);
  }
  setTimeout(type, 600);
})();
