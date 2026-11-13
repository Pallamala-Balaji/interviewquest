// Hero page: live preview of the chosen avatar and name.
(function () {
  var form = document.getElementById('heroForm');
  var data = document.getElementById('avatarData');
  if (!form || !data) { return; }

  var info = JSON.parse(data.textContent);
  var emojiEl = document.getElementById('stageEmoji');
  var typeEl = document.getElementById('stageType');
  var tagEl = document.getElementById('stageTag');
  var plateEl = document.getElementById('plateName');
  var countEl = document.getElementById('nameCount');
  var liveEl = document.getElementById('avatarLive');
  var surprise = document.getElementById('surprise');
  var nameInput = form.querySelector('input[name="hero_name"]');
  var radios = Array.prototype.slice.call(form.querySelectorAll('input[name="avatar_id"]'));
  var suggestions = ['Query Knight', 'Loop Wizard', 'Byte Ranger', 'Stack Sage',
                     'Bug Hunter', 'Syntax Scout', 'Null Ninja', 'Index Hero'];
  var nameEdited = nameInput.value.trim() !== '';

  function showAvatar(radio) {
    var item = info[radio.value];
    if (!item) { return; }
    emojiEl.textContent = radio.getAttribute('data-emoji');
    typeEl.textContent = item.name;
    tagEl.textContent = item.tag;
    liveEl.textContent = item.name + ' selected';
    emojiEl.classList.remove('pop');
    void emojiEl.offsetWidth;          // restart the animation
    emojiEl.classList.add('pop');
  }

  function showName() {
    plateEl.textContent = nameInput.value.trim() || 'Your hero';
    countEl.textContent = nameInput.value.length + '/20';
  }

  radios.forEach(function (radio) {
    radio.addEventListener('change', function () {
      if (radio.checked) { showAvatar(radio); }
    });
  });

  nameInput.addEventListener('input', function () {
    nameEdited = true;
    showName();
  });
  showName();

  if (surprise) {
    surprise.hidden = false;
    surprise.addEventListener('click', function () {
      var current = radios.findIndex(function (r) { return r.checked; });
      var next;
      do {
        next = Math.floor(Math.random() * radios.length);
      } while (radios.length > 1 && next === current);
      radios[next].checked = true;
      showAvatar(radios[next]);
      if (!nameEdited) {
        nameInput.value = suggestions[Math.floor(Math.random() * suggestions.length)];
        showName();
      }
    });
  }
})();
