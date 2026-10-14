# 공통 함수 (TOS 한글패치 AMD/인텔 지원판 베타)
$ErrorActionPreference = 'Stop'
$script:REL = 'P12E\Data\TOS_Server\Archive\Release\R01\WIN'
$script:HV_DESC = [uint32]3085532135   # PAL_FONTB0 TOTEXB_D (descriptor)
$script:HV_PAL  = [uint32]3085344091   # PAL_FONTB0 TOTEXP_P (DDS)
$script:LEN_ORIG    = [int64]1076997569   # Steam 원본 TLFILE.TLDAT
$script:LEN_KR10    = [int64]1110752596   # 한글패치 1.0 TLFILE.TLDAT
$script:TYPO_OFF    = [int64]0x13E493D5   # "로이드 아빙!" (한글패치 1.0 기준)
$script:NEW_H = 13248

function Find-GameDir([string]$hint) {
    $c = @()
    if ($hint) { $c += $hint }
    $c += (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))   # 베타 폴더를 게임 폴더 안에 둔 경우
    $c += 'C:\Program Files (x86)\Steam\steamapps\common\Tales of Symphonia'
    foreach ($d in 'C','D','E','F','G') { $c += "${d}:\SteamLibrary\steamapps\common\Tales of Symphonia" }
    foreach ($p in $c) { if ($p -and (Test-Path (Join-Path $p 'TOS.exe'))) { return (Resolve-Path $p).Path } }
    throw "게임 폴더를 찾지 못했어요. 이 베타 폴더를 게임 폴더(TOS.exe 있는 곳) 안에 넣고 다시 실행하세요."
}

function Get-Records([byte[]]$idx) {
    $base = 40 + 84385 * 8
    $n = [int](($idx.Length - $base) / 40)
    $map = @{}
    for ($i = 0; $i -lt $n; $i++) {
        $o = $base + 40 * $i
        $hv = [BitConverter]::ToUInt32($idx, $o + 24)
        if ($hv -eq $script:HV_DESC -or $hv -eq $script:HV_PAL) { $map[$hv] = $o }
    }
    return $map
}

function Read-Entry([System.IO.FileStream]$fs, [byte[]]$idx, [int]$recOff) {
    $size = [BitConverter]::ToInt64($idx, $recOff)
    $csz  = [BitConverter]::ToInt64($idx, $recOff + 8)
    $off  = [BitConverter]::ToInt64($idx, $recOff + 16)
    $buf = New-Object byte[] $csz
    $fs.Position = $off; [void]$fs.Read($buf, 0, $csz)
    if ($csz -ne $size -and $buf[0] -eq 0x54 -and $buf[1] -eq 0x4C -and $buf[2] -eq 0x5A -and $buf[3] -eq 0x43) {
        $ms = [System.IO.MemoryStream]::new($buf, 24, [int]($csz - 24))
        $ds = [System.IO.Compression.DeflateStream]::new($ms, [System.IO.Compression.CompressionMode]::Decompress)
        $out = New-Object byte[] $size
        $got = 0
        while ($got -lt $size) { $r = $ds.Read($out, $got, $size - $got); if ($r -le 0) { break }; $got += $r }
        $ds.Dispose()
        if ($got -ne $size) { throw "압축 해제 실패" }
        return ,$out
    }
    return ,$buf
}
