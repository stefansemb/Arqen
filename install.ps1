<#
.SYNOPSIS
    Installs Arqen on this computer.

.DESCRIPTION
    Sets up everything Arqen needs, inside this folder:
      - a private Python environment (.venv) with Arqen's packages
      - the Chromium browser that Arqen's web tools drive (Playwright)
      - ffmpeg for the voice, if it is missing (through winget)
      - a Start menu shortcut, and a desktop one if you want

    Nothing is installed system-wide except Python and ffmpeg, and only if they
    are missing and you say yes. Run it again after a new release to update
    the packages.

.PARAMETER Yes
    Answer yes to every question.

.PARAMETER NoShortcuts
    Do not create any shortcuts.

.PARAMETER NoLaunch
    Do not offer to start Arqen at the end.
#>
param([switch]$Yes, [switch]$NoShortcuts, [switch]$NoLaunch)

# Native programs (pip, winget) report on stderr; exit codes decide instead.
$ErrorActionPreference = 'Continue'
$root = $PSScriptRoot
Set-Location $root

function Step($text) { Write-Host ''; Write-Host "==> $text" -ForegroundColor Green }
function Info($text) { Write-Host "    $text" }
function Warn($text) { Write-Host "    $text" -ForegroundColor Yellow }
function Fail($text) {
    Write-Host ''
    Write-Host "    $text" -ForegroundColor Red
    exit 1
}
function Confirm-Step($question) {
    if ($Yes) { return $true }
    $answer = Read-Host "    $question [Y/n]"
    return ($answer -eq '' -or $answer -match '^(y|yes|j|ja)$')
}

Write-Host 'Arqen installer' -ForegroundColor Green
Write-Host "Folder: $root"

# ---------------------------------------------------------------- Python
Step 'Python 3.10 to 3.13'
# The newest Python is not always supported by every package yet (PyQt6,
# faster-whisper), so a supported version is picked, newest tested first.
$supported = @('3.12', '3.13', '3.11', '3.10')

function Find-Python {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    foreach ($version in $supported) {
        if ($launcher) {
            $exe = & py "-$version" -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0 -and $exe) { return "$exe".Trim() }
        }
        $candidate = Join-Path $env:LOCALAPPDATA ('Programs\Python\Python' + $version.Replace('.', '') + '\python.exe')
        if (Test-Path $candidate) { return $candidate }
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    # The WindowsApps "python" only opens the Microsoft Store.
    if ($python -and $python.Source -notlike '*WindowsApps*') {
        $version = & python -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($supported -contains "$version".Trim()) {
            return ("" + (& python -c 'import sys; print(sys.executable)')).Trim()
        }
    }
    return $null
}

$python = Find-Python
if (-not $python) {
    Warn 'No supported Python was found.'
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Fail 'Install Python 3.12 from https://www.python.org/downloads/ (tick "Add python.exe to PATH"), then run this installer again.'
    }
    if (-not (Confirm-Step 'Install Python 3.12?')) {
        Fail 'Arqen needs Python 3.10 to 3.13. Install it, then run this installer again.'
    }
    winget install --exact --id Python.Python.3.12 --scope user
    $python = Find-Python
    if (-not $python) {
        Fail 'Python was installed, but this window cannot see it yet. Close it and run the installer again.'
    }
}
Info "Using $python"

# ---------------------------------------------------------------- Packages
Step 'Python environment (.venv)'
$venv = Join-Path $root '.venv'
$venvPython = Join-Path $venv 'Scripts\python.exe'
$venvPythonw = Join-Path $venv 'Scripts\pythonw.exe'
if (Test-Path $venvPython) {
    Info 'Already there; updating it.'
} else {
    & $python -m venv $venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) { Fail 'Could not create the Python environment.' }
    Info 'Created.'
}

Step 'Packages (a few minutes the first time)'
& $venvPython -m pip install --upgrade pip --disable-pip-version-check --quiet
& $venvPython -m pip install -r (Join-Path $root 'requirements.txt') --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { Fail 'Installing the packages failed; see the messages above.' }

Step 'Browser for the web tools (Chromium)'
& $venvPython -m playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Warn 'Chromium could not be installed. The browser tools need it; install it later with:'
    Warn '.venv\Scripts\python -m playwright install chromium'
}

# ---------------------------------------------------------------- ffmpeg
Step 'ffmpeg for the voice'
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Info 'Found.'
} elseif ((Get-Command winget -ErrorAction SilentlyContinue) -and (Confirm-Step 'Install ffmpeg?')) {
    winget install --exact --id Gyan.FFmpeg
    if ($LASTEXITCODE -eq 0) {
        Info 'Installed. If Arqen cannot find it, sign out of Windows and in again.'
    } else {
        Warn 'ffmpeg could not be installed. Arqen works without it, but cannot speak.'
    }
} else {
    Warn 'Without ffmpeg Arqen works, but cannot speak. Install it with: winget install Gyan.FFmpeg'
}

# ---------------------------------------------------------------- Shortcuts
function New-ArqenShortcut($path) {
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut($path)
    $link.TargetPath = $venvPythonw
    $link.Arguments = '-m arqen.ui'
    $link.WorkingDirectory = $root
    $link.IconLocation = (Join-Path $root 'assets\arqen.ico')
    $link.Description = 'Arqen, local AI assistant'
    $link.Save()
}

if (-not $NoShortcuts) {
    Step 'Shortcuts'
    New-ArqenShortcut (Join-Path ([Environment]::GetFolderPath('Programs')) 'Arqen.lnk')
    Info 'Start menu: Arqen'
    if (Confirm-Step 'Put a shortcut on the desktop too?') {
        New-ArqenShortcut (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Arqen.lnk')
        Info 'Desktop: Arqen'
    }
}

# ---------------------------------------------------------------- Done
Step 'Arqen is installed'
Info 'Start it from the Start menu, or with start.cmd in this folder.'
Info 'First time: open Settings (bottom left), pick a profile or a provider and model,'
Info 'paste your API key, press TEST CONNECTION and SAVE.'
Info 'Fully local: install Ollama (https://ollama.com) and pick the Private (Ollama) profile.'
Info 'Something wrong? Look in data\arqen.log.'

if (-not $NoLaunch -and (Confirm-Step 'Start Arqen now?')) {
    Start-Process -FilePath $venvPythonw -ArgumentList '-m', 'arqen.ui' -WorkingDirectory $root
}
