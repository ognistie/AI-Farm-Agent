param([string]$PythonExecutable = 'py')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot '.venv'
$venvPython = Join-Path $venvPath 'Scripts/python.exe'
$lockPath = Join-Path $repoRoot 'ai-farm-agent/requirements-windows-py311.lock.txt'
if (-not (Test-Path -LiteralPath $venvPython)) {
    if ($PythonExecutable -eq 'py') {
        & $PythonExecutable -3.11 -m venv $venvPath
    } else {
        & $PythonExecutable -m venv $venvPath
    }
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar ambiente virtual.' }
}
& $venvPython -c 'import sys; assert sys.version_info[:2] == (3,11), "Use Python 3.11 para o ambiente validado."'
if ($LASTEXITCODE -ne 0) { throw 'Versao Python diferente da validada.' }
& $venvPython -m pip install -r $lockPath
if ($LASTEXITCODE -ne 0) { throw 'Falha na instalacao das dependencias.' }
& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependencias inconsistentes.' }
& $venvPython (Join-Path $PSScriptRoot '..\ai-farm-agent\scripts\install_shortcuts.py')
if ($LASTEXITCODE -ne 0) { Write-Warning 'Atalhos nao criados; o app ainda abre por iniciar.cmd.' }
Write-Output 'Ambiente preparado. Configure .env e abra o AI Farm Agent pelo atalho na Area de Trabalho.'
