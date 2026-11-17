// Runs before the page is drawn, so the chosen theme never flashes the wrong colours.
(function () {
  try {
    var root = document.documentElement;
    if (root.getAttribute('data-theme')) { return; }   // a logged-in player's choice comes from the server
    var saved = localStorage.getItem('iq.theme');
    if (saved === 'light' || saved === 'dark' || saved === 'system') { root.setAttribute('data-theme', saved); }
  } catch (e) { /* storage can be blocked; the system theme is used */ }
})();