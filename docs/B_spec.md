# Tales of Symphonia (Steam) 한글패치 → 네이티브(B) 구현 명세

## 목표
NVIDIA 전용 후킹 패치를 **GPU 무관 네이티브 패치**로 전환. AMD / Intel Arc에서도 한글 출력.

## 근본 원인 (확정)
- 이 게임 UI 텍스트는 **단일바이트(라틴)** 모델. 2바이트로 인식되는 코드는 `[0x8101,0x81FF]`(255개)뿐.
- 한글패치 텍스트는 **EUC-KR(2바이트)** → 엔진이 1바이트로 잘라 읽음 → 깨짐.
- 원 패치(korfnt.dll)는 **엔진 폰트 렌더링을 자체 BMFont 시스템으로 대체**해 해결:
  1. 텍스트 루프 2곳 후킹 → 리더 `0x10001F80`: DBCS 규칙(lead≥0x81, trail 0x40~0xFE)으로 2바이트 코드 읽기
  2. `MultiByteToWideChar(cp949)`로 유니코드화
  3. BMFont 맵(BST `0x10002E20`) 조회 → `ctx->0x20`에 글리프코드 설정
  4. 아틀라스 치수 `1728→4096` 패치(`0x10002240`) + PAL_FONTB0에 4096² 아틀라스(korfnt_0.dds)
- **korfnt는 이 PC(AMD)에서 훅을 설치하지 않음**(게이트) → "NVIDIA 전용" 실체.

## korfnt 후킹 지점 (TOS.exe 10곳)
| foundAddr | 역할 | hook = found-12 |
|---|---|---|
| 0x57A81C | 변환기 | 0x57A810 |
| 0x57A990 / 0x554E1E | 변환기 중복본 | 0x57A984 / 0x554E12 |
| 0x578680 | 글리프 슬롯 | 0x578674 |
| 0x57ACD0 | 폭 함수 | 0x57ACC4 |
| 0x57AD04 | 폭 내부 | 0x57ACF8 |
| 0x53281B | 폭/테이블 | 0x53280F |
| 0x4D783A / 0x4D7C86 | 텍스트 루프 | 0x4D782E / 0x4D7C7A |
| 0x4D77C4 | 텍스트 루프 | 0x4D77B8 |
| 0x594CDB / 0x62666E | 기타 | 0x594CCF / 0x626662 |

## 핵심 코드 (TOS.exe)
- 변환기 0x57A810: `c<0x80→전각표(0x8AD868)`, `0x80≤c≤0xFF→c+0x8220`, `c>0xFF→0x831F`
- 글리프 슬롯 0x578680: 아틀라스 16열, `col=slot&0xF`, `row=(slot>>4)+group*12`
- 폭 0x57ACD0, 텍스트 길이규칙: `lea reg,[code+0x7EFF]; cmp ax,0xFE; ja len1` (2바이트 iff code∈[0x8101,0x81FF]) — **27곳 중복**
- 그리기 루프 0x57A880: 2바이트 읽어 code=(b0<<8)|b1 → 폭 호출
- 폰트: TLFNTB_D(메트릭) / FONTDATA·FONTTYPE A/B/C_PIC / PAL_FONTB0. 셀 48px, 16×12, 768×576 DXT5 mips3.

## 엔진 ctx 구조 (korfnt 리더가 사용)
- `+4` = 문자 버퍼 포인터 (또는 +8과 반대일 수 있음)
- `+8` = 바이트 인덱스
- `+0x10` = 글리프/레이아웃 노드
- `+0x20` = 결과 글리프 코드 (0x8276 = 기본)
- `+0x24` = 커서(호출 주소) → 어느 루프인지 구분 (A=[0x1003CB30], B=[0x1003CB34])

## 우리(B) 구현 계획
1. **텍스트 루프 2곳 함수단위 후킹 + DBCS 리더 이식**
   - 규칙: lead byte ≥0x81 (≠0xFF), trail ∈[0x40,0xFE] (≠0x7F,0xFF) → 2바이트 코드
2. **코드 매핑**: EUC-KR 코드 → 우리 슬롯
   - 공식: `slot = (b0-0xB0)*94 + (b1-0xA1)`  (한글) ; ASCII는 별도
   - (MultiByteToWideChar 불필요 — 공식으로 직접)
3. **글리프 처리**: 슬롯 → 페이지/행/열 후 엔진 글리프 함수(0x578680) 경로에 전달
4. **폰트 아틀라스**: 우리 13페이지(768×576, 엔진 토착 포맷)를 폰트 페이지에 배치
   → 치수 패치 불필요(1728/768 유지) 가능
5. **변환기/폭**: 우리 슬롯 기준으로 처리
6. 게임 내 반복 테스트

## 주의
- 길이규칙 27곳 **일괄 패치** 및 그리기 루프 1곳 단독 패치는 **게임 크래시** 유발 → korfnt처럼 **함수 단위 정밀 후킹** 필요.
  (2026-10-13 재현: 순진한 일괄 패치는 원래 1바이트 문자까지 2바이트로 만들어 파싱이 어긋나 크래시)
- 모든 테스트 후 게임 폴더는 원본 SHA로 복구할 것:
  - TOS.exe: 01CAD33820C383B938452ACB60EED21262152B9F85F29BFBBCEE04D51D3A7104
  - korfnt.dll: 93679A069EB50BA957524681C644EE78658F327711BA6A4A9D8B2C04B98576E7
  - TLDAT: 2451FFA6B0D844C32CEA418D8129D46B267E95BC1FF6B4D7E8776F416E588283

## 산출물 위치
- 로깅/패처 DLL 소스: work\logger*.c, patcher*.c (mingw32 gcc로 빌드)
- 한글 아틀라스: work\kf13\page_00..12.dds (+ png)
- 인덱스/엔트리 파서: work\dump_index.py, extract_cmp.py 등

---

# 부록 A — 2026-10-13 런타임 검증 (이어서 작업분)

## A.1 훅 설치는 AMD에서도 성공 (핵심 긍정 결과)
- 우리 로거 DLL(`work\logger6.c` → `korfnt_logger6.dll`)을 `korfnt\korfnt.dll`로 교체해
  TOS.exe 프로세스 내부에서 코드 패치를 수행 → 훅이 **정상 설치·동작**했고, 게임이 25초 이상
  살아 있으면서 로그가 축적됨(원본 korfnt는 AMD에서 아무것도 안 함).
- 결론: **"AMD라서 코드 패치가 안 된다"는 아님.** 후킹 기반 네이티브화의 전제가 성립.

## A.2 런타임 텍스트는 1바이트(ASCII) + 0x81xx 2바이트 이스케이프
`0x57A880`(메인 텍스트 루프 선두 `0x57A8B0`)을 탭해 얻은 실제 스트림:

```
ptr=29A07476 bytes="as t"     ptr=...477 "s th"   ...478 "the" ...479 "the "
...  "e of" " of " "f ma" " man" "mana" "ana." 
...  "Once" "Once " "nce u" "ce up" "e upo" "upon" "on a" " a t" "a tim" "time" "ime,"
```
- 포인터가 **1바이트씩 증가** → ASCII는 1바이트 문자로 전진.
- 폭/변환기 입력도 ASCII(0x20,0x65'e',0x74't',0x61'a' …)이며, 글리프 함수 출력은
  전각 SJIS 코드(`0x8140`=공백, `0x8285`='e', `0x8294`='t', `0x8281`='a', …).
- 매핑: `ASCII → 표(0x8AD868) → 전각 SJIS 글리프(0x8140..0x833F)` → glyph group **0/1**.
- 즉 **2바이트로 취급되는 텍스트 코드는 `[0x8101,0x81FF]` 뿐**이라는 B_spec 가정이 런타임에서 확인됨.
- 한글(EUC-KR 0xB0A1..0xC8FE)은 이 규칙에서 1바이트로 잘림 → 반드시 길이규칙 패치 필요.

## A.3 길이규칙 사이트 = 27곳 (전수 조사)
`lea R2,[R+0x7EFF]` + `cmp R2w,0xFE` + `ja` 패턴. 코드 레지스터 R은 lea의 base(rm):

```
460973 460A50 4D7426 4D7A52 4D7D61 4F961E                                (.text)
53228D 53243D 5325A4 5326FC 53297C 532A94 5387AD 538985 538B17 538C77
54C345 54D4BC 55308D 5538AD 553AF0 554D5D 57355F 57619D 576827
57A8DA 57AB31
```
- 대부분 `lea …; mov R3,0xFE; cmp R2w,R3w; ja len1` 형태이며 `mov R3,0xFE`가 **5바이트**라
  패치 지점으로 적합.
- 주의(다른 형태): `4D7D61`은 lea와 cmp 사이에 `add esp,4`가 끼어 있고,
  `4F961E`·`55308D`는 즉시값 대신 레지스터 비교(`cmp cx,di`)라 별도 처리 필요.

## A.4 변환기 중복본 = 11곳
`B9 80 00 00 00 66 3B C1` (`mov ecx,0x80; cmp ax,cx`) 패턴:
```
4B93FD 4B9442 52E66A 52E6D1 532895 537F92 537FE2 5388E6 57A81C 57AC82 57AD8D
```
- `57A81C` = 단독 변환기(0x57A810) 본체. 나머지는 **인라인 복제본** →
  한글 매핑을 넣으려면 이들을 모두 고쳐야 함(메인 루프는 인라인 복제본을 사용).

## A.5 폰트 페이지 전수 (TDAT 디스크립터 이름 복원)
- `FONTDATA_PIC000..019`  idx 83201..83239 (20장)
- `FONTTYPEA_PIC000..019`  idx 83241..83279 (20장)
- `FONTTYPEB_PIC000..019`  idx 83281..83319 (20장)
- `FONTTYPEC_PIC000..019`  idx 83321..83359 (20장)
- `PAL_FONTB0`             idx 83361 (768×1728 DXT5 mips3)
- 각 페이지 = **768×576 DXT5 mips3, 580736B(+4B 프리픽스)** → 우리 `kf13\page_00..12.dds`와
  **동일 포맷** → 치수 패치 없이 페이지 교체 가능(4종×13 = 52장, 약 29MB).
- 글리프 group(0..0x13=20) = 페이지 번호, `row=(slot>>4)+group*12` → 페이지를 세로로 쌓아
  한 텍스처로 보는 좌표계. ASCII/기호는 group 0/1 사용 → 한글은 group 2..14 사용 가능.

## A.6 로거 버그 수정 메모 (재현 방지)
- 초기 패처가 **VA/RVA를 혼용**(`base+0x57ACD0` 처럼)해 엉뚱한 주소를 패치 → 크래시.
  반드시 `base(모듈베이스) + RVA`.
- 로그 스텁이 **ecx를 보존하지 않아** glyph 함수의 `this`(ecx) 인자를 파괴 → 크래시.
  모든 탭 스텁은 eax/ecx/edx를 보존해야 함. (수정판: `logger6.c`)

## A.6b 검증 완료: 길이규칙 26곳 동시 패치 성공 (2026-10-13)
- `gen_lensites.py`가 27곳 중 `mov R3,0xFE`(5B)를 갖는 **26곳**을 자동 추출 →
  `lensites.h` 생성. 각 사이트의 코드 레지스터 R(lea의 base)과 len1/len2 목적지 확정.
  - 1곳(`0x4F961E`)은 `cmp cx,di`처럼 즉시값 로드가 없어 별도 처리 필요.
- 스텁(설계): `push eax; movzx eax,Rw; sub eax,0xB0A1; cmp eax,0x185D; jbe L_kr;
  pop eax; mov R3,0xFE; jmp resume; L_kr: pop eax; jmp len2`
  - `mov R3,0xFE`(5B)에 그대로 덮어써 패치. eax를 저장/복원하므로 다른 레지스터 영향 없음.
  - 2바이트 조건 = `code∈[0x8101,0x81FF]`(원래) ∪ `code∈[0xB0A1,0xC8FE]`(한글).
- `logger7.c`(26곳 일괄 패치) 실행 결과: **npatched=26, 크래시 없음**, 그리고
  영어 텍스트가 **완전히 원래와 동일**하게 파싱됨(1바이트 전진 유지, ASCII 코드 동일).
  → 길이규칙 일괄 패치 자체는 안전. (순진한 ">=0x8101 전부 2바이트" 패치만 크래시 원인)

## A.7b E2E 검증 (2026-10-13): 한글 데이터로 실제 구동
패치본 TLDAT/FILEHEADER를 게임 R01에 넣고 `logger8.dll`(아래 5종 패치 전부)로 실행:

패치 5종:
1. 길이규칙 26곳 → 한글 2바이트
2. 변환기 5곳(0x57A81C, 0x57A990, 0x554E1E, 0x57ABA5, 0x538809) → `EUC-KR → 0x4000+idx`
   (idx=(b0-0xB0)*94+(b1-0xA1); 검사: lead∈[0xB0,0xC8] ∧ trail∈[0xA1,0xFE])
3. 글리프 0x578680 → `ax∈[0x4000,0x4000+N)` → `group=2+idx/192, slot=idx%192`
4. 폭 0x57ACD0 → 한글이면 48 반환
5. (미적용) 아틀라스 페이지 교체

결과:
- **크래시 없음.** 메인 텍스트 루프가 한글을 2바이트씩 전진(ptr +2).
- **한글 코드 인식 성공**: rings에 `B0A1, B1D7, B8A6, BAB4, B4EB, BCF6, BEB3, BCBC, B0E8, C0C7 …`
  가 들어왔고, CP949로 복원하면 **"마나", "중심"** 등 실제 한글 단어가 그대로 읽힘.
  → EUC-KR 2바이트 읽기 + 변환 + 글리프 슬롯 경로가 **end-to-end로 동작**.
- 현재 그 글리프는 게임 원본 페이지(2..14)를 가리키므로 화면에는 잘못된 글리프가 나옴
  (아틀라스 교체 전). 즉 **남은 것은 폰트 페이지 교체뿐**.

## A.7c 남은 디버깅 과제
- 로그에서 올바른 한글 코드와 함께 **변위(desync)된 코드**(예: 0x20B3, 0xC220, 0xD6BE)가
  섞여 들어옴(약 절반). 메인 루프는 정상(+2 전진)이므로, **아직 패치하지 못한 측정 경로**가
  원인으로 추정:
  - 길이규칙 예외 1곳 `0x4F961E`(즉시값 로드 없음, `cmp cx,di` 형태) 미패치.
  - `lea +0x7EFF` 패턴이 아닌 다른 길이 계산 경로 존재 가능.
- 다음: 변환기 호출부에 스텁 id를 로깅해 어느 경로가 변위 코드를 만드는지 특정.

## A.8 (2026-10-13 후반) 폰트 파이프라인 규명 — 핵심 돌파
컬러코딩/확대/로그 실험으로 확정:

1. **엔진 글리프 아틀라스 = `PAL_FONTB0`** (결정적 증거: A/B/C/DATA/PAL을 각각 다른 색으로 칠했을 때
   대사창 텍스트가 **빨강 = PAL_FONTB0**).  → FONTTYPE*_PIC 페이지는 이 텍스트에 안 쓰임.
2. **우리 파이프라인은 동작한다**: `PAL_FONTB0`을 **768×1728** 그대로 두고 그 안에 우리 kf13 3페이지
   (576자)를 세로 적층 + `logger11`(원래 행 공식, GPAGEOFF=0)로 실행 → **대사창에 정상 한글 글리프 출력**
   (예: "게 …경 …잣 니까낫"). ASCII도 정상 (저작권 표기 `©KOSUKE FUJISHIMA ©2004 BANDAI NAMCO…`).
3. **엔진 UV 정규화는 (768, 1728) 고정**: `PAL_FONTB0`을 4096² 또는 768×7488로 바꾸면
   대사창이 **빈 화면/가로로 찌그러진 조각**으로 깨짐. → 아틀라스는 **768×1728 (16열×36행, 48px 셀)** 이어야 함.
   (= 용량 576글리프)
4. 글리프 스텁/로그로 좌표 검증 완료 (`B0A1→(0,0)`, `C8FE→(45,26)`, ASCII공백→(46,26) 등 정확).
5. 타이틀/메뉴의 한글("불러오기/새 게임/커스텀/게임종료")은 **사전 렌더 이미지**(사용자 확인) → 폰트 검증 대상 아님.

### 남은 문제
- 576글리프 용량으로는 한글 2350자를 못 담음(48px 셀 기준).
- 확장 후보:
  - (a) 엔진이 아틀라스를 768×1728로 고정하는 지점(폰트 텍스처 생성/UV 상수) 찾아 패치.
  - (b) 768×1728 안에서 **셀 크기 축소**(예: 23px → 33×75=2475칸) + 우리 스텁이 px를 직접 출력.
      단, 쿼드의 UV 폭(span)이 고정 48이면 인접 셀을 물고 옴 → span 출처 규명 필요.
  - (c) 상수 `0x882a30 = 48.0` 패치 — 참조 45곳(공용)이라 위험.

# B. 다음 세션 시작점 (2026-10-13 마감 시점 상태)

## 현재 성공한 구성 (재현 가능)
- 코드 패치 DLL: `work/logger11.c` (= logger8에서 GPAGEOFF=0) — 빌드: `gcc -shared -O2 -s -o korfnt_logger11.dll logger11.c -lkernel32` (mingw32)
  - 내용: 길이규칙 26곳(한글 2바이트) + 변환기 5곳(`EUC-KR → 0x4000+idx`) + 글리프 스텁(그룹=idx/192, jmp 0x578737) + 폭(한글=48)
- 데이터: `work/tppal3/` = 패치 TLDAT 기반 + `PAL_FONTB0`을 **768×1728**에 kf13 3페이지 세로 적층
- 이 조합으로 **대사창에 정상 한글 렌더 성공** (검증됨)
- 설치/실행: `install_build.py <datadir> <dllname>` (설치만), `run_atlas_test4.py <sec> <datadir> <shotsdir>` (실행+스샷+복구)
- 테스트 후 **반드시** `backup/TLFILE.TLDAT.orig`, `backup/FILEHEADER.TOFHDB.orig`로 복구

## 바로 다음 할 일 (우선순위) — 2026-10-13 후반에 1·2 모두 해결(→ 부록 A.9)
1. ~~UV 폭(span) 출처 규명~~ → **규명 완료**: [edi+8]/[edi+0xc]는 span이 아니고 배치 상태.
   실제 span = V는 공용상수 `0x882a30=48.0`, U는 `width(code)`. (자세히 A.9)
2. ~~768×1728 고정 지점 패치~~ → **해결**: 고정 지점은 DDS가 아니라 **TOTEXB_D 디스크립터(+0x14)**.
   디스크립터 height만 패치 → 768×8640 임의 확장 성공, 나레이션·대사 한글 정상(부록 A.9).
3. 폭 함수 실제 반환값/전각 정렬 재확인(대사창 가로 찌그러짐이 span 문제였는지) — 남음(경미).

## 마감 시 게임 폴더 상태 (복구 완료)
- TOS.exe `01CAD338…3A7104`, korfnt.dll `93679A06…8576E7`, R01 TLDAT `2451FFA6…E588283`, TOFHDB `D118A4C0…0AF3BA34`
- 잔여물 없음 (krcodes.bin / korfnt.dll.real 없음), TOS 프로세스 없음

---

# 부록 A.9 — (2026-10-13 후반2) 아틀라스 확장 + ASCII/desync 해결 ★핵심 돌파

## A.9.1 엔진의 "768×1728 고정" 정체 = TOTEXB_D 디스크립터 (DDS 아님)
- 폰트 텍스처는 `TOTEXP_P`(DDS 본체) + `TOTEXB_D`(디스크립터 52~58B) 쌍. 디스크립터 레이아웃(확정):
  `"DPDF" | size=0x18 | 1 | 0xC8 | u16@0x10(=768 상수) | u16@0x12=width | u16@0x14=height | u16@0x16 | 0 | 4 | name`
  - 예: FONTTYPE 페이지 = (768,576), PAL_FONTB0 = (768,**1728**), SYSTEM_PIC001 = (128,256) — DDS 헤더와 정확히 일치.
- **엔진은 UV 정규화를 디스크립터 치수로 한다.** A.8에서 4096²·768×7488이 깨진 이유는
  디스크립터는 768×1728 그대로였기 때문(uv.py로 `same=True` 확인).
- 검증: PAL_FONTB0 TOTEXB_D(idx 83361)의 `+0x14` u16만 7488/8640으로 패치 + DDS를 그 크기로 →
  **대사창·나레이션 한글이 정상 렌더**. 즉 임의 높이 확장 가능.
- 산출물: `build_pal13b.py`(768×7488+desc), `build_pal15.py`(768×8640+desc), `run_pal13b.py`(실행/스샷/복구)

## A.9.2 최종 아틀라스 = 768×8640 = [원본 page0·1(ASCII/기호)] + [kf13 13페이지(한글)]
- group 0/1 (rows 0..23, 원본 유지) = ASCII·기호·가나 → **ASCII 경로가 원래대로 동작**.
- group 2..14 (rows 24..179) = 우리 한글. 글리프 스텁 `GPAGEOFF=2` (logger12/14).
- 용량 = 15페이지 × 192 = **2880칸 ≥ 2445자**(한글 2350 + ASCII 95). 768×7488만으로도 2496칸 가능.
- 근거: 원본 PAL_FONTB0 상단 2페이지가 ASCII(1..9,A..Z,a..z,©,™,기호)임을 이미지로 확인.

## A.9.3 ★길이규칙 스텁의 ecx 미보존 버그 = A.7c "desync"의 진짜 원인
- 증상: 나레이션/일부 경로에서 공백·마침표가 엉뚱한 글리프(`긷` 등)로, 일부 음절 치환.
- 계측(logger13: 글리프 호출을 (code, retaddr)로 링 기록) 결과:
  - 모든 글리프 호출이 `0x57A880` 루프(복귀 0x57A9EB)에서 옴.
  - 공백이 `0x831F`(=변환기 "c>0xFF" 결과)로 변환됨 → 스텁이 1바이트 문자를 2바이트로 오인.
- 원인: `stub_len`이 `KORTEST`로 **eax만 push/pop하고 ecx를 보존하지 않음**.
  → 1바이트 경로의 `mov esi,ecx`(0x57A928)에서 ecx(=b0)가 오염 → 변환기가 쓰레기 코드(0x831F) 수신.
- 수정: `stub_len`에 `push ecx/pop ecx` 추가(logger14). 검증:
  나레이션 `그 옛날 / 세계의 중심에는 / 마나를 낳는 대수가 있었다.`, `그 일에 한탄한 여신은 / 하늘로 사라졌다.` **완벽 렌더** (shots14).
- A.7c의 `0x20B3·0xC220·0xD6BE` 같은 변위 코드도 동일 원인으로 설명됨.

## A.9.4 UV span 규명 (B의 1번 과제 답)
- 글리프 함수(0x578680)는 ctx(esi)에 `[esi]=col*48.0`, `[esi+4]=row*48.0`, `[esi+8]=0`, `[esi+0xc]=[0xb18f9c(=0x0E000000)]` 기록.
  → **`[edi+8]/[edi+0xc]`는 UV span이 아니라 배치 상태(0/상수)**. span 가정은 오답이었음.
- 정점 생성(0x57ADB0 → 0x594500, 36B 정점 = x,y,z,u,v,rgba):
  - UV 사각형 = (u0,v0)-(u1,v1). v0=`[edi+4]`, v1=`v0+48.0`(`fadd qword [0x882a30]`, 0x57AA54) → **V span은 공용상수 48 하드코딩**.
  - U span = `width(code)`(0x57ACD0 반환, `[ebp-0x3c]`).
- 셀 축소(23px)하려면 `0x882a30`(48.0, 참조 45곳) 또는 각 호출부의 `fadd [0x882a30]`를 23으로 바꿔야 함 → 위험.
  **디스크립터 확장(A.9.1)으로 대체하여 불필요해짐.**

## A.9.5 이번 세션 산출물
- `work/logger12.c`(+`korfnt_logger12.dll`): logger11 + GPAGEOFF=2
- `work/logger13.c`(+dll): 계측용(글리프 (code,ret) 링) — desync 진단
- `work/logger14.c`(+`korfnt_logger14.dll`): **logger12 + stub_len ecx 보존 = 현재 최종본**
- `work/build_pal15.py` → `work/tppal15/` (768×8640, desc 8640)
- 검증 스샷: `work/shots14/t024,t028,t044` (나레이션 정상), `work/shots13/t024`(대사창)
- 빌드: `gcc -shared -O2 -s -o korfnt_logger14.dll logger14.c -lkernel32` (C:\msys64\mingw32\bin PATH 필요)
- 실행: `py -3.12 install_build.py tppal15 korfnt_logger14.dll` 후 `run_pal13b.py tppal15 100 shots14 korfnt_logger14.dll` (자동 복구)

## A.9.6 남은 과제
1. EUC-KR 기호 확장: 나레이션은 해결됐으나, EUC-KR 2바이트 기호(0xA1xx~0xA3xx, 예 `？`=0xA3BF)는
   원본 변환기가 0x831F로 보내 잘못된 글리프 → 변환기에서 0xA1..0xAF lead를 우리 기호 슬롯으로 매핑 + 아틀라스에 기호 추가 필요.
2. ASCII 폭: 현재 ASCII는 원본 page0/1(원래 폭) 사용 → 정상. 만약 ASCII를 우리 글리프로 바꿀 경우 폭 스텁도 확장 필요.
3. 나머지 폰트 오브젝트(13개: D_D/NPC/…/캐릭터별)와 PAL_FONTB0의 관계 — 대사창/메뉴/전투에서 전수 확인.
4. 배포용 정적 exe 패치 + 데이터 패키징, 한글 마커 파일명.

---

# 부록 A.10 — (2026-10-13 후반3) EUC-KR 기호 확장 (구현·정적검증 완료)

## A.10.1 설계 (기호 블록 추가)
- 기호 lead 0xA1..0xAF 중 실제 사용: 스캔 결과 0xA1(4.6만), 0xA3(1.9만), 0xA2(0.7만), 0xA6/0xAA/0xAB/0xAE/0xAF 등.
  → 안전하게 **lead 0xA1..0xAF 전체(15행×94=1410)** 를 수용.
- 슬롯(위치 고정, gi == 전달 index):
  - Hangul  0..2349    : (b0-0xB0)*94+(b1-0xA1)
  - ASCII   2350..2444 : 2350+(c-0x20)        (아직 미사용, 여유)
  - Symbol  2445..3854 : 2445+(b0-0xA1)*94+(b1-0xA1)
- 총 3855칸 → 21페이지(kf17), 원본 2페이지와 합쳐 **768×13248**(=23×576), 디스크립터 height=13248.
- 기호/한글 판정 스텁 `OURSIDX`(logger15): lead 0xB0..C8→한글, 0xA1..AF→기호, trail 0xA1..FE 공통.

## A.10.2 검증 완료 (게임 미실행, 정적)
- 스텁 역어셈블(test_stubs.c → capstone): OURSIDX/len/conv/width의 분기(SYM/DONE/NOT=비우리경로) 전부 정상.
- 아틀라스 셀: gi=0=`가`, 기호 idx2663(0xA3BF)=`？` 확인.
- D3D9 caps 실측(capsprobe.c): **AMD Radeon RX 9070 XT, MaxTextureWidth/Height=16384** → 13248 OK.
- 산출물: `work/logger15.c`(+`korfnt_logger15.dll`), `work/gen_atlas17.py`→`kf17/`(21p), `work/build_pal17.py`→`tppal17/`
- 빌드: `gcc -shared -O2 -s -o korfnt_logger15.dll logger15.c -lkernel32` (PATH에 C:\msys64\mingw32\bin)

## A.10.3 설치/테스트 (형님 직접, 스샷 후 종료)
1. `py -3.12 install_build.py tppal17 korfnt_logger15.dll`
2. `TOS.exe` 실행 → `？` 포함 대사(설정 변경 확인 등) 스샷
3. 원복: `backup\TLFILE.TLDAT.orig`, `backup\FILEHEADER.TOFHDB.orig` 복사 + `korfnt\korfnt.dll.real` → `korfnt.dll`
- 주의: AI가 게임을 임의 실행하지 말 것(형님이 스샷 찍고 종료하는 방식). 확인은 스팀 스크린샷 폴더로:
  `C:\Program Files (x86)\Steam\userdata\44668259\760\remote\372360\screenshots\`

## A.10.4 정상 기준 샷
- `tppal15 + logger14` = 나레이션 완벽(스샷 11:11). 이 조합이 회귀 기준.
- 기호확장 후에도 그 나레이션이 동일해야 하고, 추가로 `？`가 정상이어야 함.



