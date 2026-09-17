# -*- coding: utf-8 -*-
"""Playwright 打开 3D 航空术语知识图谱，截取多个视角（swiftshader-webgl 参数已验证可用）。"""
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
import io

BASE = r'D:\360MoveData\Users\叶丽娜\Desktop\bert'
url = 'file:///D:/360MoveData/Users/叶丽娜/Desktop/bert/aviation_kg_dynamic_3d.html'
OUT = os.path.join(BASE, '_kg_shots')
os.makedirs(OUT, exist_ok=True)

def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path)
    im = Image.open(path).convert('RGB')
    arr = np.array(im)
    d = (arr.mean(axis=2) < 240).mean()
    print(f'  {name}: 全页非白占比 {d:.1%}')
    return path

def drag(page, dx, dy, steps=30):
    page.mouse.move(640, 430)
    page.mouse.down()
    for i in range(1, steps + 1):
        page.mouse.move(640 + dx * i // steps, 430 + dy * i // steps, steps=2)
        page.wait_for_timeout(20)
    page.mouse.up()
    page.wait_for_timeout(1500)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=[
        '--enable-webgl', '--no-sandbox', '--disable-gpu-sandbox',
        '--use-gl=swiftshader-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    page = browser.new_page(viewport={'width': 1400, 'height': 950})
    page.goto(url)
    page.wait_for_timeout(16000)
    print('已加载，开始截图')

    # 1) 默认视角
    shot(page, 'kg_3d_view1_default.png')

    # 2) 水平旋转 ~120°
    drag(page, 320, 0)
    shot(page, 'kg_3d_view2_rotated.png')

    # 3) 抬高视角（垂直拖）
    drag(page, 0, -300)
    shot(page, 'kg_3d_view3_elevated.png')

    # 4) 滚轮放大中心簇（指针需悬停在场景上）
    page.mouse.move(640, 430)
    for _ in range(8):
        page.mouse.wheel(0, -350)
        page.wait_for_timeout(250)
    page.wait_for_timeout(2000)
    shot(page, 'kg_3d_view4_zoom.png')

    # 5) 缩回全貌 + 隐藏图例（干净版）
    page.mouse.move(640, 430)
    for _ in range(10):
        page.mouse.wheel(0, 350)
        page.wait_for_timeout(150)
    page.wait_for_timeout(1500)
    try:
        page.evaluate("""() => { document.querySelectorAll('.legend').forEach(el => el.style.display='none'); }""")
    except Exception:
        pass
    page.wait_for_timeout(1200)
    shot(page, 'kg_3d_view5_clean.png')

    browser.close()
print('完成 →', OUT)
