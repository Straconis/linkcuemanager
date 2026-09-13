param(
    [switch]$SkipTests,
    [switch]$NoClean
)

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Projects\LinkCue Suite\LinkCue Manager"
$AppName     = "LinkCue Manager"
$ExeName     = "LinkCueManager"
$IconName    = "linkcue_manager.ico"
$InstallerId = "manager"
$AppId       = "6A9D99EB-634F-4AAF-84F4-54D50921A94B"
$Publisher   = "LinkCue"

$VersionFile = Join-Path $ProjectRoot "version.py"
$IconPath    = Join-Path $ProjectRoot "assets\$IconName"
$BuildDir    = Join-Path $ProjectRoot "build"
$DistDir     = Join-Path $ProjectRoot "dist"
$InstallerDir = Join-Path $ProjectRoot "installer"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " $AppName RELEASE BUILD" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

#
# VERSION
#

if (-not (Test-Path -LiteralPath $VersionFile)) {
    throw "Missing version.py: $VersionFile"
}

$VersionText = Get-Content -LiteralPath $VersionFile -Raw

if ($VersionText -notmatch 'APP_VERSION\s*=\s*["'']([^"'']+)["'']') {
    throw "Could not read APP_VERSION from $VersionFile"
}

$Version = $Matches[1]

Write-Host "[+] Version: $Version" -ForegroundColor Green

#
# ICON
#

if (-not (Test-Path -LiteralPath $IconPath)) {
    throw "Missing application icon: $IconPath"
}

Write-Host "[+] Icon: $IconPath"

#
# PYTHON
#

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (Test-Path -LiteralPath $VenvPython) {
    $Python = $VenvPython
}
else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue

    if (-not $PythonCommand) {
        throw "Python was not found."
    }

    $Python = $PythonCommand.Source
}

Write-Host "[+] Python: $Python"

#
# FIND APPLICATION ENTRY POINT
#

$PreferredEntryPoints = @(
    "main.py",
    "run.py",
    "player.py",
    "manager.py",
    "app.py"
)

$EntryPoint = $null

foreach ($Candidate in $PreferredEntryPoints) {
    $CandidatePath = Join-Path $ProjectRoot $Candidate

    if (Test-Path -LiteralPath $CandidatePath) {
        $EntryPoint = $CandidatePath
        break
    }
}

if (-not $EntryPoint) {

    $MainCandidates = Get-ChildItem `
        -LiteralPath $ProjectRoot `
        -Recurse `
        -File `
        -Filter "*.py" |
        Where-Object {
            $_.FullName -notmatch '\\\.venv\\' -and
            $_.FullName -notmatch '\\tests\\' -and
            $_.FullName -notmatch '\\build\\' -and
            $_.FullName -notmatch '\\dist\\' -and
            $_.FullName -notmatch '\\__pycache__\\'
        } |
        Where-Object {
            Select-String `
                -LiteralPath $_.FullName `
                -Pattern 'if\s+__name__\s*==\s*["'']__main__["'']' `
                -Quiet
        }

    if ($MainCandidates.Count -eq 1) {
        $EntryPoint = $MainCandidates[0].FullName
    }
    elseif ($MainCandidates.Count -gt 1) {

        Write-Host ""
        Write-Host "[!] Multiple possible launch files found:" -ForegroundColor Yellow

        $MainCandidates |
            ForEach-Object {
                Write-Host "    $($_.FullName)"
            }

        throw "Could not safely choose an application entry point."
    }
}

if (-not $EntryPoint) {
    throw "Could not locate the Python application entry point."
}

Write-Host "[+] Entry point: $EntryPoint" -ForegroundColor Green

#
# DEPENDENCIES
#

$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"

Write-Host ""
Write-Host "=== BUILD DEPENDENCIES ===" -ForegroundColor Cyan

& $Python -m pip install --disable-pip-version-check --upgrade pip

if ($LASTEXITCODE -ne 0) {
    throw "pip upgrade failed."
}

if (Test-Path -LiteralPath $RequirementsFile) {

    & $Python -m pip install `
        --disable-pip-version-check `
        -r $RequirementsFile

    if ($LASTEXITCODE -ne 0) {
        throw "Application dependency installation failed."
    }
}

& $Python -m pip install `
    --disable-pip-version-check `
    pyinstaller

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller installation failed."
}

#
# TESTS
#

if (-not $SkipTests) {

    $TestsDir = Join-Path $ProjectRoot "tests"

    if (Test-Path -LiteralPath $TestsDir) {

        Write-Host ""
        Write-Host "=== TESTS ===" -ForegroundColor Cyan

        $RequirementsDev = Join-Path $ProjectRoot "requirements-dev.txt"

        if (Test-Path -LiteralPath $RequirementsDev) {
            & $Python -m pip install `
                --disable-pip-version-check `
                -r $RequirementsDev

            if ($LASTEXITCODE -ne 0) {
                throw "Development dependency installation failed."
            }
        }

                Write-Host "[+] Running project test suite..." -ForegroundColor Yellow

        Push-Location $ProjectRoot

        try {
            & $Python -m pytest tests -ra
        }
        finally {
            Pop-Location
        }

        if ($LASTEXITCODE -ne 0) {
            throw "Tests failed. Release build aborted."
        }

        Write-Host "[OK] Tests passed." -ForegroundColor Green
    }
}

#
# CLEAN
#

if (-not $NoClean) {

    Write-Host ""
    Write-Host "=== CLEAN ===" -ForegroundColor Cyan

    foreach ($Path in @($BuildDir, $DistDir)) {

        if (Test-Path -LiteralPath $Path) {
            Remove-Item `
                -LiteralPath $Path `
                -Recurse `
                -Force
        }
    }
}

New-Item `
    -ItemType Directory `
    -Path $InstallerDir `
    -Force | Out-Null

#
# PYINSTALLER
#

Write-Host ""
Write-Host "=== PYINSTALLER ===" -ForegroundColor Cyan

$PyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--onedir",
    "--name", $ExeName,
    "--icon", $IconPath,
    "--distpath", $DistDir,
    "--workpath", $BuildDir,
    "--specpath", $BuildDir
)

#
# PySide6 applications
#

$PyInstallerArgs += @(
    "--collect-all", "PySide6"
)

#
# Player uses pywebview. This is harmless if the package exists,
# and only added when the current project actually has it installed.
#

$WebViewCheck = & $Python -c "import importlib.util; print('yes' if importlib.util.find_spec('webview') else 'no')"

$HasWebView = ($WebViewCheck.Trim() -eq "yes")

if ($HasWebView) {
    Write-Host "[+] pywebview detected; collecting webview resources."

    $PyInstallerArgs += @(
        "--collect-all", "webview"
    )
}

#
# Include assets directory.
#

$AssetsDir = Join-Path $ProjectRoot "assets"

if (Test-Path -LiteralPath $AssetsDir) {

    $PyInstallerArgs += @(
        "--add-data",
        "$AssetsDir;assets"
    )
}

$PyInstallerArgs += $EntryPoint

Push-Location $ProjectRoot

try {
    & $Python @PyInstallerArgs
}
finally {
    Pop-Location
}

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

$BuiltExe = Join-Path $DistDir "$ExeName\$ExeName.exe"

if (-not (Test-Path -LiteralPath $BuiltExe)) {
    throw "Expected executable was not created: $BuiltExe"
}

Write-Host "[OK] Application EXE created:" -ForegroundColor Green
Write-Host "     $BuiltExe"

#
# FIND / INSTALL INNO SETUP
#

Write-Host ""
Write-Host "=== INNO SETUP ===" -ForegroundColor Cyan

$InnoCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
)

$ISCC = $InnoCandidates |
    Where-Object {
        $_ -and (Test-Path -LiteralPath $_)
    } |
    Select-Object -First 1

if (-not $ISCC) {

    Write-Host "[+] Inno Setup not found." -ForegroundColor Yellow

    $Winget = Get-Command winget -ErrorAction SilentlyContinue

    if ($Winget) {

        Write-Host "[+] Installing Inno Setup with winget..." -ForegroundColor Yellow

        winget install `
            --id JRSoftware.InnoSetup `
            --exact `
            --accept-package-agreements `
            --accept-source-agreements

        $ISCC = $InnoCandidates |
            Where-Object {
                $_ -and (Test-Path -LiteralPath $_)
            } |
            Select-Object -First 1
    }
}

if (-not $ISCC) {
    throw @"
Inno Setup compiler ISCC.exe was not found.

Install Inno Setup 6, then run this build script again.
"@
}

Write-Host "[+] ISCC: $ISCC"

#
# RELEASE DIRECTORY
#

$ReleaseDir = Join-Path $ProjectRoot "release\v$Version"

New-Item `
    -ItemType Directory `
    -Path $ReleaseDir `
    -Force | Out-Null

#
# GENERATE INNO SETUP FILE
#

$IssPath = Join-Path $InstallerDir "${InstallerId}_installer.iss"

$DistSource = Join-Path $DistDir "$ExeName"

$IssContent = @"
#define MyAppName "$AppName"
#define MyAppVersion "$Version"
#define MyAppPublisher "$Publisher"
#define MyAppExeName "$ExeName.exe"

[Setup]
AppId={{$AppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\LinkCue\$AppName
DefaultGroupName=LinkCue\$AppName

DisableProgramGroupPage=yes
PrivilegesRequired=admin

OutputDir=$ReleaseDir
OutputBaseFilename=$AppName Setup $Version

SetupIconFile=$IconPath
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
Uninstallable=yes

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

VersionInfoVersion=$Version
VersionInfoCompany=$Publisher
VersionInfoDescription=$AppName Installer
VersionInfoProductName=$AppName
VersionInfoProductVersion=$Version

[Files]
Source: "$DistSource\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\$AppName"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall $AppName"; Filename: "{uninstallexe}"
Name: "{autodesktop}\$AppName"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch $AppName"; Flags: nowait postinstall skipifsilent
"@

Set-Content `
    -LiteralPath $IssPath `
    -Value $IssContent `
    -Encoding UTF8

Write-Host "[OK] Inno Setup definition created:" -ForegroundColor Green
Write-Host "     $IssPath"

#
# COMPILE INSTALLER
#

Write-Host ""
Write-Host "=== INSTALLER BUILD ===" -ForegroundColor Cyan

& $ISCC $IssPath

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compiler failed."
}

$InstallerExe = Join-Path $ReleaseDir "$AppName Setup $Version.exe"

if (-not (Test-Path -LiteralPath $InstallerExe)) {
    throw "Expected installer was not created: $InstallerExe"
}

#
# FINAL REPORT
#

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " RELEASE BUILD COMPLETE" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

Write-Host ""
Write-Host "Application EXE:" -ForegroundColor Cyan
Write-Host "  $BuiltExe"

Write-Host ""
Write-Host "Inno Setup file:" -ForegroundColor Cyan
Write-Host "  $IssPath"

Write-Host ""
Write-Host "Installer:" -ForegroundColor Cyan
Write-Host "  $InstallerExe"

Write-Host ""
Write-Host "Installer uninstall support:" -ForegroundColor Cyan
Write-Host "  [OK] Windows Installed Apps entry"
Write-Host "  [OK] Inno Setup uninstaller"
Write-Host "  [OK] Start Menu Uninstall shortcut"

Write-Host ""
Write-Host "[OK] $AppName v$Version ready." -ForegroundColor Green


