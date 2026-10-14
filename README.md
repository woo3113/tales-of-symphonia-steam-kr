# Tales of Symphonia (Steam) — 한글패치 네이티브 전환

Steam판 **테일즈 오브 심포니아**(appid `372360`, `TOS.exe`)의 기존 한글패치를
**GPU 무관 네이티브 패치**로 바꾸는 리버싱/툴체인 프로젝트 (WIP).

> **이 저장소에는 게임 데이터/폰트/패치 바이너리를 포함하지 않습니다.** 소스·스크립트·리버싱 노트만 있습니다.

## 왜 "네이티브"인가

기존 한글패치(`korfnt`)는 **D3D9 런타임 후킹**으로 게임 위에 한글을 직접 그립니다.
그 렌더 경로가 드라이버에 민감해 **NVIDIA에서만 정상**, AMD/Intel에서는 폰트가 깨집니다.

이 프로젝트는 후킹 대신 **게임 자체 폰트 파이프라인을 패치**해 한글을 그리게 합니다 →
렌더는 원래 게임 경로(D3D9)를 그대로 쓰므로 **어느 GPU에서나 동작**합니다.

## 근본 원인 (확정)

- 게임 UI 텍스트는 **단일바이트 코드** 모델. 2바이트로 인식되는 코드는 `[0x8101,0x81FF]`(255개)뿐.
- 한글패치 번역 텍스트는 **EUC-KR(2바이트)** → 엔진이 1바이트로 잘라 읽음 → 깨짐.

## 패치 개요 (핵심 5가지)

| # | 대상 | 내용 |
|---|---|---|
| 1 | 텍스트 길이 규칙 **26곳** | 한글/EUC-KR을 2바이트로 읽게 (`leal +0x7EFF` 사이트의 `mov R3,0xFE` 자리) |
| 2 | 문자 변환기 **5곳** | `EUC-KR → 0x4000+idx`, ASCII 유지/매핑 |
| 3 | 글리프 슬롯 함수 `0x578680` | 글리프 코드 → 아틀라스 좌표 |
| 4 | 폭 함수 `0x57ACD0` | 한글 전각(48) 반환 |
| 5 | 폰트 아틀라스 `PAL_FONTB0` | 우리 한글 아틀라스로 교체(TLDAT 재패킹) |

## 엔진 리버싱 요약 (확인된 사실)

- **글리프 아틀라스 = `PAL_FONTB0`** (컬러코딩 실험으로 확정 — FONTTYPE*_PIC 페이지는 대사에 안 쓰임)
- 주요 함수
  - `0x57A810` 문자 변환기, `0x578680` 글리프 슬롯, `0x57ACD0` 폭
  - `0x57A880` 메인 텍스트 레이아웃/그리기 루프
- 폰트 셀 **48px**, 글리프 vertex = `(x,y,z,u,v,rgba)`, V span = `row*48 + 48`(하드코딩 `@0x882a30=48.0`)
- 리소스 아카이브: `FILEHEADER.TOFHDB`(바이너리 인덱스) + `TLFILE.TLDAT`(데이터),
  압축은 **TLZC = 24B 헤더 + raw DEFLATE** (파이썬 zlib 만으로 해제/재압축 가능)
- 폰트 텍스처 페이지: `FONTDATA/A/B/C × PIC000~019`, `PAL_FONTB0` (DXT5)

## 진행 상태

- ✅ 게임 내 확인(AMD RX 9070 XT): 대사창·나레이션·메뉴·화자 이름표·설정 설명칸·K 버튼 행동명 한글, 일본어 음성 설정 유지
- ✅ 최종 조합: 아틀라스 21페이지(3855글리프) + `src/korfnt_kr.c`(logger23 릴리스 빌드)
- 🧪 **베타 0.1**: 한글패치 1.0 위에 덮어씌우는 추가패치 — [`beta/`](beta/설명서.md), [`docs/C_beta_0.1.md`](docs/C_beta_0.1.md)
  (다른 사람의 번역·로더 파일은 포함하지 않음)
- ⏳ 베타 배포본 글꼴(Noto → 나눔고딕 교체 예정) 게임 내 최종 확인, 글꼴 그림 변환 스크립트 추가

자세한 일지/명세: **[`docs/B_spec.md`](docs/B_spec.md)**, 초기 구조 분석: **[`docs/analysis.md`](docs/analysis.md)**

## 저장소 구성

```
docs/    B_spec.md (작업 명세·실험 일지), analysis.md (초기 구조 분석)
src/     로거/패처 C 소스 (mingw32 gcc) — logger*.c, patcher*.c, lensites.h 등
tools/   리버싱·빌드 파이썬 스크립트 (PE 분석, TLZC, 아틀라스 생성, TLDAT 재패킹 등)
```

## 빌드 / 실행 (Windows)

```bat
:: 1) 패치 DLL 빌드 (msys2 mingw32 필요)
set PATH=C:\msys64\mingw32\bin;%PATH%
gcc -shared -O2 -s -o korfnt_logger15.dll logger15.c -lkernel32

:: 2) 데이터+ DLL 설치 (게임은 켜지 않음)
py -3.12 install_build.py tppal17 korfnt_logger15.dll

:: 3) 게임 실행 후 스크린샷으로 확인

:: 4) 원복 (필수)
copy backup\TLFILE.TLDAT.orig        "…\R01\WIN\TLFILE.TLDAT"
copy backup\FILEHEADER.TOFHDB.orig   "…\R01\WIN\FILEHEADER.TOFHDB"
copy korfnt\korfnt.dll.real          korfnt\korfnt.dll
```

게임 데이터 경로: `…\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\`

## 원본 무결성 (테스트 후 복구 기준 SHA-256)

| 파일 | SHA-256 |
|---|---|
| `TOS.exe` | `01CAD33820C383B938452ACB60EED21262152B9F85F29BFBBCEE04D51D3A7104` |
| `korfnt\korfnt.dll` | `93679A069EB50BA957524681C644EE78658F327711BA6A4A9D8B2C04B98576E7` |
| `R01\WIN\TLFILE.TLDAT` | `2451FFA6B0D844C32CEA418D8129D46B267E95BC1FF6B4D7E8776F416E588283` |

## 주의 · 법적 고지

- 이 저장소는 **게임 데이터, 폰트, 번역 텍스트, 패치 바이너리를 포함하지 않습니다.**
- 사용자는 **정품 게임**과 **자신이 보유한 번역 데이터**로만 위 스크립트를 사용해야 합니다.
- 개인 학습/연구 목적의 리버싱 노트입니다. 게임 및 폰트의 권리는 각 권리자에게 있습니다.
