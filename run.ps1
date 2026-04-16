# run.ps1 — BuE-Hentai Downloader interactive launcher (Windows)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location $PSScriptRoot

# ── UI primitives ─────────────────────────────────────────────────
function Header {
    Write-Host
    Write-Host "  ╭──────────────────────────────────────╮" -ForegroundColor White
    Write-Host "  │        BuE-Hentai Downloader         │" -ForegroundColor White
    Write-Host "  ╰──────────────────────────────────────╯" -ForegroundColor White
    Write-Host
}

function Section([string]$Title) {
    Write-Host
    Write-Host "  ◆ $Title" -ForegroundColor Cyan
    Write-Host
}

function Ok([string]$Msg)   { Write-Host "    ✓ $Msg" -ForegroundColor Green }
function Info([string]$Msg) { Write-Host "    · $Msg" -ForegroundColor DarkGray }
function Warn([string]$Msg) { Write-Host "    ! $Msg" -ForegroundColor Yellow }
function Fail([string]$Msg) { Write-Host "    ✗ $Msg" -ForegroundColor Red; exit 1 }

function Ask([string]$Prompt, [string]$Default = "") {
    Write-Host -NoNewline "    "
    Write-Host -NoNewline "› " -ForegroundColor Yellow
    Write-Host -NoNewline $Prompt
    if ($Default -ne "") { Write-Host -NoNewline " [$Default]" -ForegroundColor DarkGray }
    Write-Host -NoNewline " "
    $val = [Console]::ReadLine()
    if ($null -eq $val -or $val -eq "") {
        if ($Default -ne "") { return $Default }
        return ""
    }
    return $val
}

# ─────────────────────────────────────────────────────────────────
Header

# ── Environment ───────────────────────────────────────────────────
Section "Environment"

$python = ".\.venv\Scripts\python.exe"
$pip    = ".\.venv\Scripts\pip.exe"

if (-not (Test-Path $python)) {
    Info "Creating virtual environment..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Fail "Failed to create venv. Is Python installed?" }
}

Info "Checking dependencies..."
& $pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) { Fail "Failed to install dependencies." }
Ok "Environment ready"

# ── Login ─────────────────────────────────────────────────────────
Section "Login"

$cookieStr = ""
$hires     = $false

function Ask-Hires {
    $v = Ask "Download original resolution? (requires GP)" "n"
    if ($v.ToLower() -eq "y") { $script:hires = $true }
}

function Do-FreshLogin {
    Write-Host
    Info "How to get your cookie string:"
    Write-Host "      1. Open e-hentai.org and log in"           -ForegroundColor DarkGray
    Write-Host "      2. Press F12 and go to the Console tab"    -ForegroundColor DarkGray
    Write-Host "      3. Type: document.cookie  and press Enter" -ForegroundColor DarkGray
    Write-Host "      4. Copy the full output"                   -ForegroundColor DarkGray
    Write-Host
    $c = Ask "Paste cookie string:"
    $script:cookieStr = $c
    Set-Content -Path "cookies.txt" -Value $c
    Ok "Login saved to cookies.txt"
    Ask-Hires
}

if (Test-Path "cookies.txt") {
    Info "Saved login detected"
    Write-Host
    Write-Host "      1  Use saved login"         -ForegroundColor DarkGray
    Write-Host "      2  Log in again"            -ForegroundColor DarkGray
    Write-Host "      3  Continue without login"  -ForegroundColor DarkGray
    Write-Host
    $loginChoice = Ask "Choice" "1"
} else {
    Write-Host "      1  Log in"                 -ForegroundColor DarkGray
    Write-Host "      2  Continue without login" -ForegroundColor DarkGray
    Write-Host
    $raw = Ask "Choice" "2"
    $loginChoice = if ($raw -eq "1") { "2" } else { "3" }
}

switch ($loginChoice) {
    "1" {
        $script:cookieStr = (Get-Content "cookies.txt" -Raw).Trim()
        Ok "Using saved login"
        Ask-Hires
    }
    "2" { Do-FreshLogin }
    "3" { Info "Continuing without login" }
    default { Warn "Invalid choice — continuing without login" }
}

# ── Download loop ─────────────────────────────────────────────────
while ($true) {
    Section "Download"

    Write-Host "      1  Single gallery URL"             -ForegroundColor DarkGray
    Write-Host "      2  Batch file  (one URL per line)" -ForegroundColor DarkGray
    Write-Host
    $dlMode = Ask "Mode" "1"

    $galleryUrl = ""
    $batchFile  = ""

    if ($dlMode -eq "2") {
        Info "One gallery URL per line. Lines starting with # are ignored."
        Write-Host
        $batchFile = Ask "Path to file:"
    } else {
        $galleryUrl = Ask "Gallery URL:"
        if ($galleryUrl -eq "") {
            Warn "No URL entered."
            continue
        }
    }

    # Build argument list — no Invoke-Expression
    $dlArgs = @()
    if ($galleryUrl -ne "") { $dlArgs += $galleryUrl }
    if ($batchFile  -ne "") { $dlArgs += "--batch"; $dlArgs += $batchFile }
    if ($cookieStr  -ne "") { $dlArgs += "--cookies"; $dlArgs += $cookieStr }
    if ($hires)             { $dlArgs += "--hires" }

    Write-Host
    Info "Starting download..."
    Write-Host

    & $python downloader.py @dlArgs

    Write-Host
    $again = Ask "Download another gallery?" "n"
    if ($again.ToLower() -ne "y") { break }
}

Section "Done"
Info "Goodbye."
Write-Host
Start-Sleep -Seconds 1
