#!/usr/bin/env bash
# 한글 폰트 오버라이드 스테이징 (+ 선택적 단독 pak).
#
# The Black Within 은 Trajan Pro 3 만 쓰는 복합 폰트(HorrorEngine.uasset)를 쓰고,
# UE4.27 의 CJK/한글 폴백은 에디터 전용이라 shipping 빌드에서는 동작하지 않는다.
# (SlateFontRenderer.cpp: last resort 폰트는 !RequiresCookedData() 일 때만.
#  LegacySlateFontInfoCache.cpp: 한글 서브타입페이스는 GIsEditor 일 때만.)
# 따라서 같은 경로의 폰트 페이스(.ufont = 원본 TTF 바이트)를 한글 폰트로 바꿔 넣는다.
#
# 결과물: out/font_extra/  ->  build-pak 의 --extra 로 locres 와 같은 pak 에 들어간다.
#
# 사용:
#   scripts/build_font_override.sh                # 스테이징만
#   REPAK=/tmp/repak/repak scripts/build_font_override.sh   # + 단독 pak 검증
set -euo pipefail
S="$(cd "$(dirname "$0")/.." && pwd)"
FONT="$S/assets/fonts/NotoSansKR-Regular.ttf"
DEST="$S/out/font_extra/TheBlackWithin/Content/HorrorEngine/Blueprints/Widgets/Fonts"

[ -f "$FONT" ] || { echo "missing $FONT (폰트 라이브러리에서 복사)" >&2; exit 1; }

# 한글 음절 11172자 전부 있는지 확인 (폰트를 바꿔치기하므로 필수)
python3 - "$FONT" <<'PY'
import sys
from fontTools.ttLib import TTFont
cmap = TTFont(sys.argv[1], lazy=True).getBestCmap()
missing = [c for c in range(0xAC00, 0xD7A4) if c not in cmap]
assert not missing, f"한글 음절 {len(missing)}자 누락"
print("hangul syllables: 11172/11172")
PY

mkdir -p "$DEST"
cp "$FONT" "$DEST/Trajan_Pro_3_Regular.ufont"
echo "staged: ${DEST#"$S"/}/Trajan_Pro_3_Regular.ufont"

# 선택: 단독 pak 으로 묶어 경로를 검증 (최종 배포는 locres 와 합친 하나의 pak)
if [ -n "${REPAK:-}" ]; then
  "$REPAK" pack --version V11 "$S/out/font_extra" "$S/out/font_override.pak"
  "$REPAK" list "$S/out/font_override.pak"
fi
