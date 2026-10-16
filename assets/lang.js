// 언어 선택 (中文 / English / 한국어 / 日本語) — 목록·일일 페이지 공용
(function () {
  var LANGS = ['zh', 'en', 'ko', 'ja'];
  var LABEL = { zh: '中文', en: 'English', ko: '한국어', ja: '日本語' };
  var FONT = { zh: /Microsoft YaHei/i, ko: /Noto Sans KR/i, ja: /Meiryo/i };
  var BADGE = { '中': 'zh', '한': 'ko', '日': 'ja' };
  var T = {
    back: { zh: '返回列表', en: 'All briefs', ko: '전체 목록', ja: '一覧へ' },
    noEn: { zh: '', en: 'English version is not available for this date yet.', ko: '', ja: '' },
    summary: { en: "Today's Summary" }, changes: { en: "Today's Top 3 Changes" },
    why: { en: 'Why it matters' }, impact: { en: 'Impact on Huawei · Korea ICT' },
    comment: { en: 'Comment' }, source: { en: 'Source' },
    analysis: { en: 'Key Event Analysis' }, facts: { en: 'Facts' }, impactKr: { en: 'Impact on Korea ICT' },
    watchA: { en: 'What to watch' }, insights: { en: 'Business Implications' },
    judgments: { en: "Today's industry view" }, watch: { en: 'Issues to keep tracking' }
  };
  var SEC = { HUAWEI: '🔴 HUAWEI', '运营商': '📶 Operators', '友商': '🏭 Competitors', AI: '🤖 AI', ICT: '💻 ICT' };

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

  // ---- 일일 페이지: 영어 화면 (data/days/DATE.en.json) ----
  var enLoaded = false;
  function renderEn(box, src, en) {
    var h = '<header><div class="kicker">East Asia ICT MSSD AI Brief</div><h1>' + esc(src.date) + '</h1></header>';
    h += '<section><h2>' + T.summary.en + '</h2><p class="lead">' + esc(en.summary) + '</p></section>';
    if (en.changes && en.changes.length) {
      h += '<section><h2>📌 ' + T.changes.en + '</h2>';
      en.changes.forEach(function (c, i) {
        h += '<div class="card"><h3>' + (i + 1) + '. ' + esc(c.title) + '</h3><h4>' + T.why.en + '</h4><p>' + esc(c.why) +
          '</p><h4>' + T.impact.en + '</h4><p>' + esc(c.impact) + '</p></div>';
      });
      h += '</section>';
    }
    var cur = null;
    en.articles.forEach(function (a, i) {
      var s = src.articles[i] || {};
      if (s.section !== cur) { if (cur !== null) h += '</section>'; cur = s.section; h += '<section><h2>' + esc(SEC[cur] || cur) + '</h2>'; }
      h += '<div class="card"><h3>' + esc(a.title) + '</h3><div class="meta">' + esc(s.source) + (s.published ? ' · ' + esc(s.published) : '') +
        (s.url ? ' · <a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + T.source.en + '</a>' : '') + '</div><p>' + esc(a.summary) + '</p>' +
        (a.comment ? '<div class="note"><b>' + T.comment.en + '</b> ' + esc(a.comment) + '</div>' : '') + '</div>';
    });
    if (cur !== null) h += '</section>';
    if (en.analysis) {
      var a = en.analysis;
      h += '<section><h2>🔍 ' + T.analysis.en + '</h2><div class="card"><h3>' + esc(a.title) + '</h3>' +
        [['facts', 'facts'], ['why', 'why'], ['impact', 'impactKr'], ['watch', 'watchA']].map(function (p) {
          return a[p[0]] ? '<h4>' + T[p[1]].en + '</h4><p>' + esc(a[p[0]]) + '</p>' : '';
        }).join('') + '</div></section>';
    }
    if (en.insights) {
      h += '<section><h2>💡 ' + T.insights.en + '</h2><div class="card"><h4>' + T.judgments.en + '</h4><ol>' +
        (en.insights.judgments || []).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ol><h4>' + T.watch.en + '</h4><ol>' +
        (en.insights.watch || []).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ol></div></section>';
    }
    h += '<footer>Translated by AI from the original brief. Facts and judgments are presented separately; items marked “reportedly” are unconfirmed.</footer>';
    box.innerHTML = h;
  }
  function showEn(box) {
    if (enLoaded) return;
    enLoaded = true;
    var d = document.body.getAttribute('data-date');
    Promise.all(['../data/days/' + d + '.json', '../data/days/' + d + '.en.json'].map(function (u) {
      return fetch(u).then(function (r) { if (!r.ok) throw 0; return r.json(); });
    })).then(function (r) { renderEn(box, r[0], r[1]); })
      .catch(function () { box.innerHTML = '<p class="empty">' + T.noEn.en + '</p>'; });
  }

  // ---- 공통 ----
  function apply(l) {
    try { localStorage.setItem('briefLang', l); } catch (e) {}
    document.documentElement.lang = l === 'zh' ? 'zh' : l;
    document.querySelectorAll('[data-lang-btn]').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-lang-btn') === l); });
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var t = T[el.getAttribute('data-i18n')]; if (t && t[l]) el.textContent = t[l];
    });
    var mail = document.getElementById('brief'), enBox = document.getElementById('en');
    if (mail && enBox) {
      if (l === 'en') { mail.style.display = 'none'; enBox.style.display = 'block'; showEn(enBox); }
      else { mail.style.display = ''; enBox.style.display = 'none'; filterMail(l); }
    }
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
