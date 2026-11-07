# -*- coding: utf-8 -*-
from pathlib import Path, PurePosixPath
import csv
import hashlib
import json
import re
import shutil
import zipfile
import fitz

root=Path(__file__).resolve().parents[1]
pdf=root/'output/pdf/运动模糊PSF复现报告.pdf'
doc=fitz.open(pdf)
assert len(doc)==5
text='\n'.join(page.get_text() for page in doc)
for required in ['蔡斌','1024001338','104/104','385/385','1000/1000','2/2','1489']:
    assert required in text,required
for term in ['待补充','占位','TODO','TBD','遗憾的是','效果有限','后续补充','建议再跑']:
    assert term not in text,term
assert len(doc[4].get_images(full=True))==3
for i,name in [(1,'motion_psf_ai.m'),(2,'motion_psf.m')]:
    page_text=doc[i].get_text()
    block=page_text[page_text.index('function'):page_text.rfind('end')+3]
    extracted='\n'.join(line for line in block.splitlines() if not re.fullmatch(r'\d+',line.strip()))
    original=(root/name).read_text(encoding='utf-8')
    assert re.sub(r'\s+','',extracted)==re.sub(r'\s+','',original),name
for page in doc:
    for block in page.get_text('blocks'):
        assert block[0]>=0 and block[1]>=0 and block[2]<=page.rect.width+0.5 and block[3]<=page.rect.height+0.5
fonts={font[0] for page in doc for font in page.get_fonts(full=True)}
assert all(len(doc.extract_font(ref)[3])>0 for ref in fonts)
log=(root/'tmp/latex/运动模糊PSF报告.log').read_text(encoding='utf-8',errors='replace')
assert not re.search(r'^(Overfull|Underfull|LaTeX Warning|Package .* Warning)',log,re.M)
rows=list(csv.DictReader((root/'results/adversarial_cases.csv').open(encoding='utf-8')))
assert len(rows)==1385 and all(float(r['max_abs_error'])==0 for r in rows)
assert len({float(r['THETA']) for r in rows if r['group']=='boundary'})==35
assert len({float(r['LEN']) for r in rows if r['group']=='boundary'})==11
assert 'All 4 plausible faults were detected.' in (root/'results/test_sensitivity_log.txt').read_text()
for name in ['report_extracted.txt','final_pdf_text.txt']:
    (root/'results'/name).write_text(text,encoding='utf-8')

delivery=root/'提交'
delivery.mkdir(exist_ok=True)
final=delivery/'运动模糊PSF报告_数学jd2401_蔡斌_1024001338.pdf'
shutil.copy2(pdf,final)
files=[root/n for n in ['运动模糊PSF报告.tex','motion_psf.m','motion_psf_ai.m',
    'motion_psf_overlap.m','test_motion_psf.m','capture_results.m','audit_motion_psf.m',
    'audit_test_sensitivity.m','compare_ai_initial.m','compare_overlap.m',
    'compile_report.ps1','build_report.py','render_dialogue.py','README.md',
    'AI交互过程.md','对抗性审计记录.txt','截图/psf_kernels.png']]
files += [root/'results'/n for n in ['initial_comparison.tex','matlab_test_log.txt',
    'ai_initial_test_log.txt','overlap_test_log.txt','adversarial_test_log.txt',
    'adversarial_cases.csv','test_sensitivity_log.txt']]
files += list((root/'交互记录').glob('*'))
assert all(p.is_file() for p in files)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=dict(pdf_pages=5,pdf_sha256=sha(final),case_count=1489,default_calls=2,
    deliberate_faults_detected=4,boundary_angles_distinct=35,
    text_scan='passed',fonts_embedded=len(fonts),pdf_code_matches_source=True,
    revision='2026-11-05 expression and layout revision',
    files={p.relative_to(root).as_posix():sha(p) for p in files})
manifest_file=root/'results/final_verification.json'
manifest_file.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
archive=delivery/'运动模糊PSF作业_源码与记录.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files+[manifest_file]: z.write(p,p.relative_to(root).as_posix())
    z.write(final,final.name)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
    extract=root/'tmp/submission_package_check'
    for name in z.namelist():
        p=PurePosixPath(name)
        assert not p.is_absolute() and '..' not in p.parts
    z.extractall(extract)
print(json.dumps({'pdf':str(final),'zip':str(archive),'pages':5,'archive_files':len(files)+2,
    'pdf_bytes':final.stat().st_size,'zip_bytes':archive.stat().st_size},ensure_ascii=False))
