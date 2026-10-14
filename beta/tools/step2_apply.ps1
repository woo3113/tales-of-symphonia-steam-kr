param([string]$Game)
. (Join-Path $PSScriptRoot 'kr_common.ps1')
$root = Split-Path -Parent $PSScriptRoot
$g = Find-GameDir $Game
if (Get-Process TOS -ErrorAction SilentlyContinue) { throw "게임을 끄고 실행하세요." }
$tl = Join-Path $g "$REL\TLFILE.TLDAT"; $ix = Join-Path $g "$REL\FILEHEADER.TOFHDB"
$bak = Join-Path $g 'korfnt_beta_backup'
if (Test-Path (Join-Path $bak 'state.txt')) { throw "이미 적용돼 있어요. 다시 적용하려면 먼저 3_되돌리기를 실행하세요." }
$len = (Get-Item $tl).Length
if ($len -ne $LEN_KR10) { throw "한글패치 1.0 데이터가 아니에요(크기 $len). 한글패치 1.0을 먼저 설치하세요." }
if (-not (Test-Path (Join-Path $g 'd3d9.dll')) -or -not (Test-Path (Join-Path $g 'korfnt'))) { throw "한글패치 1.0(d3d9.dll, korfnt 폴더)이 없어요. 먼저 설치하세요." }
$topF = Join-Path $root 'data\pal_top.bin'
if (-not (Test-Path $topF)) { throw "data\pal_top.bin 이 없어요. 1단계(원본 글꼴 백업)를 먼저 하세요." }
$top = [IO.File]::ReadAllBytes($topF)
$kr  = [IO.File]::ReadAllBytes((Join-Path $root 'data\kr_pages.dxt5'))
$W = 768; $H = $NEW_H
if ($top.Length - 128 + $kr.Length -ne $W * $H) { throw "글꼴 데이터 크기가 맞지 않아요." }

# 새 DDS (DXT5, 768 x 13248, 밉맵 1)
$dds = New-Object byte[] ($top.Length + $kr.Length)
[Array]::Copy($top, 0, $dds, 0, $top.Length)
[Array]::Copy($kr, 0, $dds, $top.Length, $kr.Length)
[Array]::Copy([BitConverter]::GetBytes([int]0x000A1007), 0, $dds, 8, 4)
[Array]::Copy([BitConverter]::GetBytes([int]$H), 0, $dds, 12, 4)
[Array]::Copy([BitConverter]::GetBytes([int]$W), 0, $dds, 16, 4)
[Array]::Copy([BitConverter]::GetBytes([int](($W / 4) * ($H / 4) * 16)), 0, $dds, 20, 4)
[Array]::Copy([BitConverter]::GetBytes([int]1), 0, $dds, 28, 4)
$pal = New-Object byte[] ($dds.Length + 4)
[Array]::Copy([BitConverter]::GetBytes([int]$dds.Length), 0, $pal, 0, 4)
[Array]::Copy($dds, 0, $pal, 4, $dds.Length)

# 백업
New-Item -ItemType Directory -Force $bak | Out-Null
Copy-Item $ix (Join-Path $bak 'FILEHEADER.TOFHDB') -Force
Copy-Item (Join-Path $g 'korfnt\korfnt.dll') (Join-Path $bak 'korfnt.dll') -Force

$idx = [IO.File]::ReadAllBytes($ix)
$rec = Get-Records $idx
$fs = [IO.File]::Open($tl, 'Open', 'ReadWrite')
try {
    $desc = Read-Entry $fs $idx $rec[$HV_DESC]
    [Array]::Copy([BitConverter]::GetBytes([uint16]$H), 0, $desc, 20, 2)
    # 번역 오타 1곳: 로이드 아빙 -> 어빙
    $fs.Position = $TYPO_OFF; $t = New-Object byte[] 4; [void]$fs.Read($t, 0, 4)
    $typo = ($t[0] -eq 0xBE -and $t[1] -eq 0xC6 -and $t[2] -eq 0xBA -and $t[3] -eq 0xF9)
    if ($typo) { $fs.Position = $TYPO_OFF + 1; $fs.WriteByte(0xEE) }
    # 끝에 덧붙이고 목차 갱신
    $end = $fs.Length
    $fs.Position = $end; $fs.Write($pal, 0, $pal.Length)
    $end2 = $fs.Position; $fs.Write($desc, 0, $desc.Length)
    foreach ($pair in @(@($HV_PAL, $end, $pal.Length), @($HV_DESC, $end2, $desc.Length))) {
        $o = $rec[$pair[0]]
        [Array]::Copy([BitConverter]::GetBytes([int64]$pair[2]), 0, $idx, $o, 8)
        [Array]::Copy([BitConverter]::GetBytes([int64]$pair[2]), 0, $idx, $o + 8, 8)
        [Array]::Copy([BitConverter]::GetBytes([int64]$pair[1]), 0, $idx, $o + 16, 8)
    }
} finally { $fs.Close() }
[IO.File]::WriteAllBytes($ix, $idx)
Copy-Item (Join-Path $root 'korfnt\korfnt.dll') (Join-Path $g 'korfnt\korfnt.dll') -Force
"len=$len`ntypo=$typo" | Set-Content -Encoding ASCII (Join-Path $bak 'state.txt')
Write-Host "완료: 한글패치 베타를 적용했어요. 게임을 켜서 확인하세요."
