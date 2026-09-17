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
    page = browser.new_page(viewport={'width':1400,'height':950})
    page.goto(url)
    page.wait_for_timeout(16000)

    # 用 relayout 设定相机：拉近（缩放）+ 换角度
    try:
        page.evaluate("""() => {
            Plotly.relayout(document.querySelector('.plotly-graph-div'), {
                'scene.camera.eye': {x: 0.45, y: 0.85, z: 0.55},
                'scene.camera.up':  {x: 0, y: 0, z: 1}
            });
        }""")
        page.wait_for_timeout(2500)
        shot(page, 'kg_3d_view4_zoom.png')
    except Exception as e:
        print('relayout失败:', str(e)[:120])
        shot(page, 'kg_3d_view4_zoom.png')

    # 再设一个更近的特写角度
    try:
        page.evaluate("""() => {
            Plotly.relayout(document.querySelector('.plotly-graph-div'), {
                'scene.camera.eye': {x: 0.2, y: 0.45, z: 0.35}
            });
        }""")
        page.wait_for_timeout(2500)
        shot(page, 'kg_3d_view5_closeup.png')
    except Exception as e:
        print('relayout2失败:', str(e)[:120])

    browser.close()
print('完成')
