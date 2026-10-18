/* Shared behaviour for the eleven sites: theme control, phone menu sheet, reveal-once. Load with defer.
   Markup contract:
     <button class="theme" data-theme-toggle aria-pressed="false">Dark</button>
     <button class="bar__menu textbtn" data-menu-toggle aria-expanded="false" aria-controls="menu">Menu</button>
     <nav id="menu" class="sheet" hidden> ... <button data-menu-close>Close</button> ... </nav>
     <section data-reveal> ... </section>
   Canvases that draw with tokens listen for the 'themechange' event on document and repaint. */
(function () {
  var root = document.documentElement;
  var mq = window.matchMedia('(prefers-color-scheme: dark)');

  function current() {
    var t = root.getAttribute('data-theme');
    if (t === 'dark' || t === 'light') return t;
    return mq.matches ? 'dark' : 'light';
  }
  function paintToggles() {
    var dark = current() === 'dark';
    document.querySelectorAll('[data-theme-toggle]').forEach(function (b) {
      b.setAttribute('aria-pressed', dark ? 'true' : 'false');
      b.textContent = dark ? 'Dark' : 'Light';
      b.setAttribute('aria-label', dark ? 'Theme: dark. Switch to light' : 'Theme: light. Switch to dark');
    });
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', getComputedStyle(root).getPropertyValue('--bg').trim());
  }
  function setTheme(t) {
    root.setAttribute('data-theme', t);
    try { localStorage.setItem('theme', t); } catch (e) {}
    paintToggles();
    document.dispatchEvent(new CustomEvent('themechange', { detail: { theme: t } }));
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-theme-toggle]');
    if (!b) return;
    setTheme(current() === 'dark' ? 'light' : 'dark');
  });
  mq.addEventListener('change', function () {
    if (!root.hasAttribute('data-theme')) {
      paintToggles();
      document.dispatchEvent(new CustomEvent('themechange', { detail: { theme: current() } }));
    }
  });
  paintToggles();

  /* phone menu sheet */
  var toggle = document.querySelector('[data-menu-toggle]');
  var sheet = toggle && document.getElementById(toggle.getAttribute('aria-controls'));
  if (toggle && sheet) {
    var lastFocus = null;
    function open() {
      lastFocus = document.activeElement;
      sheet.hidden = false;
      sheet.removeAttribute('inert');
      toggle.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
      var first = sheet.querySelector('a, button');
      if (first) first.focus();
    }
    function close() {
      if (sheet.hidden) return;
      sheet.hidden = true;
      sheet.setAttribute('inert', '');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
      (lastFocus || toggle).focus();
    }
    sheet.setAttribute('inert', '');
    toggle.addEventListener('click', function () { sheet.hidden ? open() : close(); });
    sheet.addEventListener('click', function (e) {
      if (e.target.closest('[data-menu-close]') || e.target.closest('a')) close();
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    sheet.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var f = sheet.querySelectorAll('a[href], button:not([disabled])');
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    window.matchMedia('(min-width: 48em)').addEventListener('change', function (m) { if (m.matches) close(); });
  }

  /* settle: whatever the animations did, nothing stays hidden a few seconds after load */
  window.addEventListener('load', function () { setTimeout(function () { root.classList.add('settled'); }, 3000); });

  /* reveal once; never leaves content hidden */
  var targets = document.querySelectorAll('[data-reveal]');
  if (targets.length) {
    if (!('IntersectionObserver' in window)) { targets.forEach(function (el) { el.classList.add('is-in'); }); }
    else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } });
      }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 });
      targets.forEach(function (el) { io.observe(el); });
      window.addEventListener('load', function () { setTimeout(function () {
        targets.forEach(function (el) { var r = el.getBoundingClientRect(); if (r.top < innerHeight && r.bottom > 0) el.classList.add('is-in'); });
      }, 2500); });
    }
  }
})();
