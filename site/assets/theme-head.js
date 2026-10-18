/* Runs before first paint. Inline it in <head> on sites without a CSP; load it as a blocking same-origin
   script where the CSP forbids inline scripts. It marks JavaScript as working and applies a saved theme. */
(function () {
  var d = document.documentElement;
  d.classList.add('js');
  try {
    var t = localStorage.getItem('theme');
    if (t === 'dark' || t === 'light') d.setAttribute('data-theme', t);
  } catch (e) {}
})();
