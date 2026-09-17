# -*- coding: utf-8 -*-
"""生成 裁决工具-分歧348.html：从 gold_争议清单.json 抽有分歧的句，做专家裁决界面。"""
import json

g = json.load(open('gold_争议清单.json', encoding='utf-8'))
sents = [x for x in g if x['disputed']]
data = [{
    'text': x['data']['text'], 'lang': x['data'].get('lang', ''),
    'domain': x['data'].get('domain', ''), 'source': x['data'].get('source', ''),
    'agreed': [[s['start'], s['end'], s['text']] for s in x['gold']],
    'disputed': [[d['annotator'], d['start'], d['end'], d['text']] for d in x['disputed']],
} for x in sents]
nd = sum(len(x['disputed']) for x in data)
print('有分歧句: %d, 分歧项: %d' % (len(data), nd))

HTML = '''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>术语分歧裁决</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;padding:12px;background:#f6f7f9;color:#222}
h1{font-size:17px;margin:6px 0}
.top{position:sticky;top:0;background:#fff;padding:8px 12px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.12);z-index:9;margin-bottom:10px}
.prog{font-size:13px;color:#555}
button{font-size:15px;border:none;border-radius:8px;padding:10px 14px;font-weight:600}
#up{width:100%;background:#0ea5e9;color:#fff;margin-top:8px;padding:13px}
.sentence{background:#fff;border-radius:10px;padding:12px 14px;margin:10px 0;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.head{font-size:12px;color:#888;margin-bottom:6px}
.text{font-size:15px;line-height:1.9;margin-bottom:8px}
mark{padding:1px 2px;border-radius:3px}
mark.gold{background:#d1fae5;color:#065f46}
mark.keep{background:#a7f3d0;color:#065f46}
mark.drop{background:#e5e7eb;color:#9ca3af;text-decoration:line-through}
.item{margin:8px 0;padding:8px 10px;border:1px solid #e5e7eb;border-radius:8px;background:#fafafa}
.tag{font-size:12px;padding:2px 7px;border-radius:5px;font-weight:700;margin-right:6px}
.tag.A{background:#dbeafe;color:#1e40af}
.tag.B{background:#fee2e2;color:#991b1b}
.sp{font-size:14px}
.btns{display:flex;gap:8px;margin-top:7px}
.btns button{flex:1;padding:9px}
.btnKeep{background:#16a34a;color:#fff}
.btnDrop{background:#f3f4f6;color:#555;border:1px solid #d1d5db}
.item.done-keep{background:#f0fdf4;border-color:#86efac}
.item.done-drop{background:#f3f4f6;border-color:#e5e7eb;opacity:.75}
.item.done-drop .sp{text-decoration:line-through;color:#9ca3af}
.quick{display:flex;gap:8px;margin-bottom:8px}
.quick button{flex:1;font-size:13px;padding:7px;background:#f3f4f6;border:1px solid #d1d5db;color:#333}
#msg{font-size:13px;margin-top:6px;color:#0f766e}
</style>
</head>
<body>
<div class="top">
  <h1>✍ 术语分歧裁决（专家：标注者A）</h1>
  <div class="prog" id="prog"></div>
  <button id="up">📤 上传裁决结果到研究者电脑</button>
  <div id="msg"></div>
</div>
<div id="main"></div>
<script>
const DATA = {{DATA}};
const KEY = 'aviation_verdict_348';
let DEC = {};
try{ DEC = JSON.parse(localStorage.getItem(KEY)) || {}; }catch(e){}
let decCount = 0;
function totalN(){ return DATA.reduce((a,x)=>a+x.disputed.length,0); }
function doneN(){ return Object.values(DEC).filter(v=>v==='keep'||v==='drop').length; }
function save(){ localStorage.setItem(KEY, JSON.stringify(DEC)); updateProg(); }
function updateProg(){ document.getElementById('prog').textContent = '已裁决 ' + doneN() + ' / ' + totalN() + ' 条'; }
function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function highlight(text, spans){
  const seg = spans.slice().sort((a,b)=>a[0]-b[0]);
  let html = '', pos = 0;
  seg.forEach(s=>{
    const cls = s[3]||'gold';
    if (s[0] > pos) html += esc(text.slice(pos, s[0]));
    html += '<mark class="'+cls+'">' + esc(text.slice(s[0], s[1])) + '</mark>';
    pos = Math.max(pos, s[1]);
  });
  html += esc(text.slice(pos));
  return html;
}
function render(){
  const main = document.getElementById('main');
  main.innerHTML = DATA.map((x,si)=>{
    // 保留的 disputed span 也高亮
    const keptSpans = x.disputed.filter((d,di)=>DEC[si+':'+di]==='keep').map(d=>[d[1],d[2],d[3],'keep']);
    const dropSpans = x.disputed.filter((d,di)=>DEC[si+':'+di]==='drop').map(d=>[d[1],d[2],d[3],'drop']);
    const gSpans = x.agreed.map(s=>[s[0],s[1],s[2],'gold']);
    const items = x.disputed.map((d,di)=>{
      const key = si+':'+di;
      const v = DEC[key];
      const cls = v==='keep' ? 'done-keep' : (v==='drop' ? 'done-drop' : '');
      return '<div class="item '+cls+'">'
        + '<span class="tag '+d[0]+'">标注者'+d[0]+'</span>'
        + '<span class="sp">「' + esc(d[3]) + '」</span>'
        + '<div class="btns">'
        + '<button class="btnKeep" onclick="vote(\''+key+'\',\'keep\')">✓ 保留为术语</button>'
        + '<button class="btnDrop" onclick="vote(\''+key+'\',\'drop\')">✗ 不标</button>'
        + '</div></div>';
    }).join('');
    return '<div class="sentence">'
      + '<div class="head">句 ' + (si+1) + '/' + DATA.length + ' · ' + x.lang + ' · ' + x.domain + '</div>'
      + '<div class="quick"><button onclick="quickAll('+si+',\'keep\')">本句全保留</button>'
      + '<button onclick="quickAll('+si+',\'drop\')">本句全不标</button></div>'
      + '<div class="text">' + highlight(x.text, keptSpans.concat(dropSpans, gSpans)) + '</div>'
      + items + '</div>';
  }).join('');
  updateProg();
}
function vote(key, v){ DEC[key]=v; save(); render(); }
function quickAll(si, v){ DATA[si].disputed.forEach((d,di)=>{ DEC[si+':'+di]=v; }); save(); render(); }
document.getElementById('up').onclick = async ()=>{
  const btn = document.getElementById('up');
  btn.textContent = '⏳ 上传中…'; btn.disabled = true;
  const state = DATA.map((x,si)=>({
    text: x.text, lang: x.lang, domain: x.domain, source: x.source,
    agreed: x.agreed,
    disputed: x.disputed,
    decisions: x.disputed.map((d,di)=>DEC[si+':'+di]||null)
  }));
  try{
    const res = await fetch('/verdict', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(state)});
    const j = await res.json();
    if (res.ok && j.ok){ document.getElementById('msg').textContent = '✅ 已上传！待研究者合并 gold'; btn.textContent = '✅ 已上传'; }
    else { document.getElementById('msg').textContent = '❌ 失败 HTTP ' + res.status; btn.textContent = '📤 上传裁决结果到研究者电脑'; btn.disabled = false; }
  }catch(e){
    document.getElementById('msg').textContent = '❌ 连接失败：' + e.message;
    btn.textContent = '📤 上传裁决结果到研究者电脑'; btn.disabled = false;
  }
};
render();
</script>
</body>
</html>'''

out = HTML.replace('{{DATA}}', json.dumps(data, ensure_ascii=False))
open('裁决工具-分歧348.html', 'w', encoding='utf-8').write(out)
print('✅ 已生成 裁决工具-分歧348.html（%d 句，%d 条分歧）' % (len(data), nd))
