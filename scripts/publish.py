#!/usr/bin/env python3
"""Gmail get_message 결과(JSON) → daily/날짜.html + data/briefs.json 갱신.
사용: python3 scripts/publish.py <gmail_message.json>
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def to_lines(h):
    t = re.sub(r'<(br|/tr|/div|/p|/td)[^>]*>', '\n', h)
    t = html.unescape(re.sub(r'<[^>]+>', '', t))
    return [l.strip() for l in t.split('\n') if l.strip()]

def after(lines, start, label):
    for i in range(start, len(lines)):
        if lines[i] == label:
            return lines[i + 1]
    return ''

def main(src):
    msg = json.load(open(src, encoding='utf-8'))
    body = msg['htmlBody']
    L = to_lines(body)

    date = next(m.group(1) for l in L if (m := re.match(r'(\d{4}-\d{2}-\d{2}) \(\w+\)', l)))
    yymmdd = date[2:].replace('-', '')

    i = next(k for k, l in enumerate(L) if l.startswith('今日摘要'))
    summary = after(L, i, '한')

    j = next((k for k, l in enumerate(L) if '今日三大变化' in l), None)
    title = L[j + 2] if j is not None and L[j + 1].startswith('1.') else summary[:40]

    tags = []
    ov = next((l for l in L if l.startswith('数据概览')), '')
    for name in ['HUAWEI', '运营商', '友商', 'AI', 'ICT']:
        m = re.search(re.escape(name) + r' (\d+)', ov)
        if m and m.group(1) != '0':
            tags.append(f'{name} {m.group(1)}')

    items = []
    for k, l in enumerate(L):
        if l != '原文':
            continue
        d = next((x for x in range(k - 1, max(k - 6, 0), -1) if L[x] == '日'), None)
        if d and d >= 4 and L[d - 2] == '한' and L[d - 4] == '中':
            items += [L[d - 3], L[d - 1]]

    page = ('<!doctype html><html lang="zh"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>East Asia ICT MSSD AI Brief {yymmdd}</title></head>'
            '<body style="margin:0;background-color:#f3f0e9;">'
            '<div style="padding:12px 16px;font-family:\'Noto Sans KR\',\'Malgun Gothic\',sans-serif;font-size:14px;">'
            '<a href="../" style="color:#2b59c3;text-decoration:none;">← 전체 목록 / 返回列表</a></div>'
            + body + '</body></html>')
    (ROOT / 'daily').mkdir(exist_ok=True)
    (ROOT / 'daily' / f'{date}.html').write_text(page, encoding='utf-8')

    jp = ROOT / 'data' / 'briefs.json'
    data = json.loads(jp.read_text(encoding='utf-8'))
    data['briefs'] = [b for b in data.get('briefs', [])
                      if b.get('date') != date and b.get('title') != '예시 브리프 제목']
    data['briefs'].append({'date': date, 'title': title, 'summary': summary, 'tags': tags,
                           'url': f'daily/{date}.html', 'items': items})
    data['briefs'].sort(key=lambda b: b['date'], reverse=True)
    data['links'] = [l for l in data.get('links', []) if '예시' not in l.get('title', '')]
    jp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'published {date}: {len(items)//2} articles, tags={tags}')

if __name__ == '__main__':
    main(sys.argv[1])
