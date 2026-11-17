// Map pages: bring the current world or stage into view when the page opens.
(function () {
  var current = document.querySelector('.node.current, .wnode.current');
  if (!current || !current.scrollIntoView) { return; }
  var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  current.scrollIntoView({ block: 'center', behavior: calm ? 'auto' : 'smooth' });
})();