#!/usr/bin/env python3
"""East Asia ICT MSSD AI Brief 게시 스크립트.

1) 메일 게시:   python3 scripts/publish.py <gmail_message.json>
   → daily/DATE.html, data/days/DATE.json(번역 원본), data/briefs.json 갱신
2) 영어 반영:   python3 scripts/publish.py --en DATE
   → data/days/DATE.en.json 검증 후 briefs.json에 영어 제목·요약·항목 병합
"""
import html, json, re, sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = {'🔴': 'HUAWEI', '📶': '运营商', '🏭': '友商', '🤖': 'AI', '💻': 'ICT'}


def to_lines(h):
    t = re.sub(r'<(br|/tr|/div|/p|/td)[^>]*>', '\n', h)
    t = html.unescape(re.sub(r'<[^>]+>', '', t))
    return [l.strip() for l in t.split('\n') if l.strip()]


def tri(L, i):
    """L[i]부터 '中', '한', '日' 라벨 뒤의 문장을 찾아 {zh,ko,ja} 반환."""
    out = {}
    for lab, key in (('中', 'zh'), ('한', 'ko'), ('日', 'ja')):
        while i < len(L) and L[i] != lab:
            i += 1
        if i + 1 < len(L):
            out[key] = L[i + 1]
            i += 2
    return out, i


def find(L, pred, start=0, end=None):
    end = len(L) if end is None else end
    return next((k for k in range(start, end) if pred(L[k])), None)


def original_urls(h):
    urls = []
    for m in re.finditer(r'<a [^>]*href="([^"]+)"[^>]*>(?:(?!</a>).)*原文', h, re.S):
        u = html.unescape(m.group(1))
        q = parse_qs(urlparse(u).query).get('q')
        urls.append(q[0] if q and 'google.com/url' in u else u)
    return urls


def extract(body):
    L = to_lines(body)
    date = next(m.group(1) for l in L if (m := re.match(r'(\d{4}-\d{2}-\d{2}) \(\w+\)', l)))
    d = {'date': date}

    i = find(L, lambda l: l.startswith('今日摘要'))
    d['summary'], _ = tri(L, i)

    first_sec = find(L, lambda l: l[:1] in SECTIONS or l[:2] in SECTIONS)
    ana = find(L, lambda l: l.startswith('🔍'))
    ins = find(L, lambda l: l.startswith('💡'))

    # 今日三大变化
    d['changes'] = []
    c = find(L, lambda l: '今日三大变化' in l)
    if c is not None:
        k = c + 1
        while k < (first_sec or len(L)) and re.match(r'^\d\. ', L[k]):
            ch = {'title': {'zh': L[k][3:], 'ko': L[k + 1], 'ja': L[k + 2]}}
            ch['why'], k = tri(L, k + 3)
            ch['impact'], k = tri(L, k)
            d['changes'].append(ch)
            k = find(L, lambda l: re.match(r'^\d\. ', l) or l[:1] in SECTIONS or l[:2] in SECTIONS, k) or len(L)

    # 기사
    urls = original_urls(body)
    d['articles'] = []
    section = ''
    end = ana or ins or len(L)
    for k in range(first_sec or 0, end):
        l = L[k]
        for e, name in SECTIONS.items():
            if l.startswith(e):
                section = name
        if l != '原文':
            continue
        j = next((x for x in range(k - 1, max(k - 6, 0), -1) if L[x] == '日'), None)
        if not (j and L[j - 2] == '한' and L[j - 4] == '中'):
            continue
        meta = L[j + 2:k]
        art = {'section': section,
               'title': {'zh': L[j - 3], 'ko': L[j - 1], 'ja': L[j + 1]},
               'source': meta[0] if meta else '',
               'published': meta[1] if len(meta) > 1 else '',
               'url': urls[len(d['articles'])] if len(d['articles']) < len(urls) else ''}
        art['summary'], n = tri(L, k + 1)
        p = find(L, lambda x: x == '点评', n, n + 2)
        if p is not None:
            art['comment'] = {'zh': L[p + 1], 'ko': L[p + 2], 'ja': L[p + 3]}
        d['articles'].append(art)

    # 重点事件分析
    if ana is not None:
        a = {'title': {'zh': L[ana + 1], 'ko': L[ana + 2], 'ja': L[ana + 3]}}
        for key, lab in (('facts', '事件事实'), ('why', '为什么重要'), ('impact', '对韩国ICT'), ('watch', '后续观察点')):
            p = find(L, lambda x: x.startswith(lab), ana, ins)
            if p is not None:
                a[key], _ = tri(L, p)
        d['analysis'] = a

    # 业务启示
    if ins is not None:
        def numbered(start, stop):
            res, k = [], start
            while k is not None and k < stop:
                if re.fullmatch(r'\d', L[k]):
                    res.append({'zh': L[k + 1], 'ko': L[k + 2], 'ja': L[k + 3]})
                    k += 4
                else:
                    k += 1
            return res
        j1 = find(L, lambda x: x.startswith('今日产业判断'), ins)
        j2 = find(L, lambda x: x.startswith('建议持续跟踪'), ins)
        foot = find(L, lambda x: x.startswith('整理时间'), ins) or len(L)
        d['insights'] = {'judgments': numbered(j1 + 1, j2 or foot) if j1 else [],
                         'watch': numbered(j2 + 1, foot) if j2 else []}

    ov = next((l for l in L if l.startswith('数据概览')), '')
    d['tags'] = [f'{n} {m.group(1)}' for n in SECTIONS.values()
                 if (m := re.search(re.escape(n) + r' (\d+)', ov)) and m.group(1) != '0']
    return d


def load_index():
    jp = ROOT / 'data' / 'briefs.json'
    return jp, json.loads(jp.read_text(encoding='utf-8'))


def save_index(jp, data):
    data['briefs'].sort(key=lambda b: b['date'], reverse=True)
    jp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def publish(src):
    msg = json.load(open(src, encoding='utf-8'))
    body = msg['htmlBody']
    d = extract(body)
    date, yymmdd = d['date'], d['date'][2:].replace('-', '')
    if not d['articles']:
        sys.exit('ERROR: 기사 0건 — 메일 구조 확인 필요')

    page = ('<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>East Asia ICT MSSD AI Brief {yymmdd}</title>'
            '<link rel="stylesheet" href="../assets/brief.css"></head>'
            f'<body data-date="{date}" style="margin:0;background-color:#f3f0e9;">'
            '<div class="topbar"><a href="../">← <span data-i18n="back">전체 목록</span></a>'
            '<div id="langbar"></div></div>'
            '<div id="brief">' + body + '</div><div id="en"></div>'
            '<script src="../assets/lang.js"></script></body></html>')
    (ROOT / 'daily').mkdir(exist_ok=True)
    (ROOT / 'daily' / f'{date}.html').write_text(page, encoding='utf-8')

    days = ROOT / 'data' / 'days'
    days.mkdir(parents=True, exist_ok=True)
    (days / f'{date}.json').write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    jp, data = load_index()
    old = next((b for b in data['briefs'] if b.get('date') == date), {})
    data['briefs'] = [b for b in data['briefs'] if b.get('date') != date and b.get('title') != '예시 브리프 제목']
    data['links'] = [l for l in data.get('links', []) if '예시' not in l.get('title', '')]
    first = d['changes'][0]['title'] if d['changes'] else {k: v[:40] for k, v in d['summary'].items()}
    entry = {'date': date, 'title': dict(first), 'summary': dict(d['summary']), 'tags': d['tags'],
             'url': f'daily/{date}.html',
             'items': [t for a in d['articles'] for t in (a['title']['zh'], a['title']['ko'], a['title']['ja'])]}
    # 같은 날짜 재게시 시 기존 영어 번역 유지
    if isinstance(old.get('title'), dict) and 'en' in old['title']:
        entry['title']['en'] = old['title']['en']
        entry['summary']['en'] = old['summary'].get('en', '')
        entry['items'] += [i for i in old.get('items', []) if i not in entry['items']]
    data['briefs'].append(entry)
    save_index(jp, data)
    print(f'published {date}: {len(d["articles"])} articles, {len(d["changes"])} changes, '
          f'analysis={"analysis" in d}, tags={d["tags"]}')


def merge_en(date):
    days = ROOT / 'data' / 'days'
    src = json.loads((days / f'{date}.json').read_text(encoding='utf-8'))
    en = json.loads((days / f'{date}.en.json').read_text(encoding='utf-8'))
    assert en.get('summary'), 'en.summary 없음'
    assert len(en.get('articles', [])) == len(src['articles']), \
        f'기사 수 불일치: en {len(en.get("articles", []))} / 원본 {len(src["articles"])}'
    for a in en['articles']:
        assert a.get('title') and a.get('summary'), '기사 title/summary 누락'
    jp, data = load_index()
    b = next(b for b in data['briefs'] if b['date'] == date)
    b['title']['en'] = en['changes'][0]['title'] if en.get('changes') else en['summary'][:60]
    b['summary']['en'] = en['summary']
    b['items'] = [i for i in b['items'] if i not in [a['title'] for a in en['articles']]] + \
                 [a['title'] for a in en['articles']]
    save_index(jp, data)
    print(f'merged en {date}: {len(en["articles"])} articles')


if __name__ == '__main__':
    if sys.argv[1] == '--en':
        merge_en(sys.argv[2])
    else:
        publish(sys.argv[1])
