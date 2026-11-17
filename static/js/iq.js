// Shared helpers. Every other script uses window.IQ.
window.IQ = window.IQ || {};
(function (IQ) {
  IQ.loggedIn = document.body.getAttribute('data-logged-in') === '1';

  IQ.store = function (key, value) { try { localStorage.setItem(key, value); } catch (e) { /* blocked */ } };
  IQ.load = function (key) { try { return localStorage.getItem(key); } catch (e) { return null; } };

  IQ.csrf = function () {
    var tag = document.querySelector('meta[name="csrf-token"]');
    return tag ? tag.getAttribute('content') : '';
  };

  // Save settings on the server. Resolves to true or false and never throws.
  IQ.savePrefs = function (data) {
    if (!IQ.loggedIn) { return Promise.resolve(false); }
    return fetch('/api/prefs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': IQ.csrf() },
      body: JSON.stringify(data)
    }).then(function (response) { return response.ok; }).catch(function () { return false; });
  };

  IQ.setTheme = function (value) {
    document.documentElement.setAttribute('data-theme', value);   // system, light, or dark
  };
})(window.IQ);