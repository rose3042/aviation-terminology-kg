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
BASE = r'D:\360MoveData\Users\叶丽娜\Desktop\bert'
url_orig = 'file:///D:/360MoveData/Users/叶丽娜/Desktop/bert/aviation_kg_dynamic_3d.html'
url_en = 'file:///D:/360MoveData/Users/叶丽娜/Desktop/bert/aviation_kg_dynamic_3d_EN.html'
def probe(url, name, ctx_kw, wait=18000):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            '--enable-webgl', '--no-sandbox', '--disable-gpu-sandbox',
            '--use-gl=swiftshader-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = browser.new_context(**ctx_kw)
        page = ctx.new_page()
        page.goto(url)
        page.wait_for_timeout(wait)
        path = f'_kg_diag_{name}.png'
        page.screenshot(path=path)
        a = np.array(Image.open(path).convert('RGB'))
        print(f'{name}: 非白{(a.mean(axis=2)<240).mean()*100:.2f}%')
        # webgl 检查
        try:
            gl = page.evaluate("() => { const c=document.createElement('canvas'); return !!(c.getContext('webgl')); }")
            print(f'  webgl supported: {gl}')
        except Exception as e:
            print('  webgl check err', str(e)[:80])
        browser.close()
probe(url_orig, 'A_orig_1400', {'viewport': {'width':1400,'height':950}})
probe(url_en, 'B_en_1400x2', {'viewport': {'width':1400,'height':950}, 'device_scale_factor': 2})
