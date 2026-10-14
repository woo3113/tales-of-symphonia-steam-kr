param([string]$Game)
. (Join-Path $PSScriptRoot 'kr_common.ps1')
$g = Find-GameDir $Game
if (Get-Process TOS -ErrorAction SilentlyContinue) { throw "게임을 끄고 실행하세요." }
$tl = Join-Path $g "$REL\TLFILE.TLDAT"; $ix = Join-Path $g "$REL\FILEHEADER.TOFHDB"
$bak = Join-Path $g 'korfnt_beta_backup'
$st = Join-Path $bak 'state.txt'
if (-not (Test-Path $st)) { throw "적용된 베타가 없어요." }
$kv = @{}; Get-Content $st | ForEach-Object { $a = $_ -split '=', 2; $kv[$a[0]] = $a[1] }
$fs = [IO.File]::Open($tl, 'Open', 'ReadWrite')
try {
    $fs.SetLength([int64]$kv['len'])
    if ($kv['typo'] -eq 'True') { $fs.Position = $TYPO_OFF + 1; $fs.WriteByte(0xC6) }
} finally { $fs.Close() }
Copy-Item (Join-Path $bak 'FILEHEADER.TOFHDB') $ix -Force
Copy-Item (Join-Path $bak 'korfnt.dll') (Join-Path $g 'korfnt\korfnt.dll') -Force
Remove-Item $bak -Recurse -Force
Write-Host "완료: 한글패치 1.0 상태로 되돌렸어요."
