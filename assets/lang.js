// 언어 선택 (中文 / 한국어 / 日本語) — 목록·일일 페이지 공용
(function () {
  var LANGS = ['zh', 'ko', 'ja'];
  var LABEL = { zh: '中文', ko: '한국어', ja: '日本語' };
  var FONT = { zh: /Microsoft YaHei/i, ko: /Noto Sans KR/i, ja: /Meiryo/i };
  var BADGE = { '中': 'zh', '한': 'ko', '日': 'ja' };
  var T = {
    back: { zh: '返回列表', ko: '전체 목록', ja: '一覧へ' }
  };

  function getLang() {
    var q = new URLSearchParams(location.search).get('lang');
    if (LANGS.indexOf(q) >= 0) return q;
    try { var s = localStorage.getItem('briefLang'); if (LANGS.indexOf(s) >= 0) return s; } catch (e) {}
    return 'ko';
  }
  function esc(s) { return String(s || '').replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function langOf(el) {
    var f = (el.getAttribute('style') || '').match(/font-family:([^;]*)/i);
    if (!f) return null;
    for (var k in FONT) if (FONT[k].test(f[1])) return k;
    return null;
  }

  // ---- 일일 페이지: 메일 원문(中/한/日) 필터 ----
  var blocks = [], inline = [];
  function scan(root) {
    root.querySelectorAll('td[bgcolor]').forEach(function (td) {
      var l = BADGE[td.textContent.trim()];
      if (!l) return;
      var mini = td.closest('table');
      var outer = mini && mini.parentElement && mini.parentElement.closest('table');
      if (outer) blocks.push({ el: outer, lang: l });
    });
    root.querySelectorAll('div[style*="font-family"], span[style*="font-family"]').forEach(function (el) {
      if (el.closest('a')) return;
      var l = langOf(el);
      if (!l || !el.parentElement) return;
      var langs = {};
      Array.prototype.forEach.call(el.parentElement.children, function (c) { var cl = langOf(c); if (cl) langs[cl] = 1; });
      if (Object.keys(langs).length < 2) return;
      inline.push({ el: el, lang: l, text: el.textContent });
    });
  }
  function filterMail(l) {
    blocks.forEach(function (b) { b.el.style.display = b.lang === l ? '' : 'none'; });
    inline.forEach(function (b) {
      b.el.style.display = b.lang === l ? '' : 'none';
      if (b.el.children.length === 0) b.el.textContent = b.text.replace(/^\s*[\/／]\s*/, '');
    });
  }

  // ---- 공통 ----
  function apply(l) {
    try { localStorage.setItem('briefLang', l); } catch (e) {}
    document.documentElement.lang = l;
    document.querySelectorAll('[data-lang-btn]').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-lang-btn') === l); });
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var t = T[el.getAttribute('data-i18n')]; if (t && t[l]) el.textContent = t[l];
    });
    if (document.getElementById('brief')) filterMail(l);
    document.dispatchEvent(new CustomEvent('langchange', { detail: l }));
  }

  window.BriefLang = { get: getLang, set: apply, LANGS: LANGS };

  document.addEventListener('DOMContentLoaded', function () {
    var bar = document.getElementById('langbar');
    if (bar) LANGS.forEach(function (k) {
      var b = document.createElement('button');
      b.type = 'button'; b.textContent = LABEL[k]; b.setAttribute('data-lang-btn', k);
      b.onclick = function () { apply(k); };
      bar.appendChild(b);
    });
    var mail = document.getElementById('brief');
    if (mail) scan(mail);
    apply(getLang());
  });
})();
