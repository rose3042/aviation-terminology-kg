# -*- coding: utf-8 -*-
"""KG 3D 高清重拍：viewport 1400x950 + device_scale_factor=2（WebGL 正常且 2x 分辨率）。
HTML 中文（标题/悬停提示）替换为英文。Plotly relayout 相机定位 6 视角。
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.environ['TMP'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['TEMP'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['TMPDIR'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\.pw_browsers'
os.makedirs(os.environ['TMP'], exist_ok=True)

BASE = r'D:\360MoveData\Users\叶丽娜\Desktop\bert'
SRC = os.path.join(BASE, 'aviation_kg_dynamic_3d.html')
DST = os.path.join(BASE, 'aviation_kg_dynamic_3d_EN.html')

def esc(s):
    return ''.join('\\u%04x' % ord(c) for c in s)

t = open(SRC, encoding='utf-8').read()
# 1) 字面替换（兜底，若 HTML 中标题为字面 UTF-8）
t = t.replace('✈️  航空术语知识图谱（2184节点 · 2475关系）',
              '✈️  Aviation Terminology Knowledge Graph (2,184 nodes · 2,475 relations)')
# 2) 转义层替换（HTML 实际是 \uXXXX 存储）
repl = [
    ('航空术语知识图谱', 'Aviation Terminology Knowledge Graph'),
    ('节点', 'nodes'), ('关系', 'relations'),
    ('核心枢纽', 'hub'), ('重要术语', 'important'), ('一般术语', 'general'),
    ('连接度', 'degree'),
]
for zh, en in repl:
    ezh = esc(zh)
    n = t.count(ezh)
    t = t.replace(ezh, esc(en))
    if n:
        print(f'  [esc] {zh} -> {en}  ×{n}')
# 3) 字面中文兜底
for zh, en in repl:
    n = t.count(zh)
    if n and zh != '连接度':
        t = t.replace(zh, en)
        print(f'  [raw] {zh} -> {en}  ×{n}')
open(DST, 'w', encoding='utf-8').write(t)
print('已写', DST)

from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np

OUT = os.path.join(BASE, '_kg_shots_hi')
os.makedirs(OUT, exist_ok=True)
url = 'file:///' + DST.replace('\\', '/')

def shot(page, name, cam=None, hide_legend=False, wait=2000):
    if cam is not None:
        try:
            page.evaluate("""(eye) => {
                Plotly.relayout(document.querySelector('.plotly-graph-div'), {'scene.camera.eye': eye});
            }""", cam)
        except Exception as e:
            print('  relayout失败:', str(e)[:100])
    if hide_legend:
        try:
            page.evaluate("""() => {
                document.querySelectorAll('.legend .traces').forEach(el => el.style.display = 'none');
            }""")
        except Exception:
            pass
    page.wait_for_timeout(wait)
    path = os.path.join(OUT, name)
    page.screenshot(path=path)
    a = np.array(Image.open(path).convert('RGB'))
    print(f'  {name}: 非白{(a.mean(axis=2)<240).mean()*100:.1f}%')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=[
        '--enable-webgl', '--no-sandbox', '--disable-gpu-sandbox',
        '--use-gl=swiftshader-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    ctx = browser.new_context(viewport={'width': 1400, 'height': 950}, device_scale_factor=2)
    page = ctx.new_page()
    page.goto(url)
    page.wait_for_timeout(16000)
    print('WebGL 加载完成')
    shot(page, 'kg_3d_view1_default.png')
    shot(page, 'kg_3d_view2_rotated.png', cam={'x': -2.05, 'y': 0.55, 'z': 1.5})
    shot(page, 'kg_3d_view3_elevated.png', cam={'x': 1.5, 'y': 1.5, 'z': 3.4})
    shot(page, 'kg_3d_view4_zoom.png', cam={'x': 0.45, 'y': 0.85, 'z': 0.55})
    shot(page, 'kg_3d_view5_clean.png', cam={'x': 1.5, 'y': 1.5, 'z': 1.5}, hide_legend=True)
    shot(page, 'kg_3d_view5_closeup.png', cam={'x': 0.2, 'y': 0.45, 'z': 0.35})
    browser.close()
print('完成 →', OUT)
