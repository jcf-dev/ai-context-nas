param([string]$Python = 'python', [int]$Uid = 10001, [int]$Gid = 10001)
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    & $Python -m scripts.manage init --uid $Uid --gid $Gid
    if ($LASTEXITCODE -ne 0) { throw 'Initialization failed.' }
    Write-Host 'Before copying to your NAS, set DATA_ROOT=./runtime and set PUID/PGID to the NAS folder owner in .env.'
} finally { Pop-Location }
