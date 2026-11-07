# -*- coding: utf-8 -*-
"""Render verified excerpts of actual AI exchanges as local-page screenshots."""
from pathlib import Path
import html
import json
import re
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parent
folder = root / '交互记录'
record = json.loads((folder / '实际问答.json').read_text(encoding='utf-8'))
rounds = {r['round']: r for r in record['records']}
cards = json.loads((folder / '截图内容.json').read_text(encoding='utf-8'))

def inline(text):
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', html.escape(text))

css = '''
* { box-sizing: border-box; }
html, body { margin:0; background:white; }
body { font-family:"Microsoft YaHei",sans-serif; color:#1f2730; }
.card { width:1360px; border:1px solid #cbd4da; background:white; }
.head { display:flex; justify-content:space-between; padding:14px 28px;
        border-bottom:1px solid #d6dde4; background:#edf2f5; }
.title { font-size:28px; font-weight:600; color:#213e50; }
.meta { font-size:24px; color:#64717a; }
.exchange { padding:17px 28px 16px; }
.row { display:grid; grid-template-columns:78px 1fr; gap:18px; }
.row + .row { margin-top:12px; padding-top:12px; border-top:1px solid #edf0f3; }
.label { color:#38546b; font-size:26px; font-weight:600; padding-top:3px; }
p { font-size:32px; line-height:1.45; margin:0; text-align:left; }
code { font-family:Consolas,monospace; font-size:31px; }
'''

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        headless=True)
    page = browser.new_page(viewport={'width':1360,'height':1600},device_scale_factor=2)
    for n,card in enumerate(cards,1):
        source = rounds[card['round']]
        for key in ['question','answer']:
            assert all(part in source[key] for part in card[key+'_parts']), (n,key)
        question = ' […] '.join(card['question_parts'])
        answer = ' […] '.join(card['answer_parts'])
        markup = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>{html.escape(card['title'])}</title><style>{css}</style>
<article class="card">
<div class="head"><span class="title">{n:02d}　{html.escape(card['title'])}</span>
<span class="meta">Luna · 第 {card['round']} 轮</span></div>
<div class="exchange"><div class="row"><div class="label">提问</div><p>{inline(question)}</p></div>
<div class="row"><div class="label">答复</div><p>{inline(answer)}</p></div></div>
</article></html>'''
        (folder/(card['file']+'.html')).write_text(markup,encoding='utf-8')
        page.set_content(markup,wait_until='load')
        page.locator('.card').screenshot(path=str(folder/(card['file']+'.png')))
        print(card['file'],page.locator('.card').bounding_box())
    browser.close()
