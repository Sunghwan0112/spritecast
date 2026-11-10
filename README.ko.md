# SpriteCast

**Claude Code용 아이소메트릭 스프라이트 생성기:** 게임 소품과 인물, 8방향 걷기를 실제 크기와 내 게임의 카메라 각도로 만들어요.
그림은 이미지 모델(OpenAI, 내 키로)이 3D 가이드 위에 원하는 그림체로 그리고, SpriteCast는 크기, 각도, 걸음, 그림자를 정해요.

무료, MIT. 비용은 OpenAI(걷는 캐릭터는 Tripo도)에 직접 내요: 소품 약 $0.07, 걷는 캐릭터 약 $2.2와 Tripo 75크레딧. 키 없이 무료로
해 보려면 Claude에게 *"SpriteCast 체험해 줘"*라고 하세요.

[English](README.md)

![GPT만으로 두 번 시도한 것과 SpriteCast: 같은 캐릭터가 남동쪽으로 걷기](docs/gpt-alone-vs-guide.ko.gif)

*GPT만으로(두 번 시도) 그린 것과 SpriteCast: 같은 캐릭터가 남동쪽으로 걸어요.*

```
claude plugin marketplace add Sunghwan0112/spritecast
claude plugin install spritecast@spritecast
```

![가이드 → 스프라이트](docs/showcase.png)

## 무엇을 하나요

이미지 모델에 "아이소메트릭 안락의자"를 그려 달라고 하면 예쁘긴 한데 각도가 조금씩 틀려요. 다시 그리면 또 다른 각도, 다른 크기로 나와요.
열 개를 한 바닥에 놓으면 하나도 맞지 않아요.

걷는 캐릭터는 더 심해요. 맨 위는 GPT만으로 그린 것(같은 모델, 같은 캐릭터 시트, 걸음을 프레임마다 글로 지시)과 SpriteCast를 나란히 놓은
거예요. GPT의 프레임은 한 장씩 보면 예쁘지만 걷지 않아요: 여덟 프레임 모두 같은 다리가 앞에 있고(다리를 안 바꿔요),
팔은 다리와 반대로 흔들리지 않고 제멋대로 움찔거리고, 게임의 30° 내려다보는 시점이 아니라
눈높이에서 봤고, 그림자도 없어요. 두 번 시도한 걸 나온 그대로 보여 줘요.

SpriteCast는 모델이 잘못 읽기 어려운 가이드를 줘요(잘못 읽으면 알려 줘요).
1. Claude가 물건을 **실제 크기(미터)**의 블록으로 짜요.
2. 블록을 게임의 **정확한 카메라**로 렌더해요.
3. 이미지 모델은 그 가이드를 **원하는 그림체**로 다시 그리기만 해요.
4. 그린 그림을 오려서 **가이드의 상자에 맞춰 놓아요.** 그래서 크기와 바닥 차지 면적은 가이드와 같아요. 윤곽이 가이드를 따르지 않는
   그림은 억지로 맞추지 않고 경고해요. 그림자와 엔진용 앵커도 같이 나와요.

**그래서 좋은 점:**
- **각도와 크기가 맞아요.** 단단한 소품 예시는 가이드와 윤곽이 95–99% 겹쳐요. 일부러 잎을 자유롭게 그린 화분은 87%, 옷 입은
  인물은 69–88%예요(옷과 머리카락이 맨 마네킹 밖으로 나가요). 걷는 캐릭터는 프레임마다 점수를 매겨요(아래). 카메라와 축척이 고정이라
  다른 때에 만든 소품도 한 바닥에 맞아요.
- **그림자가 자연스러워요.** 모든 소품이 빛 하나를 함께 써서 그림자가 같은 방향으로 떨어져요. 단단한 소품은 3D 가이드의 그림자를
  그대로 받아요. 포즈 잡은 인물과 식물은 그림 모양 그대로의 그림자(모자, 머리카락, 잎)를 받는데, 위치는 3D 모델이 정해서 발과 화분
  바닥이 선 자리에서 그림자가 시작해요. 걷는 캐릭터는 프레임마다 3D 몸의 그림자를 받아요. 대충 칠한 그림자도, 각진 마네킹 그림자도
  아니에요.
- **스스로 검사해요.** 그린 뒤 가이드와 비교해서, 모델이 다른 각도로 그렸으면 억지로 늘리거나 줄이지 않아요. 대신 경고를 띄우고, Claude가
  고칠 방법을 제안한 뒤 다시 그릴지 물어봐요.
- **내 게임 시점, 내 그림체.** 2:1 아이소메트릭, 정아이소메트릭, 3/4 탑다운, 정면, 아무 각도. 한 물건의 네 방향. 기본 `cozy` 스타일이나
  내 그림 한 장.

결과물은 픽셀아트가 아니라 일러스트예요(`cozy`: 부드러운 명암, 가는 외곽선). 픽셀아트 게임이면 내 스타일 그림과 그걸 설명하는
`look`을 주고, 몇 번 시도해야 할 수 있어요.

## 사용 흐름

![사용 흐름](docs/session.png)

소품을 설명하면 Claude는 빠진 것만 물어봐요(크기, 방향, 게임 시점, 그림체). 그다음 가이드를 무료로 렌더해서 보여 주고, 비용을 말한 뒤
승인을 기다려요. 결과로 `sprite.png`, `shadow.png`, `sprite.json`을 받아요.

## 설치

터미널에서:
```
claude plugin marketplace add Sunghwan0112/spritecast
claude plugin install spritecast@spritecast
```
Claude Code 안에서 할 수도 있어요: `/plugin marketplace add Sunghwan0112/spritecast` 다음 `/plugin install spritecast@spritecast`.

**함께 필요한 건** Python 3.9 이상과 브라우저(Chrome, 또는 Edge - 윈도우에는 늘 있어요)뿐이에요. 처음 쓸 때 Claude가 설치 점검
(`doctor.py --fix`)을 돌려요: `~/.cache/spritecast/`에 전용 가상환경을 만들어 몇 가지 패키지를 넣고(10초쯤), 원래 Python은 건드리지
않고, 각각 무엇에 쓰는지 알려 줘요. 손으로 설치할 건 없어요.

**스크립트를 직접 돌릴 때.** 보통은 Claude가 대신 돌려요. 이 저장소를 받아서 손으로 돌리려면 `doctor.py`가 마지막 줄에 찍는
Python(`PYTHON=...`)을 쓰세요. `--fix` 뒤에는 `~/.cache/spritecast/venv/bin/python`이에요(Windows:
`%USERPROFILE%\.cache\spritecast\venv\Scripts\python.exe`). 그냥 `python`에는 패키지가 없을 수 있어요(`No module named ...`). 아래
명령들은 이걸 `$PYTHON`으로 적어요.
```bash
python3 skills/spritecast/scripts/doctor.py --fix
PYTHON=$(python3 skills/spritecast/scripts/doctor.py | sed -n 's/^PYTHON=//p')
$PYTHON skills/spritecast/scripts/isoprop.py --help
```
Windows PowerShell에서는:
```powershell
python skills/spritecast/scripts/doctor.py --fix
$PYTHON = "$env:USERPROFILE\.cache\spritecast\venv\Scripts\python.exe"
& $PYTHON skills/spritecast/scripts/isoprop.py --help
```
거기서는 아래의 `$PYTHON ...` 명령을 `& $PYTHON ...`로 돌리세요.

| 무엇 | 하는 일 | 꼭 필요? |
|---|---|---|
| Python 3.9 이상 | 스크립트 실행 | 네 |
| numpy, pillow, scipy | 오려내기, 맞추기, 그림자 | 네 (자동 설치) |
| playwright + Chrome 또는 Edge | 3D 가이드를 내 컴퓨터에서 렌더 (무료) | 네 (자동 설치, 있는 브라우저를 씀) |
| onnxruntime + 224 MB 모델 | 캐릭터만: 흰 종이 위 흰 신발도 남기는 AI 오려내기 | 캐릭터 (처음 한 번 저절로 받음) |
| `OPENAI_API_KEY` | 그리기, 소품 하나 약 $0.07 | 그릴 때 |
| `TRIPO_API_KEY` | 캐릭터: 3D 모델, 리그, 걷기 | 걷는 캐릭터 |

**먼저 무료로, 키 없이 해 보기:** Claude에게 *"SpriteCast 체험해 줘"*라고 하면 예시 하나의 가이드를 내 컴퓨터에서 렌더하고, 예시에
들어 있는 그림으로 마무리해서(`isoprop.py try`) 돈을 쓰기 전에 전 과정을 볼 수 있어요.

키: **플러그인 설정에 넣어요.** SpriteCast를 켤 때 Claude Code가 물어봐요(나중에 바꾸려면 `/plugin` → SpriteCast → 설정). OpenAI
키, 그리고 걷는 캐릭터를 만들면 Tripo 키요. 입력은 가려지고 시스템의 자격 증명 저장소에 보관되며, 세션이 시작될 때 SpriteCast
스크립트에 전달돼요(바꾼 뒤엔 Claude Code를 다시 켜요). 설정에 키가 없으면 환경 변수의 키도 그대로 쓸 수 있어요:

```bash
export OPENAI_API_KEY=sk-...          # macOS / Linux (계속 쓰려면 ~/.zshrc 나 ~/.bashrc 에 추가)
```
```powershell
setx OPENAI_API_KEY "sk-..."          # Windows (설정 후 새 터미널을 열어요)
```
Windows에서는 Claude Code가 명령을 Git Bash로 돌릴 때만(Git이 깔려 있으면 기본) 설정의 키가 스크립트에 전달돼요. PowerShell이면
환경 변수를 쓰세요. 키는 내 컴퓨터에만 있고 OpenAI로만 보내져요. 그림 한 장마다 OpenAI에 약 $0.07를 내요.

OpenAI는 키로 이미지 모델을 쓰기 전에 조직 인증(platform.openai.com → Settings → Organization)을 요구할 수 있어요. 첫 그림 전에
한 번 해 두세요. 키는 Claude Code를 켜기 전에 설정하세요(켜 둔 채 설정하면 다시 켜야 보여요). 걷는 캐릭터는 `TRIPO_API_KEY`도
필요해요. Tripo API 플랫폼에서 받고, 거기서 API 크레딧을 사요(캐릭터 75, 동물 30).

## 이렇게 부탁해 보세요

- *"아이소메트릭 책장 만들어 줘. 높이 1.8m, 책 가득, cozy 스타일로."*
- *"우리 게임은 3/4 탑다운이야. 줄무늬 차양이 있는 나무 시장 가판대 만들어 줘."*
- *"이 소파 네 방향 다 만들어 줘."* (`views`)
- *"상점 주인 NPC 만들어 줘. 갈색 카디건 입은 할아버지, 네 방향으로."*
- *"손 흔드는 거리 악사, 남동쪽 방향으로."*
- *"이건 우리 게임 소품이야(props/barrel.png). 같은 그림체로 나무 상자 만들어 줘."*

## 예시

모두 [`examples/`](examples)에 있고, 사양 파일과 만들어진 파일이 들어 있어요(원본 그림은 저장소를 가볍게 하려고 WebP로).

| | | |
|---|---|---|
| ![](examples/reading_armchair/preview.png) | ![](examples/potted_monstera/preview.png) | ![](examples/arcade_cabinet/preview.png) |
| `reading_armchair`: 블록 9개(좌석, 등받이, 팔걸이, 다리) | `potted_monstera`: 화분, 그리고 식물은 덩어리 하나로 | `arcade_cabinet`: 정면이 왼쪽 아래를 향함 |

![네 방향과 탑다운](docs/views.png)
`armchair_four_ways`: `views: [0, 90, 180, 270]`. 두 번째 방향부터는 첫 그림을 레퍼런스로 그려서 같은 의자로 이어져요.
`arcade_cabinet_topdown`: `camera: "topdown"`. `reading_armchair_tripo`: 같은 안락의자를 Tripo 모델로(아래).

예제의 3D 모델(`reading_armchair_tripo`, 걷는 캐릭터들의 모델과 리그)은 [Tripo](https://www.tripo3d.ai) API로 만들었어요.

## 더 정교하게: 3D 모델을 먼저 (Tripo)

![블록 가이드와 Tripo 모델 가이드 비교](docs/tripo.png)

배치와 크기가 중요하면 블록으로 충분해요. 디테일(곡선 팔걸이, 가늘어지는 다리, 단추, 조각)을 더 살리고 싶으면
[Tripo](https://www.tripo3d.ai)로 설명에서 진짜 3D 모델을 먼저 만들어요. 그 모델을 블록과 같은 실제 크기 상자에 맞춰 넣어서 가이드로
써요. 그래서 배치는 그대로이고, 이미지 모델은 실제 형태 위에 그리고, 3D 그림자도 모델 자신의 것이 돼요.

```
$PYTHON skills/spritecast/scripts/isoprop.py model  armchair.json --yes   # Tripo로 3D 모델 만들기 (Tripo 크레딧 약 20-40, 약 2분). 사양이 이 모델을 쓰게 바뀌어요
$PYTHON skills/spritecast/scripts/isoprop.py yaws   armchair.json         # 무료: 모델을 네 방향으로 돌려 보여 줘요. 맞는 방향을 "model": {"yaw": ...}에 적어요
$PYTHON skills/spritecast/scripts/isoprop.py render armchair.json         # 그다음은 평소처럼 draw, finish
```
`TRIPO_API_KEY`가 필요해요. 블록은 사양에 `blocks_draft`로 남아요.

## 인물

![마네킹 가이드와 네 방향 인물 두 명](docs/characters.png)

서 있는 인물도 같은 방식이에요. Claude가 실제 키의 마네킹을 세워서 방향마다(4 또는 8방향) 렌더하면, 이미지 모델이 설명대로 옷을 입혀
그려요. 첫 방향을 먼저 그리고 나머지는 그 그림을 따라 그려서 같은 사람으로 이어져요.

```json
{ "name": "barista",
  "character": { "height": 1.63, "build": "slim", "directions": ["south-east", "south-west", "north-east", "north-west"] },
  "description": "a cheerful young café barista: a short dark-brown bob, a cream cable-knit sweater under a forest-green apron, ..." }
```

앵커는 두 발 사이예요. 첫 방향은 약 $0.07, 나머지는 방향마다 약 $0.08예요.

**자세.** 마네킹에 관절이 있어서 자세를 고를 수 있어요. `"pose"`는 다음 중 하나예요.
- `stand` (기본, 차렷)
- `wave` (손 흔들기)
- `point` (가리키기)
- `hold` (두 손을 앞에 모음: 컵, 쟁반, 책)
- `arms-crossed` (팔짱)
- `walk` (걷는 중)

설명에도 맞춰 적어 주세요("손 흔들며 인사", "커피잔을 두 손으로 들고"). 각도를 직접 적을 수도 있어요. 그러면 Claude가
"팔을 더 높이" 같은 요청을 숫자로 바꾸고, 무료 렌더로 확인하면서 고쳐 줘요.

```json
"pose": { "base": "stand", "arm": { "left": [[150, 10], [170, 10]], "right": [[150, 10], [170, 10]] } }
```
팔다리마다 위·아래 두 마디가 있고, 각 마디는 `[옆으로, 앞으로]` 각도예요. 먼저 옆으로 벌리고 그다음 앞으로 들어요. `left`, `right`는
캐릭터 자신의 왼쪽과 오른쪽이에요.

![네 가지 자세](docs/poses.png)

**방향마다 한 장짜리 그림이에요.** 걷는 캐릭터는 [걷는 캐릭터](#걷는-캐릭터)를 보세요.
방향마다 직접 확인하세요(머리가 엉뚱한 쪽을 보는 건 윤곽 검사로 못 잡아요). 한 방향만 다시 그리려면
`draw <spec> --yes --again --only north-west`.

## 그림에 맞는 그림자

3D 가이드에서 계산한 그림자는 가구처럼 단단한 물건에는 잘 맞아요. 그런데 완성 그림에는 블록에 없던 것들이 있어요. 머리카락, 코트 모자,
화분 밖으로 뻗은 잎 같은 거예요.

그래서 가이드의 **높이 지도**를 같이 렌더해요. 픽셀마다 바닥에서 몇 m 위에 있는지 기록한 거예요. 높이가 h인 점의 그림자는 깊이와
상관없이 화면에서 "h × 빛의 이동량"만큼 떨어진 곳에 떨어져요. 그래서 그림의 각 픽셀이 그 아래 가이드의 높이를 가져와서 그만큼
옮겨져요. 가이드 밖으로 나간 머리카락이나 잎은 가장 가까운 가이드 지점의 높이를 써요.

모양은 그림 그대로이고, 시작점은 3D 모델이 정해요. 양쪽 발이 각자 자기 그림자를 시작하고, 화분 그림자는 화분 바닥에서 시작해요.
정확해야 하는 건 바닥에 닿는 부분뿐이라, 위로 갈수록(물체 높이의 10%에서 35%까지) 화면에서 읽은 부드러운 높이로 서서히 넘어가요. 그래서
머리카락, 모자, 잎의 그림자가 마네킹의 각진 모양이 아니라 자연스럽게 나와요. 바닥에 닿는 부분(블록의
아래 12cm, 즉 신발이나 화분 바닥)에는 가이드의 3D 그림자를 더해요. 그래서 그림자가 실제처럼 빛 반대쪽에서만 물체에 붙고, 앞쪽으로는 생기지
않아요. 포즈 잡은 인물과 `loose` 물건은 이 방식을 쓰고, 단단한 소품은 3D 그림자를, 걷는 캐릭터는 3D 몸의 그림자를(아래)
써요. `"shadow": "drawn" | "guide"`로 직접 고를 수도 있어요.

![블록 그림자와 그림 그림자 비교](docs/shadows.png)

## 걷는 캐릭터

![일러스트 → 3D → 그린 프레임 → 8방향 걷기](docs/character.ko.png)

![8방향 걷기](docs/character-walk.gif)

캐릭터 일러스트 한 장(정면을 보고 똑바로 선, 포즈 없는 그림)을 주면 그 그림체로 8방향 걷기(방향마다 8프레임)와 서 있는 8방향이 나와요. 이미지 모델은 프레임마다 몸과 자세를
일정하게 유지하지 못해서, 움직임은 3D에서 가져와요.
1. 일러스트로 턴어라운드를 그려요.
2. [Tripo](https://www.tripo3d.ai)가 턴어라운드로 3D 모델을 만들고, 리그를 달고, 걷기와 서 있기 동작을 입혀요.
3. 게임 카메라로 걷기를 렌더해요(무료). 프레임마다 3D 몸을 빛 방향으로 바닥에 눌러 붙인 그림자도 같이 렌더해요.
4. 이미지 모델이 렌더 위에 4프레임씩 그려요. 정면을 먼저 그리고 다른 방향은 모두 그걸 따라 그려서 같은 사람으로 유지돼요.
5. 각 프레임을 렌더에 다시 맞추고, 머리 크기를 고르게 하고, 가장자리를 정리해요. 결과는 스트립, 프레임마다 그림자(발이 그림자에
   닿고, 든 발은 따로 그림자가 생겨요), 앵커예요.

```
$PYTHON skills/spritecast/scripts/charpipe.py turnaround hero.json --yes   # 그다음 3d(모델, 리그, 렌더), draw(마무리, 미리보기까지 저절로)
```
기본으로 8방향을 다 그려요. 좌우가 같은 디자인은 `"mirror": true`로 서쪽 방향들을 동쪽에서 뒤집어 만들 수 있어요(그림자는 방향마다
자기 렌더에서). 약 $0.66 덜 들어요.

캐릭터 하나에 약 $2.2(OpenAI, `"mirror": true`면 약 $1.5), Tripo 75크레딧(약 $0.75, 동물은 30)이 들어요. 리그된 GLB가
있으면(`"rig_glb"`) 바로 `render`부터 하면 돼요.

`preview`는 `walk-all.mp4`(8방향이 한꺼번에 걷는 영상, ffmpeg가 있으면)도 만들어요. 머리가 커졌다 작아지거나 프레임이 튀는 게 가장 빨리
보여요. Tripo는 가끔 모델을 옆으로 돌려서, 또는 색 없이 보내는데 둘 다 자동으로 고쳐요. `"modeler": "meshy"`(와 `MESHY_API_KEY`)를
주면 [Meshy](https://www.meshy.ai)가 모델을 만들고(약 30 Meshy 크레딧), 리그는 그대로 Tripo가 해요.

다른 옵션(같은 사람의 여러 옷, 신발 바닥에 앵커 두기)과 요령은 [reference/character.md](skills/spritecast/reference/character.md)에
있어요. 위 여자아이 예시는 [`examples/rain_girl`](examples/rain_girl)에 있어요(일러스트, 턴어라운드, 사양, 스트립, 그림자, `character.json`, 전체 시트).
Tripo만으로 만들었고 그리기 약 $1.7, Tripo 85크레딧이 들었어요.

### 네발 동물

Tripo의 네발 동물 리그는 걸음이 어색해요(등뼈가 없고, 어깨가 목에 매달려 있어요). 그래서 동물은 리그를 사지 않아요.
`"kind": "animal"`을 쓰면 3D 모델(Tripo, 약 30크레딧)만 있으면 돼요. 뼈대(발, 등, 머리, 꼬리, 보는 방향)를 모델 모양에서 찾고,
고양이나 개의 걸음으로 걷고, 그리기, 맞추기, 3D 그림자는 사람과 같아요.

턴어라운드는 네 다리로 서서 다리가 서로 겹치지 않게, 꼬리는 뒤로 빼서 그려요. 옷은 몸에 붙는 것만(니트 조끼는 되고, 망토나 목도리는
안 돼요 - 늘어진 건 가까운 다리를 따라 움직여요). 그리기 전에 렌더를 확인하세요: 다리 넷, 머리는 앞, 꼬리는 뒤. Tripo 모델에 다리가
하나 더 생기면 다시 만들거나 Meshy(`"modeler": "meshy"`)로 만들어요.

![노란 비옷을 입은 치즈 고양이의 8방향 걷기](docs/animal-walk.gif)

고양이는 [`examples/tabby_cat`](examples/tabby_cat)에 있어요. 여자아이와 같은 노란 비옷을 입은 치즈 고양이예요(디자인, 턴어라운드, 사양,
스트립, 그림자, 시트). Tripo 30크레딧, 다시 그리기와 디자인 시도까지 그리기 약 $2.5가 들었어요. 프레임은 렌더와 0.76-0.97로
맞아요(north-east와 north-west는 `"mix"`로 프레임마다 섞었어요. reference/character.md 참고).

### 동작 추가: 달리기, 점프, 베기

걷기 말고도 달리기, 점프, 무언가를 휘두르는 동작을 만들 수 있어요. 설계도에 `"actions": ["run", "jump", {"name": "slash", "hold":
"umbrella"}]`처럼 적으면, 리깅할 때 Tripo에서 그 동작들을 받고(동작 하나에 약 10크레딧. 달리기, 점프, 베기, 쏘기, 뛰어들기, 오르기,
떨어지기, 맞기, 돌기가 있어요) 걷기처럼 8방향으로 렌더하고 그려서 동작마다 스트립과 프레임별 그림자를 만들어요. 베기처럼 손에
무언가가 필요하면 `"hold"`가 간단한 도형으로 물건을 만들어 오른손에 쥐여 줘서 모든 프레임에서 함께 움직여요(지금은 접힌 우산).
직접 리깅한 모델이면 그 안의 어떤 클립이든 동작으로 쓸 수 있어요.

![비옷 소녀가 달리고, 점프하고, 우산으로 베는 모습 - 앞과 뒤에서](docs/actions.gif)

**대부분 한 번에 나와요.** 비옷 소녀의 걷기, 달리기, 점프는 모두 한 번 그려서 모든 프레임이 3D 렌더와 0.78 이상 맞았어요. 우산 베기는
조금 더 까다로워요(가늘고 긴 물건이 몸 주위를 돌아요). 무기가 엉뚱한 곳에 그려지면 알아서 다시 그리고, 남는 건 허리를 깊이 숙이는
칸에서 몸을 조금 덜 숙여 그린 정도라 움직일 때는 자연스러워요. 그런 프레임은 목록으로 알려 주니 보고 두거나 다시 그리면 돼요.

**원하는 크기로**(요청이 있었어요): 프레임은 기본 256px 높이로 나오고, `charpipe.py pack CHAR.json --px 64`처럼 하면 같은 그림에서 원하는 높이로 한 벌 더 만들어요. 원본 프레임이 그린 그림의 디테일 그대로 남아 있어서 256보다 크게 해도 선명해요. 스트립, 그림자, `character.json`이 그 크기로 `out-64px/`에 나오고, 다시 그리지 않으며
`out/`은 그대로예요(설계도의 `"frame_px"`가 기본 크기). 아래는 512px, 256px(기본), 64px, 32px 높이를 같은 크기로 확대해서 보여 줘요(픽셀 그대로). 64px에서는 머리, 비옷,
장화, 우산이 다 보이고, 32px에서는 자세와 색은 남지만 얼굴은 거의 사라져요. 아직은 단순히 줄인 것뿐이에요([로드맵](#로드맵) 참고).

![달리기, 점프, 베기 - 512px, 256px(기본), 64px, 32px를 같은 크기로](docs/actions-small.gif)

### 그리기 건너뛰기: 3D 렌더를 그대로 프레임으로

사양에 `"draw": false`를 쓰면 프레임을 이미지 모델이 그리지 않아요. 3D 모델 자체의 렌더(툰 셰이딩, 모델 자체 텍스처)가 그대로
프레임이 되고, 3D 그림자와 앵커는 똑같이 나와요. 이미지 모델은 턴어라운드(약 $0.09)만 그려요. 리깅된 GLB를 직접 주면(`"rig_glb"`,
동물은 모델 `"model_glb"`) 이미지 모델을 아예 안 써요. 그러면 캐릭터 하나에 턴어라운드와 3D(Tripo 75크레딧, 동물 30)만 들고,
확인은 두 번, `3d`가 끝나면 바로 완성이에요. 대신 선명도가 떨어져요: 그린 선이 없고, 얼굴이 단순하고, 모델 텍스처가 그대로라 털과 주름이 흐려요.

![같은 여자아이와 고양이: 3D 렌더만 vs 그린 프레임](docs/render-vs-drawn.ko.gif)

![스트립 실제 픽셀로 확대: 3D만 vs 그림](docs/render-vs-drawn-zoom.ko.png)

## 카메라

| `camera` | 내려다보는 각도 | 어떤 게임에 |
|---|---|---|
| `"iso-2:1"` (기본) | 30°, 45° 회전 | 대부분의 아이소메트릭 게임. 바닥 타일이 가로 2 : 세로 1 |
| `"isometric"` | 35.26°, 45° 회전 | 정아이소메트릭(세 축이 120°) |
| `"topdown"` | 50°, 정면 | 3/4 탑다운 RPG |
| `"front"` | 12°, 정면 | 횡스크롤 |
| `{"pitch": 40, "yaw": 30}` | 아무 각도 | 직접 지정 |

`"light": "left"`로 바꾸면 빛과 그림자가 반대쪽으로 가요.

걷는 캐릭터는 `camera` 대신 `"pitch"`만 받아요: 30(기본, 2:1), 35.26(정아이소메트릭), 50(3/4 탑다운), 12(정면). 8방향은 45°
간격이에요. `camera`는 소품과 포즈 잡은 인물에 써요.

## 엔진에 넣는 법

`sprite.json`에 소품이 땅에 닿는 지점이 적혀 있어요.

```json
"sprite": { "file": "sprite.png", "size": [299, 357], "anchor": [0.4993, 0.9966], "anchor_px": [149.3, 355.8] },
"shadow": { "file": "shadow.png", "offset_px": [-66, 116] },
"px_per_m": 256
```

- **anchor**: 바닥 차지 면적의 앞 모서리예요. 정면 시점에서는 앞쪽 변의 가운데예요. 이 점을 소품이 놓일 타일 위에 맞춰요.
- **shadow**: `shadow.png`를 스프라이트 왼쪽 위 모서리에서 `offset_px`만큼 떨어진 곳에 놓아요. 불투명도는 30% 정도로, 모든
  스프라이트 아래에 그려요.
- **scale**: 모두 1m당 `px_per_m` 픽셀로 그려져 있어요. 타일이 1m이고 가로 `T`픽셀인 2:1 맵이면 `T / 1.414 / px_per_m` 배로
  줄이면 돼요.

| 엔진 | 방법 |
|---|---|
| Phaser | `this.add.image(x, y, 'armchair').setOrigin(anchor[0], anchor[1])` |
| Godot 4 | `Sprite2D`: `centered = false`, `offset = -anchor_px` |
| Unity | Sprite Editor → Pivot: Custom, `(anchor[0], 1 - anchor[1])` |

**걷는 캐릭터.** `character.json`에 `frame`(`[w, h]` 픽셀), `anchor`(두 발 사이, 프레임에 대한 비율), `fps`가 있어요.
`walk-<facing>.png`는 8프레임을 가로로 붙인 스트립이고, `idle-<facing>.png`는 한 프레임이에요. 한 방향의 `i`번째 그림자
`shadows.walk[facing][i]`는 `i`번째 프레임의 왼쪽 위 모서리에서 `offset`만큼 떨어진 곳에, 30% 정도 불투명도로 모든 것 아래에
그려요. `px_per_m`은 없어요: 캐릭터가 서 있을 키에 맞춰 프레임 크기를 조절하세요. Phaser에서 `rain_girl`의 수치로:

```js
this.load.spritesheet('girl-se', 'walk-south-east.png', { frameWidth: 165, frameHeight: 256 });
this.anims.create({ key: 'walk-se', frames: this.anims.generateFrameNumbers('girl-se'), frameRate: 6.76, repeat: -1 });
this.add.sprite(x, y, 'girl-se').setOrigin(0.4926, 0.8839).play('walk-se');
```
전체 형식은 [reference/character.md](skills/spritecast/reference/character.md#output-nameout)에 있어요.

## 앉기

![비 오는 소녀가 8방향으로 앉은 모습과, 예시 안락의자에 앉아 앞 조각에 가려진 모습](docs/sitting.png)

걷는 캐릭터가 있으면 Claude에게 *"앉혀 줘"*라고 해 보세요. 3D 모델을 앉은 자세(허벅지 수평, 무릎 굽힘, 손은 허벅지 위)로 8방향
렌더하는 건 무료예요. 렌더를 확인한 뒤 서 있는 모습처럼 그려요(시트 2장, 약 $0.22). 의자 없이 앉아 있어서 게임의 의자를 밑에
두면 돼요. `character.json`에 `sit`이 생겨요. 방향마다 파일, **앉는 점**(의자 좌석에 맞출 점, `anchor`처럼 프레임의 비율), 좌석
높이, 그림자가 들어 있어요. 소품에 앉히려면 `seat.py`가 좌석 위에 앉히고, 캐릭터를 가리는 **앞 조각**(팔걸이, 장의자 등받이, 벤치
등받이)을 둘의 3D 높이로 계산해요. 칠할 필요가 없어요.

![비 오는 소녀가 열 가지 좌석에 앉은 모습: 네 방향 안락의자, Tripo 안락의자, 식탁 의자 앞뒤, 장의자, 곡선 벤치 앞뒤](docs/seats.png)

좌석 높이와 방향을 찾고, 무릎이 좌석 앞 모서리에 오도록 엉덩이 위치를 정해요. 조금 어긋나 보이면 다듬기 페이지(아래)에서 끌어서
옮기면 돼요. 놓는 순간 그 자리에서 앞 조각을 다시 계산해요.
자세한 내용은 [reference/sitting.md](skills/spritecast/reference/sitting.md)에 있어요.

```
$PYTHON skills/spritecast/scripts/charpipe.py sit <name>.json            # 무료: 앉은 렌더
$PYTHON skills/spritecast/scripts/charpipe.py sit <name>.json --draw     # 약 $0.22: 그리고 마무리
$PYTHON skills/spritecast/scripts/seat.py <prop>.json <name>.json --height 1.3   # 무료: 소품에 앉히고 앞 조각 계산
```

## 손으로 다듬기

![좌석 셋: 자동으로 계산한 앞 조각과, 같은 좌석을 손으로 칠하고 캐릭터를 옮긴 결과](docs/touchup.png)

자동 단계로 대부분은 되지만, 마지막은 눈으로 보고 손으로 하는 게 가장 정확해요. **손으로 칠하는 게 어떤 자동 단계보다
정확해요.** 위 그림에서 장의자는 자동 계산으로는 등받이가 소녀를 거의 다 가렸는데, 손으로 칠하고 소녀를 위로 옮기니 제대로
앉아 보여요. 식탁 의자와 안락의자 등받이도 엉뚱한 곳을 잘랐던 걸 손으로 고쳤어요. 누끼도 늘 완벽하지는 않아요. 팔과 몸 사이에 종이가 조금 남거나, 흰 셔츠를 종이로 알고 지우기도 해요. Claude에게 다듬기 페이지를
열어 달라고 하거나 `$PYTHON skills/spritecast/scripts/touchup.py <spec>.json`을 실행하면, 그 소품이나 캐릭터의 완성된 그림이
전부 브라우저에 떠요. 칠하는 대로 저장돼요.

| 색 | 하는 일 |
|---|---|
| 빨강 | 지우기: 투명하게 |
| 초록 | 되살리기: 그 픽셀을 원래 그림에서 가져와요("drawing under"를 켜면 원래 그림이 밑에 보여요) |
| 파랑 (소품) | **앞 조각**: 그 안에 선 캐릭터보다 앞에 오는 부분. 아치의 앞 기둥, 정자 지붕, 의자의 앞쪽 팔걸이 |
| ⬠ 다각형 (P) | 꼭짓점을 클릭하고 닫으면(더블클릭, Enter, 첫 점 클릭) 지금 칠하는 색으로 채워지거나 지워져요 |
| 🪑 (좌석) | 앉은 캐릭터를 끌어서(또는 방향키로) 옮겨요. 놓으면 그 자리에서 좌석과 앞 조각을 다시 만들어요 |

다 칠하면 `touchup.py <spec>.json --apply` (캐릭터는 스트립을 다시 묶어요). 앞 조각을 칠한 소품은 `sprite-front.png`와
`sprite.json`의 `"front"`가 생겨요. 소품을 캐릭터 뒤에 그리고 앞 조각을 그 위에 그리면 돼요. `finish`를 다시 돌려도 칠한 내용은
다시 입혀지고, 칠한 뒤에 다시 그려진 그림에는 입히지 않고 따로 빼 둬요.

## 작동 방식

| 단계 | 내용 | 비용 |
|---|---|---|
| 사양 | Claude가 `<name>.json`을 써요: 바닥 크기, 미터 단위 블록, 완성품 설명 | 무료 |
| `render` | 헤드리스 Chrome에서 three.js로 가이드, 그림자, 모델 입력을 만들어요 | 무료 |
| `draw` | OpenAI 이미지(기본 `gpt-image-2.5-sunburst`)가 가이드를 내 그림체로 다시 그려요 | 약 $0.07 |
| `finish` | 배경을 부드럽게 빼고, 가이드 영역에 맞추고, 그림자를 굽고, 앵커를 재요 | 무료 |
| `preview` | 1m 격자 바닥 위에 놓아 봐요 | 무료 |

직접 실행할 수도 있어요: `$PYTHON skills/spritecast/scripts/isoprop.py render|draw|finish|preview examples/reading_armchair.json`
(`$PYTHON`은 [설치](#설치) 참고). `draw`는 `--yes`를 붙이기 전까지 비용만 보여 줘요. 사양 형식은 [reference/spec.md](skills/spritecast/reference/spec.md), 좋은
가이드를 짜는 요령은 [reference/tips.md](skills/spritecast/reference/tips.md)에 있어요.

## 문제가 생기면

| 문제 | 해결 |
|---|---|
| `No module named ...` | `python3 skills/spritecast/scripts/doctor.py`가 찍는 `PYTHON=`으로 스크립트를 돌려요(준비가 안 됐다고 나오면 먼저 `--fix`. Claude가 대신 해요) |
| 브라우저 없음 | Chrome 설치, 또는 `doctor.py --fix --browser` (Playwright의 Chromium, ~150 MB) |
| `this Python cannot make a venv` | Debian/Ubuntu: `sudo apt install python3-venv`, 또는 다른 Python(python.org, conda) |
| `draw: set OPENAI_API_KEY` | 플러그인 설정(`/plugin` → SpriteCast)에 키를 넣거나 환경 변수로 설정하고(위) Claude Code를 다시 켜요 |
| `HTTP 401` / `403` | 키가 틀렸거나, OpenAI가 이미지 모델을 쓰기 전에 조직 인증을 요구해요(platform.openai.com → Settings → Organization) |
| `finish: WARNING - the drawing does not follow the guide` | 모델이 다른 각도나 모양으로 그렸어요. 이 카메라에서 보이는 모습을 설명에 적고, 가이드를 확인한 뒤 `--again`으로 다시 그려요. 식물처럼 가이드 밖으로 삐져나와도 되는 건 `"loose": true` |
| 그림에 없던 게 추가됨 | 설명에 들어가면 안 되는 걸 적고("러그 없이, 로고 없이") 다시 그려요 |
| 모양이 틀림 | 블록을 고쳐요. 그림은 가이드를 따라가요 |

## 무엇을 보내고 받나요

아래 단계를 빼면 전부 내 컴퓨터에서 돌아가요. 돈이 드는 단계는 비용을 먼저 알려 주고 OK를 기다려요.

| 언제 | 어디로 | 무엇을 |
|---|---|---|
| `draw` | OpenAI (`api.openai.com`) | 가이드 그림, 그림체 그림, 설명 글, 그리고 `OPENAI_API_KEY` |
| 캐릭터: `turnaround`, `draw` | OpenAI | 일러스트, 턴어라운드, 3D 렌더, 같은 키 |
| 캐릭터: `3d` | Tripo (`openapi.tripo3d.ai`) | 턴어라운드 네 면, `TRIPO_API_KEY`. 모델과 리그, 걷기가 돌아와요 |
| `model` (소품, 선택) | Tripo | 설명 글 |
| 캐릭터, `"modeler": "meshy"` (선택) | Meshy (`api.meshy.ai`) | 네 면, `MESHY_API_KEY` |

키는 환경변수에서만 읽고, 각자 자기 서비스로만 보내고, 파일에 쓰거나 화면에 찍지 않아요. 내려받는 것:

| 무엇 | 어디서 | 언제 |
|---|---|---|
| numpy, pillow, scipy, playwright, onnxruntime | PyPI, 전용 가상환경(`~/.cache/spritecast/venv`)으로 | `doctor.py --fix`, 한 번 |
| Chromium (~150 MB) | Playwright 서버 | Chrome이나 Edge가 없을 때만, 물어본 뒤에 |
| 오려내기 모델 BiRefNet lite (224 MB, MIT), `SPRITECAST_KEY_MODEL=general`이면 전체 모델 (973 MB) | [rembg의 GitHub 릴리스](https://github.com/danielgatis/rembg/releases/tag/v0.0.0), md5 확인 | 캐릭터, 첫 `finish` 때 |
| 얼굴 랜드마크 모델 MediaPipe Face Landmarker (3.7 MB, Apache-2.0). `mediapipe`는 따로 `pip install` | Google (`storage.googleapis.com/mediapipe-models`) | `facecheck`(선택)만, 처음 한 번 |

렌더는 내 컴퓨터의 헤드리스 브라우저에서 돌고 인터넷에서 아무것도 불러오지 않아요. three.js는 플러그인에 들어 있어요
(`skills/spritecast/scripts/vendor/three/`, MIT).

## 로드맵

다음에 할 일이에요. 대략 이 순서지만 날짜는 정하지 않았고, 피드백에 따라 바뀌어요.
- **좌석에 맞춘 자세와 탑승** (앉기 자체는 이미 돼요. 위의 '앉기' 참고): 지금은 어느 의자든 같은 앉은 자세 하나를 쓰는데, 좌석마다 맞춘 자세(깊은 소파에 기대 앉기, 놀이기구 발판에 발 올리기)와 수레·탈것에 타기를 더해요.
- **도는 물체**: 탈것이나 놀이기구를 여러 각도로 돌려서, 8방향 사이를 툭툭 끊기지 않고 부드럽게 돌아요.
- **밤 버전**: 빛나는 부분(창문, 전구, 네온) 마스크. 엔진에서 밤에 그 부분만 켤 수 있어요.
- **지나갈 수 있는 소품 자동화**: 앞 조각을 3D 가이드에서 자동으로 계산해요(지금은 다듬기 페이지에서 손으로 칠해요).
- **동작과 쥘 물건 더하기**: 달리기, 점프, 베기는 들어갔어요. 다음은 쥘 물건 더하기(칼, 지팡이)와 숨쉬는 대기 동작.
- **작은 스프라이트**: 줄일 때 픽셀아트로 다듬는 단계(1px 외곽선, 적은 색, 3D 머리 위치로 찍는 눈), 그리고 32px 이하에서는 얼굴이
  남도록 같은 리그에서 머리를 키운 비율.
- **엔진용 내보내기**: 스프라이트 시트와 함께 Godot, Unity, Aseprite에서 바로 불러올 파일.

버전마다 무엇이 바뀌었는지는 [CHANGELOG.md](CHANGELOG.md)에 있어요.

## 피드백

다음에 무엇을 할지는 피드백으로 정해요. 피드백으로 바뀐 것은 변경 기록에 표시해요.
- **고장 났을 때**: [이슈](https://github.com/Sunghwan0112/spritecast/issues/new/choose)에서 버그 양식으로 알려 주세요. OS, Python 버전, 실행한 명령,
  오류 메시지가 있으면 가장 빨리 고칠 수 있어요.
- **아이디어나 없는 기능**: [이슈](https://github.com/Sunghwan0112/spritecast/issues/new/choose)의 기능 요청 양식.
- **만든 것 보여 주기, 사용법 질문**: [Discussions](https://github.com/Sunghwan0112/spritecast/discussions).

## 참고
- 만든 결과물은 사용자 것이에요.
- 실제 브랜드, 로고, 기존 게임 캐릭터는 설명에 넣지 마세요.
- 살아 있는 작가의 그림은 허락 없이 스타일 그림으로 쓰지 마세요.
- 캐릭터 얼굴을 닮게 하는 `photo`는 동의한 사람의 사진만 쓰세요.
- 단단한 소품은 블록의 3D 그림자, 포즈 잡은 인물과 `loose` 물건은 그림 모양 그대로의 그림자(그림자 항목 참고), 걷는 캐릭터는
  3D 몸의 그림자를 받아요.
- 설정: `SPRITECAST_MODEL`, `SPRITECAST_QUALITY` (`low` | `medium` | `high`).

## 자주 묻는 질문
- **얼마 드나요?** 가이드, 마무리, `try`는 무료예요. 소품 약 $0.07, 방향을 하나 더할 때마다 $0.08, 걷는 캐릭터는 그리기 약
  $2.2(`"mirror": true`면 약 $1.5)와 Tripo 75크레딧(동물 30)이에요. 돈이 드는 단계는 비용을 먼저 보여 주고 OK를 기다려요.
  플러그인은 무료이고, OpenAI와 Tripo에 직접 내요. 만든 사람에게 가는 돈은 없어요.
- **어떤 키가 필요하나요?** 그리려면 `OPENAI_API_KEY`, 걷는 캐릭터와 동물은 `TRIPO_API_KEY`(Meshy는 선택)예요. OpenAI가 먼저
  조직 인증을 요구할 수 있어요. [키](#설치) 참고.
- **AI 그림 아닌가요?** 맞아요. 그림은 이미지 모델이 그려요. SpriteCast가 더하는 건 형태예요: 크기, 카메라 각도, 걸음, 그림자가
  3D에서 나와요. 내 그림을 스타일로 줄 수도 있고, `"draw": false`로 걷는 캐릭터의 프레임을 이미지 모델 없이 3D 렌더로 쓸
  수도 있어요. 턴어라운드는 여전히 이미지 모델이 그려요(리깅된 모델을 직접 주면 빼고요)
  ([그리기 건너뛰기](#그리기-건너뛰기-3d-렌더를-그대로-프레임으로)).
- **못 하는 건 뭔가요?** 걷는 캐릭터는 걷기와 서 있기만 하고(다른 동작은 [로드맵](#로드맵)에 있어요), 정면을 보고 똑바로 선
  일러스트에서 시작해요. 포즈 잡은 한 장짜리 인물(손 흔들기, 가리키기, 들기...)은 설명만 있으면 돼요. 러그처럼 크고 납작한 건 위에서 그려서 바닥에 기울여 붙이는 게 나아요
  ([요령](skills/spritecast/reference/tips.md)). 결과는 직접 보세요: 머리가 엉뚱한 쪽을 보는 건 윤곽 검사로 못 잡아요.
- **어떤 엔진에서 쓰나요?** PNG를 받는 엔진이면 다 돼요. 스프라이트, 그림자, 앵커(JSON)를 받아요. Phaser, Godot, Unity는
  [엔진에 넣는 법](#엔진에-넣는-법) 참고.

## 라이선스
MIT. 동봉한 three.js(`skills/spritecast/scripts/vendor/three`)도 MIT이고 © three.js authors예요.
