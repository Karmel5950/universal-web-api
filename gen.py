# -*- coding: utf-8 -*-
"""豆包生图一条命令工具(配合 universal-web-api 使用)

用法:
    python gen.py 一只戴宇航员头盔的柴犬
    python gen.py "提示词" --out D:\\pics
依赖:无(纯标准库)。需先启动 universal-web-api 服务并登录豆包。
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8199/v1/chat/completions"
PRESET = "文本-图像预设"
TIMEOUT = 300

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser(description="豆包生图:一条命令生成并保存图片")
    ap.add_argument("prompt", help="生图提示词")
    ap.add_argument("--out", default="gen_images", help="图片保存目录(默认 ./gen_images)")
    ap.add_argument("--model", default="doubao", help="模型名(默认 doubao)")
    args = ap.parse_args()

    body = json.dumps({
        "model": args.model,
        "preset_name": PRESET,
        "messages": [{"role": "user", "content": args.prompt}],
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        API, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    print(f"[+] 提示词: {args.prompt}")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    print(f"[+] 生成完成,耗时 {time.time() - t0:.1f}s")

    content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    if content:
        print(f"[+] 豆包回复: {content.strip()[:120]}")

    media = data.get("media") or []
    images = [m for m in media if m.get("media_type") == "image" and m.get("url")]
    if not images:
        print("[!] 没有返回图片。检查:1) 受控浏览器里豆包是否已登录;2) preset 是否为 文本-图像预设")
        sys.exit(1)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, m in enumerate(images, 1):
        url = m["url"]
        ext = ".png" if ".png" in url.split("?")[0] else ".jpg"
        path = out / f"{time.strftime('%Y%m%d_%H%M%S')}_{i}{ext}"
        with urllib.request.urlopen(url, timeout=60) as r, open(path, "wb") as f:
            f.write(r.read())
        tag = "原图" if path.stat().st_size > 500_000 else "小图"
        print(f"[+] 已保存({tag}, {path.stat().st_size // 1024}KB): {path.resolve()}")
        saved.append(str(path.resolve()))

    print(f"[+] 共 {len(saved)} 张,目录: {out.resolve()}")


if __name__ == "__main__":
    main()
