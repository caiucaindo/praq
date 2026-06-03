[CmdletBinding()]
param(
    [switch]$SkipDependencyInstall,
    [switch]$CleanOnly
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Done {
    param([string]$Message)
    Write-Host "OK  $Message" -ForegroundColor Green
}

function Remove-PathBestEffort {
    param([string]$Path)

    if (Test-Path $Path) {
        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
        }
        catch {
            Write-Warning "Nao foi possivel remover ${Path}: $($_.Exception.Message)"
        }
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$LegacyDistDir = Join-Path $ProjectRoot "dist\PRAQ"
$PyInstallerWorkDir = Join-Path $ProjectRoot "build\pyinstaller"
$SpecFile = Join-Path $ProjectRoot "build\PRAQ.spec"
$OutputExe = Join-Path $ProjectRoot "dist\PRAQ.exe"

Set-Location $ProjectRoot

Write-Host "PRAQ build 0.1.0" -ForegroundColor Magenta
Write-Host "Projeto: $ProjectRoot"

if (-not (Test-Path $VenvPython)) {
    Write-Step "Criando ambiente virtual .venv"
    py -3 -m venv .venv
    Write-Done "Ambiente virtual criado"
}

if (-not $SkipDependencyInstall) {
    Write-Step "Atualizando pip"
    & $VenvPython -m pip install --upgrade pip
    Write-Done "pip atualizado"

    Write-Step "Instalando dependencias da aplicacao"
    & $VenvPython -m pip install -r requirements.txt
    Write-Done "Dependencias da aplicacao instaladas"

    Write-Step "Instalando dependencias de build"
    & $VenvPython -m pip install -r requirements-build.txt
    Write-Done "Dependencias de build instaladas"
}

Write-Step "Validando sintaxe Python"
& $VenvPython -m py_compile PRAQ.py ui.py backend.py
Write-Done "Sintaxe validada"

Write-Step "Limpando saidas anteriores"
Remove-PathBestEffort $OutputExe
Remove-PathBestEffort $LegacyDistDir
Remove-PathBestEffort $PyInstallerWorkDir
Write-Done "Pastas de build limpas"

if ($CleanOnly) {
    Write-Done "Limpeza concluida"
    exit 0
}

Write-Step "Gerando executavel com PyInstaller"
& $VenvPython -m PyInstaller --noconfirm --clean --distpath dist --workpath build\pyinstaller $SpecFile
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller falhou com codigo de saida $LASTEXITCODE"
}
Write-Done "PyInstaller finalizado"

if (-not (Test-Path $OutputExe)) {
    throw "Build finalizada, mas o executavel esperado nao foi encontrado: $OutputExe"
}

Write-Host ""
Write-Host "Build concluida com sucesso:" -ForegroundColor Green
Write-Host $OutputExe -ForegroundColor White
