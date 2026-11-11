#!/usr/bin/env python3
"""opning scene.mp4 의 영어 경고 카드(Headphones / Warning / Please reach out…)를 한국어로 덮어쓴 영상을 만든다.

배경: DefaultEngine.ini 의 `StartupMovies=opning scene` 때문에 게임을 켤 때마다 이 영상이 (건너뛸 수 없게) 재생된다.
카드 글자는 영상에 구워져 있어 locres 로 번역되지 않는다. 그래서 영어 글자 영역을 검정으로 덮고
같은 시간에 같은 페이드(7프레임 안/밖)로 한국어를 그린다. 로고(Waleedzo Games)는 그대로 둔다.

usage:
  build_intro_video.py --src "<게임>/TheBlackWithin/Content/Movies/opning scene.mp4" --out out/Movies/"opning scene.mp4"
  (--preview 로 카드마다 한 프레임씩 PNG 만 뽑아 확인할 수 있다)

카드 시간/영역(프레임 @30fps, 1920x1080)은 원본 영상에서 실측한 값이다 (docs/NOTES.md 참고).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "assets", "fonts", "NotoSansKR-Regular.ttf")
TEXTS = os.path.join(HERE, "..", "locales", "intro_cards.json")
FPS = 30
FADE = 7  # 원본 페이드 길이(프레임)

# (id, 시작프레임, 끝프레임, 영어를 덮을 영역 x,y,w,h) — 영역은 영어 글자 bbox 에 여백을 더한 값
CARDS = [
    ("headphones", 263, 381, (600, 430, 720, 175)),
    ("warning_title", 396, 539, (600, 70, 640, 110)),
    ("warning_body", 436, 653, (0, 385, 1920, 275)),
    ("reach_out", 660, 834, (0, 725, 1920, 145)),
]


def esc(s):
    """drawtext 옵션 값용 이스케이프."""
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")


def alpha_expr(a, b):
    """프레임 a..b 에서 FADE 프레임 페이드 인/아웃 (n 은 프레임 번호). 0..1."""
    return "if(lt(n,%d),0,if(lt(n,%d),(n-%d)/%d,if(lt(n,%d),1,if(lt(n,%d),(%d-n)/%d,0))))" % (
        a, a + FADE, a, FADE, b - FADE + 1, b + 1, b + 1, FADE)


def filters(texts, font):
    f = []
    for cid, a, b, (x, y, w, h) in CARDS:
        # 영어 영역은 해당 카드 구간에서만 검정으로 덮는다
        f.append("drawbox=x=%d:y=%d:w=%d:h=%d:color=black@1:t=fill:enable='between(n,%d,%d)'" % (x, y, w, h, a, b))
    for cid, a, b, _ in CARDS:
        for item in texts[cid]:
            f.append(
                "drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=white:x=%s:y=%d:alpha='%s'" % (
                    esc(font), esc(item["text"]), item["size"], item.get("x", "(w-text_w)/2"), item["y"], alpha_expr(a, b)))
    return ",".join(f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview", help="PNG 미리보기를 이 폴더에 저장하고 영상은 만들지 않는다")
    a = ap.parse_args()
    with open(TEXTS, encoding="utf-8") as fh:
        texts = json.load(fh)
    font = os.path.abspath(FONT)
    vf = filters(texts, font)
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        for cid, s, e, _ in CARDS:
            t = (s + e) / 2 / FPS
            # 입력 시킹(-ss -i)이면 필터의 n 이 0부터 다시 세어져 카드 구간이 어긋난다. 처음부터 디코드하고 select 로 고른다.
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-vf", vf + ",select=gte(t\\,%.3f)" % t, "-frames:v", "1",
                            os.path.join(a.preview, cid + ".png")], check=True)
            print("preview", cid)
        return
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    # -ss/-t 없이 전체 재인코딩: 오디오는 그대로 복사한다 (AAC 48k stereo 원본 유지)
    tmp = a.out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-pix_fmt", "yuv420p", "-profile:v", "main", "-r", "30", "-c:a", "copy", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, a.out)
    print("built", a.out, os.path.getsize(a.out), "bytes")


if __name__ == "__main__":
    sys.exit(main())
