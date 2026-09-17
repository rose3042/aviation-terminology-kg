# -*- coding: utf-8 -*-
"""Playwright 打开 3D 航空术语知识图谱，截取多个视角的图。"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

os.environ['TMP'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['TEMP'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['TMPDIR'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\.pw_browsers'
os.makedirs(os.environ['TMP'], exist_ok=True)

from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np

BASE = r'D:\360MoveData\Users\叶丽娜\Desktop\bert'
html = os.path.join(BASE, 'aviation_kg_dynamic_3d.html')
url = 'file:///' + html.replace('\\', '/')
OUT = os.path.join(BASE, '_kg_shots')
os.makedirs(OUT, exist_ok=True)

def report(path):
    im = Image.open(path).convert('RGB')
    arr = np.array(im)
    nonwhite = (arr.mean(axis=2) < 240).mean()
    print(f'  {os.path.basename(path)}: {im.size} 非白像素占比 {nonwhite:.1%}')

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--enable-webgl', '--no-sandbox', '--disable-gpu-sandbox',
              '--use-gl=swiftshader', '--enable-unsafe-swiftshader'],
    )
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    page.goto(url)
    # 等 WebGL 场景渲染完成
    page.wait_for_timeout(15000)
    print('已加载，开始截图')

    # 视图1：默认视角
    p1 = os.path.join(OUT, 'kg_3d_view1_default.png')
    page.screenshot(path=p1)
    report(p1)

    # 视图2：水平拖拽旋转 ~90°
    page.mouse.move(640, 480)
    page.mouse.down()
    for x in range(0, 260, 20):
        page.mouse.move(640 + x, 480, steps=2)
        page.wait_for_timeout(30)
    page.mouse.up()
    page.wait_for_timeout(2500)
    p2 = os.path.join(OUT, 'kg_3d_view2_rotated.png')
    page.screenshot(path=p2)
    report(p2)

    # 视图3：再垂直旋转（抬高视角）
    page.mouse.move(640, 480)
    page.mouse.down()
    for y in range(0, 220, 20):
        page.mouse.move(640, 480 - y, steps=2)
        page.wait_for_timeout(30)
    page.mouse.up()
    page.wait_for_timeout(2500)
    p3 = os.path.join(OUT, 'kg_3d_view3_elevated.png')
    page.screenshot(path=p3)
    report(p3)

    # 视图4：滚轮放大中心簇
    for _ in range(6):
        page.mouse.wheel(0, -400)
        page.wait_for_timeout(200)
    page.wait_for_timeout(2500)
    p4 = os.path.join(OUT, 'kg_3d_view4_zoom.png')
    page.screenshot(path=p4)
    report(p4)

    # 视图5：整体缩回 + 隐藏图例（更干净的全貌）
    for _ in range(10):
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(150)
    page.wait_for_timeout(2000)
    try:
        page.evaluate("""() => {
            document.querySelectorAll('.legend .traces').forEach(el => el.style.display = 'none');
        }""")
    except Exception as e:
        print('图例隐藏失败(不影响):', e)
    page.wait_for_timeout(1500)
    p5 = os.path.join(OUT, 'kg_3d_view5_clean.png')
    page.screenshot(path=p5)
    report(p5)

    browser.close()
print('全部截图完成 →', OUT)
