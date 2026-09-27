#!/usr/bin/env python3
"""Extract test-video frames and serve a fast local YOLO annotation UI.

This tool uses only Python's standard library plus the system ffmpeg command.
Labels are written immediately under data/datasets_A/test_ground_truth/labels/test.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import shutil
import subprocess
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIDEOS = ROOT / "data/videos_A/test"
DEFAULT_DATASET = ROOT / "data/datasets_A/test_ground_truth"
CLASSES = ["coke_zero", "think_protein_bar", "ziploc_box"]


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>商品数据标注 / Product Annotation</title>
  <style>
    :root {
      --ink: #17212b; --muted: #65707c; --line: #d9dee5; --paper: #f4f6f8;
      --panel: #ffffff; --navy: #17365d; --blue: #2367d1; --green: #138a5b;
      --orange: #e58320; --red: #d94747; --shadow: 0 10px 34px rgba(31,42,55,.10);
    }
    * { box-sizing: border-box; }
    body { margin: 0; color: var(--ink); background: var(--paper); font: 15px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    header { height: 64px; background: var(--navy); color: white; display: flex; align-items: center; gap: 18px; padding: 0 22px; }
    header h1 { margin: 0; font-size: 19px; letter-spacing: .2px; }
    .progress-wrap { margin-left: auto; min-width: 260px; }
    .progress-text { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 5px; opacity: .92; }
    .track { height: 7px; background: rgba(255,255,255,.22); border-radius: 20px; overflow: hidden; }
    .fill { height: 100%; width: 0; background: #6fe0aa; transition: width .2s; }
    .rules { margin: 12px 16px 0; padding: 10px 14px; background: #eef5ff; border: 1px solid #bdd3f2; border-radius: 10px; }
    .rules summary { cursor: pointer; font-weight: 750; color: var(--navy); }
    .rules ol { margin: 8px 0 0 20px; padding: 0; display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 5px 28px; font-size: 12.5px; color: #3d4b5b; }
    main { display: grid; grid-template-columns: minmax(0,1fr) 330px; gap: 16px; padding: 12px 16px 16px; height: calc(100vh - 174px); min-height: 540px; }
    .workspace, aside { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; box-shadow: var(--shadow); }
    .workspace { min-width: 0; display: flex; flex-direction: column; overflow: hidden; }
    .toolbar { display: flex; align-items: center; gap: 9px; padding: 10px 12px; border-bottom: 1px solid var(--line); }
    button, select { height: 36px; border: 1px solid #cbd2da; border-radius: 7px; background: white; color: var(--ink); padding: 0 12px; font-weight: 600; }
    button { cursor: pointer; }
    button:hover { border-color: #8d99a7; background: #f8fafc; }
    button.primary { border-color: var(--blue); background: var(--blue); color: white; }
    button.empty { border-color: #aab3bd; background: #edf1f5; }
    .meta { margin-left: auto; color: var(--muted); font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .stage { position: relative; flex: 1; min-height: 0; display: grid; place-items: center; padding: 10px; background: #252b32; overflow: hidden; }
    canvas { display: block; max-width: 100%; max-height: 100%; width: auto; height: auto; cursor: crosshair; box-shadow: 0 2px 14px rgba(0,0,0,.35); touch-action: none; }
    .footer { display: flex; align-items: center; justify-content: space-between; min-height: 43px; padding: 7px 12px; border-top: 1px solid var(--line); color: var(--muted); font-size: 13px; }
    .saved { color: var(--green); font-weight: 700; }
    aside { padding: 15px; overflow-y: auto; }
    aside h2 { margin: 0 0 10px; font-size: 16px; }
    .class-btn { width: 100%; height: 47px; display: flex; align-items: center; gap: 10px; margin: 8px 0; text-align: left; }
    .class-btn.active { outline: 3px solid rgba(35,103,209,.20); border-color: var(--blue); background: #eef5ff; }
    .key { width: 24px; height: 24px; display: grid; place-items: center; color: white; border-radius: 5px; font-size: 12px; }
    .c0 { background: var(--blue); } .c1 { background: var(--green); } .c2 { background: var(--orange); }
    .notice { margin: 14px 0; padding: 10px 11px; background: #fff7e8; border: 1px solid #f2d39d; border-radius: 8px; font-size: 13px; }
    .box-row { display: flex; align-items: center; gap: 8px; margin: 7px 0; padding: 8px; border: 1px solid var(--line); border-radius: 7px; cursor: pointer; }
    .box-row.selected { border-color: var(--blue); background: #eef5ff; }
    .box-row button { margin-left: auto; height: 27px; padding: 0 8px; color: var(--red); }
    .shortcuts { margin-top: 16px; border-top: 1px solid var(--line); padding-top: 12px; color: var(--muted); font-size: 12px; }
    .shortcuts div { display: flex; justify-content: space-between; margin: 5px 0; }
    kbd { border: 1px solid #c8ced6; background: #f8fafc; border-radius: 4px; padding: 1px 6px; color: var(--ink); }
    @media (max-width: 900px) { .rules ol { grid-template-columns: 1fr; } main { grid-template-columns: 1fr; height: auto; } .workspace { height: 72vh; } aside { min-height: 300px; } }
  </style>
</head>
<body>
  <header>
    <h1>商品数据标注 / Product Annotation</h1>
    <div class="progress-wrap">
      <div class="progress-text"><span id="progressLabel">加载中 / Loading…</span><span id="progressPct">0%</span></div>
      <div class="track"><div class="fill" id="progressFill"></div></div>
    </div>
  </header>
  <details class="rules" open>
    <summary>标注规则 / Annotation Rules</summary>
    <ol>
      <li>只标注完全匹配的目标商品；相似品牌或包装不要标。 / Label only the exact target SKUs; do not label similar products.</li>
      <li>标出画面中每一个可辨认的目标，包括货架或背景中的目标。 / Label every visible target instance, including items on shelves or in the background.</li>
      <li>边界框紧贴商品包装，不包含手、阴影、货架或旁边商品。 / Draw a tight box around the package; exclude hands, shadows, shelves, and neighbors.</li>
      <li>部分遮挡时，只在类别与位置仍能可靠判断时标注；可见不足约 15% 或无法定位时不标。 / For occlusion, label only when class and location remain reliable; skip if less than ~15% is visible or localization is uncertain.</li>
      <li>商品被画面边缘截断时，边界框止于图像边缘。 / If truncated by the image boundary, stop the box at the image edge.</li>
      <li>仅当画面中没有任何目标商品时使用“标记为空”。 / Use “Mark empty” only when no target SKU is present.</li>
    </ol>
  </details>
  <main>
    <section class="workspace">
      <div class="toolbar">
        <button id="prevBtn">← 上一张 / Previous</button>
        <button id="nextBtn">下一张 / Next →</button>
        <select id="videoFilter" aria-label="按视频筛选 / Filter by video"><option value="">全部视频 / All videos</option></select>
        <div class="meta" id="frameMeta"></div>
      </div>
      <div class="stage"><canvas id="canvas"></canvas></div>
      <div class="footer"><span>紧贴每个目标商品拖动画框。 / Draw tightly around every target product.</span><span id="saveState"></span></div>
    </section>
    <aside>
      <h2>1. 选择类别 / Choose class</h2>
      <div id="classButtons"></div>
      <div class="notice"><strong>重要 / Important:</strong> 同一商品出现多个实例时，每一个都要分别标注。 / Label every instance separately when the same product appears more than once.</div>
      <h2>2. 当前画框 / Boxes in this frame</h2>
      <div id="boxList"></div>
      <button id="undoBtn">撤销上一个 / Undo last</button>
      <button id="clearBtn">清除全部 / Clear boxes</button>
      <button id="copyBtn">复制上一帧 / Copy previous</button>
      <h2 style="margin-top:18px">3. 保存 / Save</h2>
      <button class="primary" id="saveBtn" style="width:100%;margin-bottom:8px">保存并下一张 / Save & next</button>
      <button class="empty" id="emptyBtn" style="width:100%">标记为空并下一张 / Mark empty & next</button>
      <div class="shortcuts">
        <div><span>选择类别 / Class</span><span id="classShortcuts"></span></div>
        <div><span>保存并下一张 / Save</span><kbd>Enter</kbd></div>
        <div><span>标记为空 / Empty</span><kbd>E</kbd></div>
        <div><span>撤销 / Undo</span><kbd>U</kbd></div>
        <div><span>复制上一帧 / Copy previous</span><kbd>C</kbd></div>
        <div><span>删除选中 / Delete</span><kbd>Delete</kbd></div>
        <div><span>上一张/下一张 / Prev/next</span><span><kbd>←</kbd> <kbd>→</kbd></span></div>
      </div>
    </aside>
  </main>
<script>
const colors = ['#2367d1','#138a5b','#e58320','#d94747','#6f55c8','#c33784'];
const names = ['coke_zero','think_protein_bar','ziploc_box'];
const displayNames = {
  coke_zero:'Coke Zero / 无糖可乐', oreo:'Oreo / 奥利奥', goodwipes:'Goodwipes / 湿巾',
  cheetos:'Cheetos / 奇多', sprite:'Sprite / 雪碧', sour_patch_kids:'Sour Patch Kids / 酸味软糖'
};
const canvas = document.getElementById('canvas'), ctx = canvas.getContext('2d');
const img = new Image();
let manifest=[], filtered=[], index=0, boxes=[], selectedClass=0, selectedBox=-1, drag=null;

const classButtons=document.getElementById('classButtons');
names.forEach((name,i)=>{
  const button=document.createElement('button');
  button.className='class-btn'+(i===0?' active':''); button.dataset.class=i;
  button.innerHTML=`<span class="key" style="background:${colors[i%colors.length]}">${i+1}</span>${displayNames[name]||name}`;
  button.onclick=()=>selectClass(i); classButtons.appendChild(button);
});
document.getElementById('classShortcuts').innerHTML=names.map((_,i)=>`<kbd>${i+1}</kbd>`).join(' ');

function current(){ return filtered[index]; }
function setStatus(text, saved=false){ const el=document.getElementById('saveState'); el.textContent=text; el.className=saved?'saved':''; }
function updateProgress(){
  const done=manifest.filter(x=>x.reviewed).length, total=manifest.length, pct=total?Math.round(done*100/total):0;
  document.getElementById('progressLabel').textContent=`已完成 / Reviewed: ${done} / ${total}`;
  document.getElementById('progressPct').textContent=pct+'%';
  document.getElementById('progressFill').style.width=pct+'%';
}
function draw(){
  if(!img.complete) return;
  ctx.clearRect(0,0,canvas.width,canvas.height); ctx.drawImage(img,0,0);
  boxes.forEach((b,i)=>{
    const x=(b.cx-b.w/2)*canvas.width, y=(b.cy-b.h/2)*canvas.height;
    const w=b.w*canvas.width, h=b.h*canvas.height;
    ctx.strokeStyle=colors[b.class_id]; ctx.lineWidth=i===selectedBox?6:4; ctx.strokeRect(x,y,w,h);
    ctx.font='bold 22px sans-serif'; const label=names[b.class_id]; const tw=ctx.measureText(label).width+12;
    ctx.fillStyle=colors[b.class_id]; ctx.fillRect(x,Math.max(0,y-29),tw,29);
    ctx.fillStyle='white'; ctx.fillText(label,x+6,Math.max(22,y-7));
  });
  if(drag){ ctx.setLineDash([10,7]); ctx.strokeStyle=colors[selectedClass]; ctx.lineWidth=4; ctx.strokeRect(drag.x,drag.y,drag.x2-drag.x,drag.y2-drag.y); ctx.setLineDash([]); }
}
function renderBoxList(){
  const host=document.getElementById('boxList'); host.innerHTML='';
  if(!boxes.length){ host.innerHTML='<div style="color:#7a8490;margin:8px 0 12px">还没有画框 / No boxes yet</div>'; return; }
  boxes.forEach((b,i)=>{
    const row=document.createElement('div'); row.className='box-row'+(i===selectedBox?' selected':'');
    row.innerHTML=`<span class="key" style="background:${colors[b.class_id%colors.length]}">${b.class_id+1}</span><span>${displayNames[names[b.class_id]]||names[b.class_id]}</span><button>删除 / Delete</button>`;
    row.onclick=()=>{selectedBox=i;renderBoxList();draw()};
    row.querySelector('button').onclick=(e)=>{e.stopPropagation();boxes.splice(i,1);selectedBox=-1;renderBoxList();draw();setStatus('未保存 / Unsaved')};
    host.appendChild(row);
  });
}
async function loadItem(){
  const item=current(); if(!item) return;
  setStatus('加载中 / Loading…'); selectedBox=-1;
  const response=await fetch('/api/labels/'+encodeURIComponent(item.id)); boxes=await response.json();
  img.onload=()=>{canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;draw()};
  img.src='/image/'+encodeURIComponent(item.id)+'?v='+Date.now();
  document.getElementById('frameMeta').textContent=`${item.video} · ${item.time_s.toFixed(1)}s · frame ${index+1}/${filtered.length}`;
  setStatus(item.reviewed?'已保存 / Saved':'未标注 / Not reviewed',item.reviewed); renderBoxList();
}
async function saveAndNext(empty=false){
  if(!current()) return; if(empty) boxes=[];
  setStatus('保存中 / Saving…');
  const response=await fetch('/api/labels/'+encodeURIComponent(current().id),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({boxes})});
  if(!response.ok){setStatus('保存失败 / Save failed');return}
  current().reviewed=true; const original=manifest.find(x=>x.id===current().id); if(original) original.reviewed=true;
  updateProgress(); setStatus('已保存 / Saved',true); if(index<filtered.length-1){index++;await loadItem()}
}
function changeIndex(delta){ index=Math.max(0,Math.min(filtered.length-1,index+delta)); loadItem(); }
function canvasPoint(event){const r=canvas.getBoundingClientRect();return{x:(event.clientX-r.left)*canvas.width/r.width,y:(event.clientY-r.top)*canvas.height/r.height}}
function hitBox(p){for(let i=boxes.length-1;i>=0;i--){const b=boxes[i],x=(b.cx-b.w/2)*canvas.width,y=(b.cy-b.h/2)*canvas.height,w=b.w*canvas.width,h=b.h*canvas.height;if(p.x>=x&&p.x<=x+w&&p.y>=y&&p.y<=y+h)return i}return -1}
canvas.onpointerdown=e=>{const p=canvasPoint(e),hit=hitBox(p);if(hit>=0){selectedBox=hit;renderBoxList();draw();return}selectedBox=-1;drag={x:p.x,y:p.y,x2:p.x,y2:p.y};canvas.setPointerCapture(e.pointerId)};
canvas.onpointermove=e=>{if(!drag)return;const p=canvasPoint(e);drag.x2=Math.max(0,Math.min(canvas.width,p.x));drag.y2=Math.max(0,Math.min(canvas.height,p.y));draw()};
canvas.onpointerup=e=>{if(!drag)return;const x1=Math.min(drag.x,drag.x2),x2=Math.max(drag.x,drag.x2),y1=Math.min(drag.y,drag.y2),y2=Math.max(drag.y,drag.y2);drag=null;if(x2-x1>8&&y2-y1>8){boxes.push({class_id:selectedClass,cx:(x1+x2)/(2*canvas.width),cy:(y1+y2)/(2*canvas.height),w:(x2-x1)/canvas.width,h:(y2-y1)/canvas.height});selectedBox=boxes.length-1;setStatus('未保存 / Unsaved')}renderBoxList();draw()};
function selectClass(c){selectedClass=c;document.querySelectorAll('.class-btn').forEach(b=>b.classList.toggle('active',+b.dataset.class===c))}
document.getElementById('prevBtn').onclick=()=>changeIndex(-1); document.getElementById('nextBtn').onclick=()=>changeIndex(1);
document.getElementById('saveBtn').onclick=()=>saveAndNext(false); document.getElementById('emptyBtn').onclick=()=>saveAndNext(true);
document.getElementById('undoBtn').onclick=()=>{boxes.pop();selectedBox=-1;renderBoxList();draw();setStatus('未保存 / Unsaved')};
document.getElementById('clearBtn').onclick=()=>{boxes=[];selectedBox=-1;renderBoxList();draw();setStatus('未保存 / Unsaved')};
document.getElementById('copyBtn').onclick=async()=>{if(index===0)return;const prior=filtered[index-1];if(prior.video!==current().video){setStatus('上一帧属于另一个视频 / Previous frame is another video');return}boxes=await (await fetch('/api/labels/'+encodeURIComponent(prior.id))).json();selectedBox=-1;renderBoxList();draw();setStatus('已复制，请调整后保存 / Copied — adjust then save')};
document.getElementById('videoFilter').onchange=e=>{filtered=e.target.value?manifest.filter(x=>x.video===e.target.value):manifest;index=0;loadItem()};
window.onkeydown=e=>{if(/^\d$/.test(e.key)&&+e.key>=1&&+e.key<=names.length)selectClass(+e.key-1);else if(e.key==='Enter')saveAndNext(false);else if(e.key.toLowerCase()==='e')saveAndNext(true);else if(e.key.toLowerCase()==='u'){document.getElementById('undoBtn').click()}else if(e.key.toLowerCase()==='c'){document.getElementById('copyBtn').click()}else if(e.key==='Delete'&&selectedBox>=0){boxes.splice(selectedBox,1);selectedBox=-1;renderBoxList();draw();setStatus('未保存 / Unsaved')}else if(e.key==='ArrowLeft')changeIndex(-1);else if(e.key==='ArrowRight')changeIndex(1)};
(async()=>{manifest=await (await fetch('/api/manifest')).json();filtered=manifest;const videos=[...new Set(manifest.map(x=>x.video))];const select=document.getElementById('videoFilter');videos.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v;select.appendChild(o)});updateProgress();loadItem()})();
</script>
</body>
</html>"""


def video_duration(path: Path) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())
    except FileNotFoundError:
        import cv2

        capture = cv2.VideoCapture(str(path))
        frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        capture.release()
        if frames <= 0 or fps <= 0:
            raise RuntimeError(f"Cannot read video duration: {path}")
        return frames / fps


def extract_frames(
    video: Path,
    output_pattern: Path,
    extraction_fps: float,
    frames_per_video: int | None,
    rotate: int = 0,
) -> None:
    """Use ffmpeg when available and OpenCV as a Windows fallback."""
    try:
        subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(video),
             "-vf", f"fps={extraction_fps}", "-frames:v", str(frames_per_video) if frames_per_video else "999999",
             "-q:v", "2", str(output_pattern)],
            check=True,
        )
        return
    except FileNotFoundError:
        import cv2

        capture = cv2.VideoCapture(str(video))
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        native_fps = float(capture.get(cv2.CAP_PROP_FPS))
        if total <= 0 or native_fps <= 0:
            capture.release()
            raise RuntimeError(f"Cannot extract frames from {video}")
        count = min(frames_per_video, total) if frames_per_video else max(1, round(total * extraction_fps / native_fps))
        indices = [round(i * (total - 1) / max(1, count - 1)) for i in range(count)]
        for output_index, frame_index in enumerate(indices, start=1):
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                continue
            if rotate == -90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif rotate == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            elif abs(rotate) == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            output = Path(str(output_pattern).replace("%05d", f"{output_index:05d}"))
            cv2.imwrite(str(output), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        capture.release()


def prepare(
    videos_dir: Path,
    dataset_dir: Path,
    fps: float,
    overwrite: bool,
    classes: list[str],
    rotate: int = 0,
    split: str = "test",
    patterns: list[str] | None = None,
    frames_per_video: int | None = None,
    recursive: bool = False,
) -> None:
    manifest_path = dataset_dir / "manifest.json"
    if manifest_path.exists() and not overwrite:
        print(f"Annotation task already exists: {manifest_path}")
        return
    if dataset_dir.exists() and overwrite:
        shutil.rmtree(dataset_dir)
    images_dir = dataset_dir / "images" / split
    labels_dir = dataset_dir / "labels" / split
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    patterns = patterns or ["*"]
    candidates = []
    for pattern in patterns:
        candidates.extend(videos_dir.rglob(pattern) if recursive else videos_dir.glob(pattern))
    videos = sorted({path for path in candidates if path.suffix.lower() in {".mp4", ".mov"}})
    if not videos:
        raise SystemExit(f"No videos found in {videos_dir}")

    items = []
    for video in videos:
        relative_video = video.relative_to(videos_dir)
        prefix = "__".join(relative_video.with_suffix("").parts)
        output_pattern = images_dir / f"{prefix}__%05d.jpg"
        duration = video_duration(video)
        extraction_fps = frames_per_video / duration if frames_per_video else fps
        print(f"Extracting {video.name} at {extraction_fps:g} fps...")
        extract_frames(video, output_pattern, extraction_fps, frames_per_video, rotate)
        frames = sorted(images_dir.glob(f"{prefix}__*.jpg"))
        for sequence, image_path in enumerate(frames):
            items.append({
                "id": image_path.stem,
                "image": image_path.name,
                "video": relative_video.as_posix(),
                "time_s": min(sequence / extraction_fps, duration),
            })

    manifest_path.write_text(json.dumps({"fps": fps, "split": split, "classes": classes, "items": items}, indent=2), encoding="utf-8")
    (dataset_dir / "classes.txt").write_text("\n".join(classes) + "\n", encoding="utf-8")
    print(f"Created {len(items)} annotation frames in {dataset_dir}")


class AnnotationHandler(BaseHTTPRequestHandler):
    dataset_dir: Path
    split: str
    items_by_id: dict[str, dict]
    classes: list[str]
    index_html: str

    def send_bytes(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, value, status: int = 200) -> None:
        self.send_bytes(json.dumps(value).encode(), "application/json; charset=utf-8", status)

    def item_from_path(self, prefix: str):
        item_id = unquote(urlparse(self.path).path[len(prefix):])
        return item_id, self.items_by_id.get(item_id)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self.send_bytes(self.index_html.encode(), "text/html; charset=utf-8")
            return
        if path == "/api/manifest":
            result = []
            for item in self.items_by_id.values():
                row = dict(item)
                row["reviewed"] = (self.dataset_dir / "labels" / self.split / f"{item['id']}.txt").exists()
                result.append(row)
            self.send_json(result)
            return
        if path.startswith("/api/labels/"):
            item_id, item = self.item_from_path("/api/labels/")
            if not item:
                self.send_json({"error": "unknown item"}, HTTPStatus.NOT_FOUND)
                return
            label_path = self.dataset_dir / "labels" / self.split / f"{item_id}.txt"
            boxes = []
            if label_path.exists():
                for line in label_path.read_text(encoding="utf-8").splitlines():
                    parts = line.split()
                    if len(parts) == 5:
                        boxes.append({"class_id": int(parts[0]), "cx": float(parts[1]), "cy": float(parts[2]),
                                      "w": float(parts[3]), "h": float(parts[4])})
            self.send_json(boxes)
            return
        if path.startswith("/image/"):
            _, item = self.item_from_path("/image/")
            if not item:
                self.send_bytes(b"not found", "text/plain", HTTPStatus.NOT_FOUND)
                return
            image_path = self.dataset_dir / "images" / self.split / item["image"]
            self.send_bytes(image_path.read_bytes(), mimetypes.guess_type(image_path.name)[0] or "image/jpeg")
            return
        self.send_bytes(b"not found", "text/plain", HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not path.startswith("/api/labels/"):
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        item_id, item = self.item_from_path("/api/labels/")
        if not item:
            self.send_json({"error": "unknown item"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            boxes = payload.get("boxes", [])
            lines = []
            for box in boxes:
                class_id = int(box["class_id"])
                values = [float(box[key]) for key in ("cx", "cy", "w", "h")]
                if class_id not in range(len(self.classes)) or not all(0.0 <= value <= 1.0 for value in values):
                    raise ValueError("invalid class or box coordinate")
                if values[2] <= 0 or values[3] <= 0:
                    raise ValueError("box must have positive size")
                lines.append(f"{class_id} " + " ".join(f"{value:.6f}" for value in values))
            label_path = self.dataset_dir / "labels" / self.split / f"{item_id}.txt"
            temporary = label_path.with_suffix(".tmp")
            temporary.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
            temporary.replace(label_path)
            self.send_json({"saved": True, "boxes": len(lines)})
        except (ValueError, KeyError, json.JSONDecodeError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args) -> None:
        return


def serve(dataset_dir: Path, host: str, port: int, open_browser: bool) -> None:
    manifest_path = dataset_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit("No annotation task found. Run once with --prepare.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    classes = manifest.get("classes", CLASSES)
    html = INDEX_HTML.replace(
        "const names = ['coke_zero','think_protein_bar','ziploc_box'];",
        "const names = " + json.dumps(classes) + ";",
    )
    if classes == ["coke_zero", "oreo", "goodwipes"]:
        html = html.replace("Think protein bar / 蛋白棒", "Oreo / 奥利奥")
        html = html.replace("Ziploc box / 保鲜袋盒", "Goodwipes / 湿巾")
    handler = type("ConfiguredAnnotationHandler", (AnnotationHandler,), {
        "dataset_dir": dataset_dir,
        "split": manifest.get("split", "test"),
        "classes": classes,
        "index_html": html,
        "items_by_id": {item["id"]: item for item in manifest["items"]},
    })
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}"
    print(f"Annotation UI: {url}")
    print("Labels are saved immediately. Press Control-C here to stop the server.")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--videos", type=Path, default=DEFAULT_VIDEOS)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--fps", type=float, default=2.0)
    parser.add_argument("--frames-per-video", type=int)
    parser.add_argument("--pattern", action="append", dest="patterns",
                        help="Video glob; repeat this option to include multiple patterns")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--split", choices=("train", "val", "test"), default="test")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--classes", nargs="+", default=CLASSES)
    parser.add_argument("--rotate", type=int, choices=(-180, -90, 0, 90, 180), default=0)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.fps <= 0:
        raise SystemExit("--fps must be positive")
    if args.frames_per_video is not None and args.frames_per_video <= 0:
        raise SystemExit("--frames-per-video must be positive")
    if args.prepare:
        prepare(
            args.videos.resolve(), args.dataset.resolve(), args.fps, args.overwrite, args.classes, args.rotate,
            args.split, args.patterns, args.frames_per_video, args.recursive,
        )
    if args.prepare_only:
        return
    serve(args.dataset.resolve(), args.host, args.port, not args.no_browser)


if __name__ == "__main__":
    main()
