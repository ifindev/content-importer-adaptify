#!/usr/bin/env python3
"""Export the Design canvas (design/project) to one self-contained design/canvas.html.

Every artboard is embedded at its canvas position and frame size on a
pan/zoom canvas. Links between artboards move the canvas to that artboard.

Usage: python3 design/export.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "project"
OUT = ROOT / "canvas.html"

# Only static artboards convert 1:1; template features need the editor's runtime.
DYNAMIC = re.compile(r"\{\{|<sc-for|<sc-if|<dc-import|<x-import")

NAV_SCRIPT = (
    "document.addEventListener('click',e=>{const a=e.target.closest('a[data-board]');"
    "if(a){e.preventDefault();parent.postMessage({board:a.dataset.board},'*')}})"
)


def frame_id(board):
    return board.removesuffix(".dc.html")


def artboard_html(board, frame):
    src = (SRC / board).read_text()
    if DYNAMIC.search(src):
        raise SystemExit(f"{board}: uses template features ({{{{ }}}}, sc-*, dc-import, x-import); static export can't render it")
    xdc = re.search(r"<x-dc>(.*)</x-dc>", src, re.S)
    if not xdc:
        raise SystemExit(f"{board}: no <x-dc> block")
    lang = re.search(r'<html lang="([^"]+)"', src)
    body = xdc.group(1)
    helmet = re.search(r"<helmet>(.*?)</helmet>", body, re.S)
    head = helmet.group(1).strip() if helmet else ""
    if helmet:
        body = body.replace(helmet.group(0), "", 1)
    # A link to another artboard asks the canvas to move to it.
    body = re.sub(r'href="([^"#:/]+)\.dc\.html"', r'href="#\1" data-board="\1"', body)
    return (
        f'<!doctype html><html lang="{lang.group(1) if lang else "en"}"><head><meta charset="utf-8">'
        f"{head}<style>html,body{{min-height:{frame['h']}px}}</style></head>"
        f"<body>{body.strip()}<script>{NAV_SCRIPT}</script></body></html>"
    )


def canvas_html(canvas):
    boards = canvas["boards"]
    notes = [n for n in canvas.get("notes", {}).values() if n.get("kind") == "title1"]
    xs = [b["x"] for b in boards.values()] + [n["x"] for n in notes]
    ys = [b["y"] for b in boards.values()] + [n["y"] for n in notes]
    x0, y0 = min(xs) - 120, min(ys) - 160
    width = max(b["x"] + b["w"] for b in boards.values()) - x0 + 120
    height = max(b["y"] + b["h"] for b in boards.values()) - y0 + 120

    items = [
        f'<div class="note" style="left:{n["x"] - x0}px;top:{n["y"] - y0}px;max-width:{n.get("maxW", 2000)}px">'
        f'{html.escape(n["text"])}</div>'
        for n in notes
    ]
    for name in canvas.get("order", boards):
        b = boards[name]
        fid, label = frame_id(name), html.escape(b.get("title", name))
        doc = html.escape(artboard_html(name, b), quote=True)
        items.append(
            f'<div class="frame" id="{fid}" style="left:{b["x"] - x0}px;top:{b["y"] - y0}px;width:{b["w"]}px;height:{b["h"]}px">'
            f'<a class="label" href="#{fid}">{label}</a>'
            f'<iframe srcdoc="{doc}" title="{label}"></iframe></div>'
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(canvas.get("title", "Design"))}</title>
<style>
html,body{{margin:0;height:100%;overflow:hidden;background:#1e1e1e;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
#viewport{{position:absolute;inset:0;cursor:grab;touch-action:none}}
#viewport.dragging{{cursor:grabbing}}
#stage{{position:absolute;left:0;top:0;width:{width}px;height:{height}px;transform-origin:0 0}}
.frame{{position:absolute}}
.frame iframe{{display:block;width:100%;height:100%;border:0;background:#fff;pointer-events:none}}
body.interact .frame iframe{{pointer-events:auto}}
.label{{position:absolute;left:0;right:0;bottom:100%;padding-bottom:calc(5px / var(--s,1));font-size:calc(11px / var(--s,1));color:#a3a3a3;text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.label:hover{{color:#fff}}
.note{{position:absolute;font-size:72px;line-height:1.2;font-weight:700;color:#f5f5f5;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
#ui{{position:fixed;right:16px;bottom:16px;display:flex;gap:6px;align-items:center}}
#ui button{{height:32px;padding:0 12px;border:1px solid #3a3a3a;border-radius:8px;background:#2a2a2a;color:#e5e5e5;font:500 13px inherit;cursor:pointer}}
#ui button[aria-pressed="true"]{{background:#e5e5e5;color:#111}}
#zoom{{min-width:48px;text-align:center;color:#a3a3a3;font-size:12px}}
</style>
</head>
<body>
<div id="viewport"><div id="stage">
{chr(10).join(items)}
</div></div>
<div id="ui">
  <span id="zoom">100%</span>
  <button id="fit" type="button">Fit</button>
  <button id="interact" type="button" aria-pressed="false" title="Click into the screens instead of panning">Interact</button>
</div>
<script>
const vp = document.getElementById('viewport'), stage = document.getElementById('stage');
const W = {width}, H = {height};
let s = 1, tx = 0, ty = 0;
function apply() {{
  stage.style.transform = `translate(${{tx}}px,${{ty}}px) scale(${{s}})`;
  stage.style.setProperty('--s', s);
  document.getElementById('zoom').textContent = Math.round(s * 100) + '%';
}}
function show(x, y, w, h, pad) {{
  s = Math.min((innerWidth - pad) / w, (innerHeight - pad) / h, 1);
  tx = (innerWidth - w * s) / 2 - x * s; ty = (innerHeight - h * s) / 2 - y * s; apply();
}}
function fit() {{ show(0, 0, W, H, 0); }}
function go(id) {{
  const f = id && document.querySelector('.frame#' + CSS.escape(id));
  if (!f) return fit();
  show(f.offsetLeft, f.offsetTop, f.offsetWidth, f.offsetHeight, 96);
  try {{ history.replaceState(null, '', '#' + id); }} catch {{}}
}}
function focusFrame() {{ go(decodeURIComponent(location.hash.slice(1))); }}
function zoomAt(k, cx, cy) {{
  const n = Math.min(4, Math.max(0.05, s * k));
  tx = cx - (cx - tx) * n / s; ty = cy - (cy - ty) * n / s; s = n; apply();
}}
vp.addEventListener('wheel', e => {{
  e.preventDefault();
  if (e.ctrlKey || e.metaKey) zoomAt(Math.exp(-e.deltaY * 0.01), e.clientX, e.clientY);
  else {{ tx -= e.deltaX; ty -= e.deltaY; apply(); }}
}}, {{ passive: false }});
let drag = null;
vp.addEventListener('pointerdown', e => {{
  if (document.body.classList.contains('interact') || e.target.closest('a')) return;
  drag = {{ x: e.clientX - tx, y: e.clientY - ty }}; vp.classList.add('dragging'); vp.setPointerCapture(e.pointerId);
}});
vp.addEventListener('pointermove', e => {{ if (drag) {{ tx = e.clientX - drag.x; ty = e.clientY - drag.y; apply(); }} }});
vp.addEventListener('pointerup', () => {{ drag = null; vp.classList.remove('dragging'); }});
document.getElementById('fit').onclick = () => {{ try {{ history.replaceState(null, '', location.pathname); }} catch {{}} fit(); }};
document.getElementById('interact').onclick = e => {{
  const on = document.body.classList.toggle('interact');
  e.currentTarget.setAttribute('aria-pressed', on);
}};
document.querySelectorAll('.label').forEach(a => a.addEventListener('click', e => {{
  e.preventDefault(); go(a.parentElement.id);
}}));
addEventListener('message', e => {{ if (typeof e.data?.board === 'string') go(e.data.board); }});
addEventListener('hashchange', focusFrame);
addEventListener('resize', focusFrame);
focusFrame();
</script>
</body>
</html>
"""


def main():
    canvas = json.loads((SRC / "canvas.json").read_text())
    OUT.write_text(canvas_html(canvas))
    print(f"Exported {len(canvas['boards'])} screens to {OUT}")


if __name__ == "__main__":
    main()
