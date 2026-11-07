# -*- coding: utf-8 -*-
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
p=root/'交互记录/截图内容.json'
cards=json.loads(p.read_text(encoding='utf-8'))
cards[1]['title']='参数化与离散权重'
cards[1]['question_parts']=['请重新核对，明确正确分母，并说明为何同尺寸仍不等于相同离散核。']
cards[2]['title']='函数与输出核验'
cards[2]['question_parts']=['推导与代码是否相符，包括连续L/2和离散(len-1)/2；','图方向和图题是否一致。']
cards[2]['answer_parts']=['连续模型的 L/2 与离散半长 (ell−1)/2 已区分；推导、最终代码和日志在半核网格、端点权重、镜像及归一化上吻合。','图中 0° 水平、45° 左下至右上、90° 竖直，方向与题注一致，测试统计也与日志相符。']
for card in cards:
    card.pop('footer',None)
p.write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf-8')
