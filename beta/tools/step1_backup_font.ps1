param([string]$Game)
. (Join-Path $PSScriptRoot 'kr_common.ps1')
$g = Find-GameDir $Game
$tl = Join-Path $g "$REL\TLFILE.TLDAT"; $ix = Join-Path $g "$REL\FILEHEADER.TOFHDB"
$len = (Get-Item $tl).Length
if ($len -ne $LEN_ORIG) {
    throw "원본 게임 데이터가 아니에요(크기 $len). 스팀에서 '게임 파일 무결성 확인'을 먼저 한 뒤 다시 실행하세요."
}
$idx = [IO.File]::ReadAllBytes($ix)
$rec = Get-Records $idx
$fs = [IO.File]::OpenRead($tl)
try { $pal = Read-Entry $fs $idx $rec[$HV_PAL] } finally { $fs.Close() }
$p = 0; if (-not ($pal[0] -eq 0x44 -and $pal[1] -eq 0x44)) { $p = 4 }   # 4바이트 길이 접두사
$w = [BitConverter]::ToInt32($pal, $p + 16); $h = [BitConverter]::ToInt32($pal, $p + 12)
if ($w -ne 768 -or $h -ne 1728) { throw "예상과 다른 글꼴 텍스처($w x $h)" }
$top = 768 * 1152                      # 원본 1~2페이지(영문/기호) = DXT5 768x1152
$out = New-Object byte[] (128 + $top)
[Array]::Copy($pal, $p, $out, 0, 128 + $top)
$dst = Join-Path (Split-Path -Parent $PSScriptRoot) 'data\pal_top.bin'
[IO.File]::WriteAllBytes($dst, $out)
Write-Host "완료: 원본 영문 글꼴 부분을 백업했어요 -> $dst"
