# Notes — theblackwithin-l10n-ko

## 게임/패키지

- The Black Within (Steam), UE4.27.2, `ProjectVersion=3.0.1`, `ProjectName="The Black Within "` (`TheBlackWithin/Config/DefaultGame.ini`).
- pak: `TheBlackWithin/Content/Paks/TheBlackWithin-WindowsNoEditor.pak`
  (V11, 인덱스 미암호화, Oodle 압축, 14,767 엔트리). 항상 좁은 `-i` glob 으로만 `repak unpack` 한다.
- **로컬라이제이션 타깃이 없다.** `DefaultGame.ini` 에 `InternationalizationPreset=English`,
  `-CulturesToStage=en`, `+CulturesToStage=en` 만 있고 `Localization/` 폴더도, `.locres` 도 없다.
  그래서 게임의 `en` locres 로 키를 확인할 방법이 없고, 자산에서 직접 스캔해야 한다.
- 기본 폰트: `/Game/HorrorEngine/Blueprints/Widgets/Fonts/HorrorEngine` (UFont, `FontCacheType=Runtime`,
  복합 폰트에 타입페이스 1개 = Trajan Pro 3). 한글 글리프 없음 → 아래 폰트 항목 참고.

## 기법

FText 리터럴은 cooked 자산 안에서 `(namespace="", key=<32-hex GUID>)` 를 갖는다.
높은 우선순위 pak(`zz_KoreanPatch_P.pak`)에 `TheBlackWithin/Content/Localization/Game/ko/Game.locres`
를 넣으면 GUID 키로 원문이 덮인다. entry 해시는 `pylocres.crc_hash.str_crc32(msgid)`.
PO 규약: `msgctxt="::<GUID>"`, `msgid`=영어 원문, `msgstr`=한국어.
`.uasset` 은 건드리지 않는다.

## 문자열 규모

- PO **1327 엔트리 / 고유 msgid 649** (`locales/game_raw.po`).
- 917 엔트리(65개 파일): `adapters/ue_locres.py scan-uexp` 로 스캔한 표준 FText
  (`FString 3개 = namespace/key/source`). namespace 는 전부 빈 문자열.
- **410 엔트리(50개 파일) 추가**: 블루프린트 노드 기본값에 저장된 FText 는
  `\x1f<source>\x00\x1f<GUID>\x00` 형식(문자열 길이 없이 NUL 종료)이라 위 스캐너가 놓친다.
  공유 스캐너(`scan-uexp`)의 두 번째 패스로 채웠다. 이 410개 키는 전부 The Green Light 의 `en` locres 에도
  같은 원문으로 존재해 실제 지역화 키임이 확인된다(410/410). 고유 문구는 91개이고
  **그중 63개는 기존 PO 에 아예 없던 문구**다(`"is empty."`, `"added to equipment."`, `"VIDEO SETTINGS"` 등).
- GL(The Green Light)과 겹침: 고유 msgid 649개 중 **644개가 GL PO 와 동일**, BW 전용은 5개
  (`"Find a way to enter your boss's house."`, `"Okay, in and out..."`, `The Rituals Begin`,
  `Wishlist As Long As She Forgot`, `arnes house`).
- 형식: 선행 공백 6, 후행 공백 63, 실제 CRLF 1, LF 1, 큰따옴표로 시작 82, `{N}`/`%s` 자리표시자 0.
- 화자 접두(고유 msgid 기준): `Laila:` 35, `Arne:` 19, `Stranger:` 3, `Tip:` 1.
- 번역 제외 26개(URL 1, 숫자·기호 18, 키 이름 3, 브랜드 3, `300 FPS`) → `locales/no_translate.txt`.

## 스캔 누락 가능성 점검 (실측)

| 종류 | 결과 |
|------|------|
| 비어 있지 않은 namespace | 0 (전부 `""`) |
| `FText::Format`/ArgumentFormat | 자산에 `{0}`~`{9}`/`%s` 없음. 조립은 BP 문자열 연결로만 한다 |
| StringTable 참조 | 게임에 StringTable 자산 없음 |
| `.umap` 레벨 액터 텍스트 | `.umap` 자체에는 FText 없음(데이터는 `.uexp`). 미커버 맵(`Loding`, `cutscen1`, `Thegreenlight`, `Intro`)도 문자열 0 |
| 일반 FString/FName | 로컬라이즈 불가. MainMenu 의 `steam://openurl/https://store.steampowered.com/...`, `https://twitter.com/...` 등이 여기 속하며 **영어 그대로 남는다**(URL 이라 문제 없음) |
| Text3D/TextRender | 액터의 `Text` 는 FText 라 스캔에 포함된다. 폰트는 지정돼 있지 않아 엔진 Roboto 복합 폰트를 쓰고, 그 폰트는 `FallbackTypeface=DroidSansFallback` 이라 한글이 나온다 |
| 노드 리터럴 FText | 첫 스캐너가 놓침 → 두 번째 패스(`_NODE_LITERAL`)로 보완 |

`locales/game_raw.po` 를 다시 만들 때는 한 번이면 된다 (표준 FText 와 노드 리터럴을 같이 찾는다):

```
tools-l10n-ko/adapters/ue_locres.py scan-uexp --src <푼 디렉터리> --out locales/game_raw.po
```

노드 리터럴 처리는 처음에 이 repo 의 보완 스크립트로 했다가, 공유 어댑터 `ue_locres.py` 의 `scan-uexp` 로 합쳤다
(`tests/test_ue_locres.py::test_scan_all_finds_node_literal_layout_too`). 스크립트는 삭제했다.

## 조각 문자열 (BP 문자열 연결)

노드 리터럴에는 **아이템 이름 뒤에 이어 붙는 조각**이 많다
(`<이름>` + `"is empty."`, `"There is no any"` + `<이름>` + `"in inventory."`, `"added to "` + `"equipment."`).
번역할 때 앞뒤 공백·마침표를 그대로 두고 서술어로 옮긴다(자세한 규칙은 `docs/style.md`).
한국어 조사는 아이템 이름 쪽에 붙지 않으므로 `"열쇠 잠겼습니다."` 처럼 읽히게 만든다.

## 폰트 — 오버라이드 필요 (확정)

결론: **한글을 표시하려면 폰트를 바꿔 넣어야 한다.** 근거는 전부 실제 파일에서 확인했다.

1. 게임 UI 폰트는 `/Game/.../Widgets/Fonts/HorrorEngine` (UFont, 복합 폰트, `FontCacheType=Runtime`).
   타입페이스는 `Trajan_Pro_3_Regular` 하나이고 **`FallbackTypeface` 가 없다**
   (이름 테이블에 `FallbackTypeface` 없음. 엔진 `Roboto.uasset` 에는 있다).
   Trajan 실측: cmap 839자, **한글 음절 0/11,172**.
2. UE4.27 의 CJK/한글 폴백은 **에디터 전용**이다.
   - `SlateFontRenderer.cpp:362-377`: 글리프가 없으면 "last resort fallback font" 를 쓰는데,
     `FLegacySlateFontInfoCache::IsLastResortFontAvailable()` 일 때만이다.
   - `LegacySlateFontInfoCache.cpp:50-51`: `LastResortFontPath = Engine/Content/SlateDebug/Fonts/LastResort.ttf`,
     `bIsLastResortFontAvailable = !FPlatformProperties::RequiresCookedData() && FileExists(...)`.
     shipping(쿠킹된) 빌드에서는 항상 false 이고, 이 게임 pak 에 `SlateDebug/` 자체가 없다.
   - `LegacySlateFontInfoCache.cpp:187-207`: 한글 서브타입페이스(NanumGothic)와 CJK 폴백은 `if (GIsEditor)`.
3. 참고로 게임 pak 에는 `Engine/Content/EngineFonts/Faces/DroidSansFallback.ufont`(3.9MB)가 있고
   **한글 음절 11,172자 전부 + 자모 99 + 호환자모 94** 를 포함한다(fontTools 실측, cmap 34,492자).
   엔진 `Roboto.uasset` 의 `FallbackTypeface` 가 이 폰트를 가리키므로 **Roboto 복합 폰트를 쓰는 텍스트
   (TextRender 등)는 한글이 정상 출력**된다. 문제는 게임 위젯이 쓰는 Trajan 복합 폰트뿐이다.
4. 같은 개발사의 The Green Light 는 한글 지원을 위해 `HorrorEngine` 폰트를 Pretendard 로 바꿔 두었다.
   같은 결론의 실물 증거다.

### 오버라이드 방식 (확인한 사실)

- `Trajan_Pro_3_Regular.uexp` 는 157바이트짜리 **외부 벌크 참조**다:
  `../../../The Black Within steam/Content/HorrorEngine/Blueprints/Widgets/Fonts/Trajan_Pro_3_Regular.ufont`
  경로만 들고 있고 **폰트 바이트 크기는 저장하지 않는다**
  (158KB RobotoRegular, 386KB Trajan, 3.9MB DroidSansFallback 의 uexp 헤더 구조가 동일하고 크기 정수가 없다).
- `.ufont` = 폰트 파일 원본 바이트(TTF/OTF). 따라서 **같은 가상 경로로 다른 폰트를 넣으면 교체된다.**
  `.uasset`/`.uexp` 는 건드리지 않는다.
- 적용 폰트: **Noto Sans KR Regular** (`assets/fonts/NotoSansKR-Regular.ttf`, 6,191,364B,
  SIL OFL 1.1 — `assets/fonts/OFL.txt`). 게임 전체(영문·숫자 포함)가 이 폰트로 그려진다.
- `scripts/build_font_override.sh` 가 한글 11,172자 전수 검사 후
  `out/font_extra/TheBlackWithin/Content/HorrorEngine/Blueprints/Widgets/Fonts/Trajan_Pro_3_Regular.ufont`
  로 스테이징하고, `REPAK` 을 주면 V11 pak 으로 묶어 `repak list` 로 경로를 검증한다(실행 확인).
- 최종 배포는 locres 와 같은 pak 하나에 넣는다:
  `ue_locres.py build-pak ... --extra out/font_extra` → `out/zz_KoreanPatch_P.pak`.

## 시작 경고 화면 (영상에 구워진 글자)

게임을 켤 때마다 나오는 `Headphones` / `Warning` / `Please reach out to your local church or mosque immediately.` 는
FText 가 아니라 **영상 `Content/Movies/opning scene.mp4` (1920x1080, 30fps, 34.03s) 의 픽셀**이다. locres 로는 번역되지 않는다.
`DefaultEngine.ini` 의 `StartupMovies=opning scene` + `bMoviesAreSkippable=False` 로 매번 재생된다
(`opningsceneplayer` MediaPlayer 에셋에는 파일 경로가 없고 pak 안 어떤 에셋도 이 파일을 가리키지 않는다).
이 파일은 pak 밖의 느슨한 파일이라 같은 경로로 교체하면 된다.

- 카드 구간(프레임, 7프레임 페이드 인/아웃): Headphones 263-381, Warning 제목 396-539, Warning 본문 436-653, 교회/모스크 줄 660-834.
  Waleedzo 로고(2.5-8s)는 브랜드라 그대로 둔다.
- `scripts/build_intro_video.py`: 영어 영역을 검정 박스로 덮고 같은 구간·같은 페이드로 한국어를 `drawtext` 로 그린다
  (Noto Sans KR, 문구와 위치는 `locales/intro_cards.json`). 비디오 libx264 CRF17 재인코딩, **오디오는 `-c:a copy` 로 원본과 바이트 동일**(md5 확인).
- ffmpeg `drawtext` 의 `n`(프레임 번호)은 입력 시킹(`-ss` 가 `-i` 앞)이면 0부터 다시 세어져 카드 구간이 어긋난다. 미리보기는 `select` 로 고른다.
- 설치기 반영 여부: **현재 배포하지 않는다** (사용자 결정으로 설치기 config 에서 뺐다). 다시 넣으려면 `copy` + `"gate": true` 항목을 추가한다 (원본 해시 `15e96b74…`가 다르면 설치를 거부하고, 원본은 `kor_bak` 에 백업된다). README 의 "시작 경고 화면" 참고.

## 설치기: 새 파일 처리

payload 는 새 파일 하나다: `TheBlackWithin/Content/Paks/zz_KoreanPatch_P.pak`(원본 없음).

초기 조사에서는 원본 없는 파일의 복원/삭제(메뉴 2·3, `--uninstall`)가 불가능했다(`restore()` 가 모든 항목의 백업을 요구).
공유 설치기를 고쳐 해결했다: 설치 시 대상이 없으면 `kor_bak/<경로>.new` 표시 파일을 남기고 `restore()` 가 그 파일을 **삭제**한다.
제안했던 `"new": true` config 필드는 필요 없어 추가하지 않았다.
gate 파일이 지원 버전이 아닐 때 앞서 처리된 pak 이 이미 설치되던 문제도 고쳤다: `install()` 이 쓰기 전에 모든 gate 를 먼저 검사한다.

## 검증한 것

- 공유 스캐너(`scan-uexp`)가 두 형식을 한 번에 찾아 1327 엔트리를 낸다 (에이전트가 따로 만든 PO 와 키 개수 일치).
- 폰트 스테이징 + `repak pack --version V11` + `repak list` → 경로 1개 확인.
- `tools/translate/translate.py prefix --glossary ... --style ...` 로 glossary/style 로드 확인.
- PO 전 항목이 pak 안 자산에서 키 바이트로 존재(추출한 65개 파일 376/376).
- **실제 게임에서 확인**(Orca computer-use): 메인 메뉴(`계속/새 게임/게임 불러오기/설정/게임 종료`), 설정 화면 전체
  (`게임플레이/입력/비디오 설정` 탭 포함 — 노드 리터럴로 보완한 키), 목표 창(`아직 목표가 없습니다.`, `[TAB]닫기`).
  한글이 두부(□) 없이 Noto Sans KR 로 렌더링된다.
