# -*- coding: utf-8 -*-
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
folder=root/'交互记录'
q4='最终统计为104组常规+385组边界+1000组随机+2默认全isequal，误差0；四种人为错误（半长、上下翻转、eps、三角计算顺序）均被测试抓住。请严查：①推导与代码是否相符，包括连续L/2和离散(len-1)/2；②旧初版/修正后错误是否解释准确；③有没有范围过宽、无根据、反复自辩或“AI味”措辞；④图方向和图题是否一致。'
a4='连续模型的 L/2 与离散半长 (ell−1)/2 已区分；推导、最终代码和日志在半核网格、端点权重、镜像及归一化上吻合。初版参数化错误及修正后尺寸相同但逐元素不同的解释准确，未将尺寸相同说成支持集相同。图中 0° 水平、45° 左下至右上、90° 竖直，方向与题注一致，测试统计也与日志相符。'
data=json.loads((folder/'实际问答.json').read_text(encoding='utf-8'))
data['records']=[r for r in data['records'] if r['round']!=4]
data['records'].append(dict(round=4,question=q4,answer=a4,review='P1：无。P2：建议将输入范围写明为有限实数double标量。正文已补充。第5节截图排版由主审另行逐页验证。'))
(folder/'实际问答.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
cards=json.loads((folder/'截图内容.json').read_text(encoding='utf-8'))
cards=[c for c in cards if c['file']!='03_最终核验']
cards.append(dict(file='03_最终核验',title='最终代码与结果核验',round=4,question_parts=['最终统计为104组常规+385组边界+1000组随机+2默认全isequal，误差0；','①推导与代码是否相符，包括连续L/2和离散(len-1)/2；','④图方向和图题是否一致。'],answer_parts=[a4],footer='实际问答摘录 · 核验依据为最终函数、MATLAB 日志与核函数图'))
(folder/'截图内容.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf-8')
parts=['# AI 交互过程\n','本文件整理 2026 年 11 月 5 日与 Luna 的实际问答。报告内三张图片为摘录排版截图；代码与数值均有对应文件。\n']
for r in data['records']:
    parts += [f"## 第 {r['round']} 轮\n",'提问：'+r['question']+'\n','AI 答复：'+r['answer']+'\n']
    if 'code' in r: parts.append('```matlab\n'+r['code']+'```\n')
    for key in ['note','review']:
        if key in r: parts.append('核查记录：'+r[key]+'\n')
(root/'AI交互过程.md').write_text('\n'.join(parts),encoding='utf-8')
print('Final actual dialogue added.')
