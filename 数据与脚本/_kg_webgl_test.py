# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.environ['TMP'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['TEMP'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['TMPDIR'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\_tmp_video'
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = r'D:\360MoveData\Users\叶丽娜\Desktop\bert\.pw_browsers'

from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image
import io

BASE = r'D:\360MoveData\Users\叶丽娜\Desktop\bert'
url = 'file:///D:/360MoveData/Users/叶丽娜/Desktop/bert/aviation_kg_dynamic_3d.html'

COMBOS = {
    'A_angle_swiftshader': ['--enable-webgl', '--no-sandbox', '--disable-gpu-sandbox',
        '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
    'B_swiftshader_webgl': ['--enable-webgl', '--no-sandbox', '--use-gl=swiftshader-webgl',
        '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
    'C_angle_d3d11': ['--enable-webgl', '--no-sandbox', '--use-gl=angle', '--use-angle=d3d11', '--ignore-gpu-blocklist'],
    'D_default': ['--enable-webgl', '--no-sandbox'],
}

def scene_density(page):
    buf = page.screenshot(clip={'x':300,'y':200,'width':680,'height':520})
    im = Image.open(io.BytesIO(buf)).convert('RGB')
    arr = np.array(im)
    return (arr.mean(axis=2) < 240).mean()

with sync_playwright() as p:
    for name, args in COMBOS.items():
        try:
            browser = p.chromium.launch(headless=True, args=args)
            page = browser.new_page(viewport={'width':1280,'height':900})
            page.goto(url)
            page.wait_for_timeout(10000)
            info = page.evaluate("""() => {
                const cs = [...document.querySelectorAll('canvas')];
                return cs.map(c => {
                    const gl = c.getContext('webgl') || c.getContext('experimental-webgl');
                    return {w:c.width, h:c.height, webgl:!!gl};
                });
            }""")
            d = scene_density(page)
            print(f'[{name}] canvas={info} 场景区非白占比={d:.1%}')
            browser.close()
        except Exception as e:
            print(f'[{name}] 异常: {str(e)[:120]}')
            try: browser.close()
            except: pass
