[CmdletBinding()]
param(
    [switch]$SkipDependencyInstall,
    [switch]$CleanOnly
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$FrontendDir = Join-Path $ProjectRoot "frontend"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SpecFile = Join-Path $ProjectRoot "build\PRAQ-web.spec"
$WorkDir = Join-Path $ProjectRoot "build\pyinstaller-web"
$OutputExe = Join-Path $ProjectRoot "dist\PRAQ.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Ambiente virtual nao encontrado: $VenvPython"
}

if (-not $SkipDependencyInstall) {
    & $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependencias da aplicacao." }
    & $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements-build.txt")
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependencias de build." }
    Push-Location $FrontendDir
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependencias do frontend." }
    }
    finally {
        Pop-Location
    }
}

& $VenvPython -m py_compile `
    (Join-Path $ProjectRoot "PRAQ_web.py") `
    (Join-Path $ProjectRoot "core.py") `
    (Join-Path $ProjectRoot "app_service.py")
if ($LASTEXITCODE -ne 0) { throw "Falha na validacao de sintaxe Python." }

if (Test-Path $OutputExe) {
    Remove-Item -LiteralPath $OutputExe -Force
}
if (Test-Path $WorkDir) {
    Remove-Item -LiteralPath $WorkDir -Recurse -Force
}

if ($CleanOnly) {
    exit 0
}

Push-Location $FrontendDir
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Falha ao compilar o frontend." }
}
finally {
    Pop-Location
}

& $VenvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath (Join-Path $ProjectRoot "dist") `
    --workpath $WorkDir `
    $SpecFile

if ($LASTEXITCODE -ne 0 -or -not (Test-Path $OutputExe)) {
    throw "A build web nao gerou o executavel esperado: $OutputExe"
}

$OutputExe
