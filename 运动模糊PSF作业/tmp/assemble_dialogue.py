# -*- coding: utf-8 -*-
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
q1="请直接编写 MATLAB 函数 motion_psf_ai(len,theta)，根据运动长度（像素）和直角坐标系逆时针角度（度），构造匀速直线运动的离散点扩散函数，目标是与 MATLAB fspecial('motion',LEN,THETA) 输出一致。给出可执行完整代码（尽量35行以内），并用2句解释离散方法。不要声称已运行或已验证。"
a1="代码把运动轨迹视为长度为 `len` 的连续线段，逐像素计算线段穿过该像素方格的长度，再将结果归一化。角度按直角坐标系逆时针解释，并在写入矩阵时映射到向下递增的图像行坐标。"
q2="已把你第一轮代码原样保存为 motion_psf_ai.m，并在 MATLAB R2023b 实测：LEN=9 时，THETA=0 的初版尺寸1×1，内置1×9；45°初版2×2，内置7×7；90°初版1×1，内置9×1，三个isequal均为0。请审查你给出的参数化：p0=-len*d/2，p1=len*d/2，但t分母用d(k)，并将区间限制到[0,1]。这种写法实际覆盖了多长的轨迹？应怎样改这一行？修正该参数化后，按像素方格内轨迹长度积分，能否保证与fspecial的距离权重规则完全相同？"
a2="裁剪用 p(t)=p0+t*d、t∈[0,1]，原 d 是单位向量，故轨迹仅长1像素，len只改变包围盒。将 `d = [cosd(theta), sind(theta)];` 改为 `d = len*[cosd(theta), sind(theta)];`，使 d=p1-p0，区间覆盖len。方格交长不同于R2023b规则：按半长(max(1,len)-1)/2构造半核，按像素中心垂距及端点修正赋权max(1+eps-|distance|,0)，镜像后按sum+eps*len*len归一化。"
q3="你的上一条单行建议不能直接使用：若把 d 改为 len*[cosd,sind]，后面的 p0=-len*d/2、p1=len*d/2 会把端点再乘一次len，得到len²尺度。保持单位方向d及原p0、p1不变，真正的单行修正应为 t = sort((q(k)+[-0.5 0.5]-p0(k))/(p1(k)-p0(k))); 。该改法已实际运行：LEN=9时0°、45°、90°尺寸分别1×9、7×7、9×1，均与内置同尺寸；但三个isequal仍均为0，45°最大逐元素误差0.057428348770532045，0°/90°为2.6367796834847468e-16。请重新核对，明确正确分母，并说明为何同尺寸仍不等于相同离散核。"
a3="`t`的正确分母是 `p1(k)-p0(k)`：`d`仍为单位向量，端点差对应长度 `len`，由此把线段投影参数归一到[0,1]。尺寸相同仅说明支持域相同；方格相交长度积分按穿格长度赋权，R2023b则按像素中心垂距和端点修正规则赋权后镜像归一。轴向轨迹两者近乎相同，45°权重分布不同，故isequal失败。"
records=[dict(round=1,question=q1,answer=a1,code=(root/'motion_psf_ai.m').read_text(encoding='utf-8')),dict(round=2,question=q2,answer=a2,note='本轮提出的修改会使端点多乘一次len，未采用；下一轮已核查纠正。'),dict(round=3,question=q3,answer=a3,note='答复中的“尺寸相同仅说明支持域相同”术语不准确；正文仅据尺寸判断矩阵外形，第四轮已要求纠正。')]
(root/'交互记录'/'实际问答.json').write_text(json.dumps({'date':'2026-11-05','model':'gpt-6-luna','reasoning_effort':'max','records':records},ensure_ascii=False,indent=2),encoding='utf-8')
cards=[dict(file='01_初版生成',title='初版生成',round=1,question_parts=[q1.split('给出可执行')[0]],answer_parts=[a1],footer='实际问答摘录 · AI 初版完整代码见报告第 2 节'),dict(file='02_差异分析',title='差异分析与纠正',round=3,question_parts=['该改法已实际运行：LEN=9时0°、45°、90°尺寸分别1×9、7×7、9×1，均与内置同尺寸；但三个isequal仍均为0，45°最大逐元素误差0.057428348770532045，0°/90°为2.6367796834847468e-16。','请重新核对，明确正确分母，并说明为何同尺寸仍不等于相同离散核。'],answer_parts=['`t`的正确分母是 `p1(k)-p0(k)`：`d`仍为单位向量，端点差对应长度 `len`，由此把线段投影参数归一到[0,1]。','方格相交长度积分按穿格长度赋权，R2023b则按像素中心垂距和端点修正规则赋权后镜像归一。'],footer='实际问答摘录 · 省略处以 […] 标示；实测数据见报告第 2 节')]
(root/'交互记录'/'截图内容.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved actual question/answer records and two excerpt definitions.')
