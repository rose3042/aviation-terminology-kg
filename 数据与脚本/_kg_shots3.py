# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.environ['TMP'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['TEMP'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['TMPDIR'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\.pw_browsers'

from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np

BASE = r'D:\360MoveData\Users\叶丽娜\Desktop\bert'
url = 'file:///D:/360MoveData/Users/叶丽娜/Desktop/bert/aviation_kg_dynamic_3d.html'
OUT = os.path.join(BASE, '_kg_shots')

def density(page):
    buf = page.screenshot()
    arr = np.array(Image.open(buf if isinstance(buf,str) else __import__('io').BytesIO(buf)).convert('RGB'))
    return (arr.mean(axis=2) < 240).mean()

def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path)
    arr = np.array(Image.open(path).convert('RGB'))
    sat = ((arr.max(axis=2) - arr.min(axis=2)) > 25)
    colored = (arr.mean(axis=2) < 240) & sat
    print(f'  {name}: 非白{(arr.mean(axis=2)<240).mean()*100:.1f}% 彩色{colored.mean()*100:.1f}%')
    return path

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=[
        '--enable-webgl', '--no-sandbox', '--disable-gpu-sandbox',
        '--use-gl=swiftshader-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])

    # 视图4：适度放大中心簇
    page = browser.new_page(viewport={'width':1400,'height':950})
    page.goto(url)
    page.wait_for_timeout(16000)
    page.mouse.move(640, 430)
    for _ in range(3):           # 只放大3档，避免过猛
        page.mouse.wheel(0, -350)
        page.wait_for_timeout(300)
    page.wait_for_timeout(2000)
    shot(page, 'kg_3d_view4_zoom.png')
    page.close()

    # 视图5：全新加载，隐藏图例的干净全貌
    page = browser.new_page(viewport={'width':1400,'height':950})
    page.goto(url)
    page.wait_for_timeout(16000)
    try:
        page.evaluate("""() => { document.querySelectorAll('.legend').forEach(el => el.style.display='none'); }""")
    except Exception:
        pass
    page.wait_for_timeout(1200)
    shot(page, 'kg_3d_view5_clean.png')
    page.close()

    browser.close()
print('完成')
