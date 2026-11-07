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
.card { width:1200px; border:1px solid #bac4ce; background:white; }
.head { display:flex; justify-content:space-between; padding:15px 24px;
        border-bottom:1px solid #d6dde4; background:#f2f5f8; }
.title { font-size:24px; font-weight:600; }
.meta { font-size:20px; color:#4b5e70; }
.exchange { padding:13px 24px 0; }
.label { color:#38546b; font-size:20px; font-weight:600; margin:0 0 3px; }
p { font-size:24px; line-height:1.43; margin:0 0 9px; text-align:justify; }
code { font-family:Consolas,monospace; font-size:23px; }
.foot { padding:10px 24px 13px; color:#66717b; font-size:18px; }
'''

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        headless=True)
    page = browser.new_page(viewport={'width':1200,'height':1600},device_scale_factor=2)
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
<span class="meta">AI 问答摘录 · 第 {card['round']} 轮</span></div>
<div class="exchange"><div class="label">提问</div><p>{inline(question)}</p>
<div class="label">AI · Luna</div><p>{inline(answer)}</p></div>
<div class="foot">{html.escape(card['footer'])}</div></article></html>'''
        (folder/(card['file']+'.html')).write_text(markup,encoding='utf-8')
        page.set_content(markup,wait_until='load')
        page.locator('.card').screenshot(path=str(folder/(card['file']+'.png')))
        print(card['file'],page.locator('.card').bounding_box())
    browser.close()
