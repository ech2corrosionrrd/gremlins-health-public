<#
.SYNOPSIS
    Start / stop / inspect the Gremlins Health backend API and Telegram bot.

.DESCRIPTION
    Called by start.bat and stop.bat in the repository root. Can also be run
    directly:

        powershell -ExecutionPolicy Bypass -File scripts\service.ps1 -Action status

    Processes are tracked by PID files under .run\. When a PID file is missing
    or stale (the service was started by hand, say) the script falls back to
    scanning for python processes whose command line points at THIS project
    directory. That scoping matters: other projects on this machine run their
    own node/python dev servers, and a port- or name-based kill would take
    them down too.
#>
[CmdletBinding()]
param(
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'status',

    # Which services to act on.
    [ValidateSet('all', 'api', 'bot', 'web', 'tunnel')]
    [string]$Only = 'all',

    # start: also launch the Vite dev server for the Mini App.
    [switch]$WithWeb,

    # start: also bring up the Cloudflare tunnel that publishes the dev server
    # at https://your-tunnel.example.com (required for Telegram, which opens Mini
    # Apps over HTTPS only).
    [switch]$WithTunnel,

    # start: skip "alembic upgrade head".
    [switch]$SkipMigrations,

    # stop: terminate child processes too (uvicorn --reload spawns a worker).
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir '..')).Path
$BackendDir  = Join-Path $ProjectRoot 'backend'
$WebDir      = Join-Path $ProjectRoot 'apps\telegram-mini-app'
$RunDir      = Join-Path $ProjectRoot '.run'
$TunnelToken = Join-Path $RunDir 'tunnel.token'
$LogDir      = Join-Path $ProjectRoot 'logs'

foreach ($d in @($RunDir, $LogDir)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

# --------------------------------------------------------------------------
# Output helpers
# --------------------------------------------------------------------------
function Write-Step { param([string]$Text) Write-Host "  $Text" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Text) Write-Host "  [ OK ] $Text" -ForegroundColor Green }
function Write-Warn { param([string]$Text) Write-Host "  [WARN] $Text" -ForegroundColor Yellow }
function Write-Err  { param([string]$Text) Write-Host "  [FAIL] $Text" -ForegroundColor Red }
function Write-Head {
    param([string]$Text)
    Write-Host ''
    Write-Host "== $Text " -ForegroundColor White -NoNewline
    Write-Host ('=' * [Math]::Max(0, 60 - $Text.Length)) -ForegroundColor DarkGray
}

# --------------------------------------------------------------------------
# Service definitions
# --------------------------------------------------------------------------
function Get-PythonExe {
    $venv = Join-Path $BackendDir '.venv\Scripts\python.exe'
    if (Test-Path $venv) { return $venv }
    $sys = Get-Command python -ErrorAction SilentlyContinue
    if ($sys) { return $sys.Source }
    throw "Python not found. Install it, or create a venv: python -m venv backend\.venv"
}

function Get-NpmExe {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($npm) { return $npm.Source }
    return $null
}

$Services = [ordered]@{
    api = @{
        Name    = 'API'
        Desc    = 'FastAPI backend (uvicorn, port 8000)'
        Dir     = $BackendDir
        PidFile = Join-Path $RunDir 'api.pid'
        Log     = Join-Path $LogDir 'api.log'
        # Identifies an already-running instance not started by this script.
        Match   = 'uvicorn'
        # Health-проба після старту все одно виконується, ця ознака лише
        # прибирає зайве очікування.
        ReadyPattern = 'Application startup complete'
    }
    bot = @{
        Name    = 'BOT'
        Desc    = 'Telegram bot (aiogram long polling)'
        Dir     = $BackendDir
        PidFile = Join-Path $RunDir 'bot.pid'
        Log     = Join-Path $LogDir 'bot.log'
        Match   = 'app.bot.bot'
        # aiogram пише це, коли вже автентифікувався в Telegram і почав опитування.
        ReadyPattern = 'Run polling for bot|Start polling'
    }
    tunnel = @{
        Name    = 'TUN'
        Desc    = 'Cloudflare tunnel -> https://your-tunnel.example.com'
        Dir     = $ProjectRoot
        PidFile = Join-Path $RunDir 'tunnel.pid'
        Log     = Join-Path $LogDir 'tunnel.log'
        Match   = 'cloudflared'
        # Перше зареєстроване з'єднання означає, що тунель уже приймає трафік.
        ReadyPattern = 'Registered tunnel connection'
    }
    web = @{
        Name    = 'WEB'
        Desc    = 'Mini App dev server (vite, port 5173)'
        Dir     = $WebDir
        PidFile = Join-Path $RunDir 'web.pid'
        Log     = Join-Path $LogDir 'web.log'
        Match   = 'vite'
        ReadyPattern = 'ready in \d+\s*ms'
    }
}

# --------------------------------------------------------------------------
# Process discovery
#
# Everything here is scoped to $ProjectRoot. Never match on port or image
# name alone - this machine runs other projects' dev servers.
# --------------------------------------------------------------------------
function Test-BelongsToProject {
    # Untyped on purpose: Get-CimInstance yields CimInstance, not the
    # ManagementBaseObject that the old Get-WmiObject returned.
    param($Proc)

    if (-not $Proc -or -not $Proc.CommandLine) { return $false }

    # Windows does not expose a process's working directory, and
    # (Get-Process).Path is the executable (python.exe), not the cwd - so the
    # command line is the only reliable evidence. Services started by this
    # script always carry the project path there; see Start-One.
    return $Proc.CommandLine -like "*$ProjectRoot*"
}

function Get-ProjectProcesses {
    <#
        Finds candidate processes for a service.

        Two tiers, because a process started by hand ("python -m uvicorn
        app.main:app" from the backend directory) carries no path at all:

          path      - the command line names this project directory. Certain.
          signature - the command line matches a module path unique to this
                      application. Likely, and reported as such before
                      anything is terminated.
    #>
    param(
        [string]$Signature,
        # Suppress the signature tier. Used by the leftovers sweep, which runs
        # unprompted and must never report - let alone stop - a process it
        # cannot tie to this directory.
        [switch]$PathOnly
    )

    $all = Get-CimInstance Win32_Process -Filter "Name like 'python%' or Name like 'node%'" |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*$Signature*" }

    $byPath = @($all | Where-Object { Test-BelongsToProject $_ })
    if ($byPath.Count -gt 0 -or $PathOnly) {
        return @($byPath | ForEach-Object {
            [pscustomobject]@{ Proc = $_; Certainty = 'path' }
        })
    }

    return @($all | ForEach-Object {
        [pscustomobject]@{ Proc = $_; Certainty = 'signature' }
    })
}

function Get-ServiceProcess {
    param([hashtable]$Svc)

    # 1. PID file. It records the creation time as well as the id, so a
    #    recycled PID belonging to some unrelated process is never matched.
    if (Test-Path $Svc.PidFile) {
        $recorded = (Get-Content $Svc.PidFile -Raw).Trim()
        $parts = $recorded -split '\|'
        if ($parts[0] -match '^\d+$') {
            $p = Get-CimInstance Win32_Process -Filter "ProcessId = $($parts[0])" -ErrorAction SilentlyContinue
            if ($p) {
                $stampOk = $true
                if ($parts.Count -ge 2 -and $p.CreationDate) {
                    $stampOk = ($p.CreationDate.ToFileTimeUtc().ToString() -eq $parts[1])
                }
                if ($stampOk) {
                    return [pscustomobject]@{ Proc = $p; Certainty = 'pidfile' }
                }
            }
        }
        Remove-Item $Svc.PidFile -Force -ErrorAction SilentlyContinue
    }

    # 2. Scan, for instances started outside this script.
    return (Get-ProjectProcesses -Signature $Svc.Match | Select-Object -First 1)
}

function Save-PidFile {
    param([string]$Path, [int]$ProcessId)

    $p = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    $stamp = if ($p -and $p.CreationDate) { $p.CreationDate.ToFileTimeUtc().ToString() } else { '' }
    Set-Content -Path $Path -Value "$ProcessId|$stamp" -Encoding ascii
}

function Get-DescendantIds {
    param([int]$ParentId)

    $ids = @()
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ParentId" -ErrorAction SilentlyContinue
    foreach ($c in $children) {
        $ids += $c.ProcessId
        $ids += Get-DescendantIds -ParentId $c.ProcessId
    }
    return $ids
}

# --------------------------------------------------------------------------
# Environment checks
# --------------------------------------------------------------------------
function Read-LogTail {
    <#
        Читає хвіст лог-файлу, НЕ блокуючи його.

        Get-Content у циклі готовності відкривав файл так, що дочірній процес
        не міг у нього писати, отримував помилку вводу-виводу й помирав —
        тобто перевірка готовності вбивала сервіс, який перевіряла.
        FileShare ReadWrite|Delete лишає письменнику повний доступ.
    #>
    param([string[]]$Path, [int]$MaxBytes = 8192)

    $chunks = @()
    foreach ($file in $Path) {
        if (-not (Test-Path $file)) { continue }
        try {
            $fs = [System.IO.File]::Open(
                $file, [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::Read,
                [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete)
            try {
                if ($fs.Length -gt $MaxBytes) { [void]$fs.Seek(-$MaxBytes, [System.IO.SeekOrigin]::End) }
                $reader = New-Object System.IO.StreamReader($fs)
                $chunks += $reader.ReadToEnd()
            } finally { $fs.Dispose() }
        } catch { }
    }
    return ($chunks -join "`n")
}

function Read-DotEnv {
    $envFile = Join-Path $BackendDir '.env'
    $values = @{}
    if (-not (Test-Path $envFile)) { return $values }

    foreach ($line in Get-Content $envFile) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $idx = $trimmed.IndexOf('=')
        if ($idx -lt 1) { continue }
        $key = $trimmed.Substring(0, $idx).Trim()
        $val = $trimmed.Substring($idx + 1).Trim().Trim('"').Trim("'")
        $values[$key] = $val
    }
    return $values
}

function Get-SchemaState {
    <#
        Classifies the database before migrating:
          empty      - no tables at all; a plain upgrade will build it
          unstamped  - application tables exist but alembic_version does not
                       (a legacy create_all database)
          managed    - alembic_version present; normal upgrade path
          unknown    - could not inspect; let alembic report the real error
    #>
    param([string]$Python)

    $probe = @'
import asyncio, os, sys

# The probe lives in .run\, so sys.path[0] is not the backend directory.
# The working directory is, and that is where the "app" package lives.
sys.path.insert(0, os.getcwd())

from sqlalchemy import inspect, text
from app.core.database import engine

async def main():
    async with engine.connect() as conn:
        names = await conn.run_sync(lambda c: inspect(c).get_table_names())

        app_tables = [n for n in names if n != "alembic_version"]
        stamped = False
        if "alembic_version" in names:
            # The table can exist while holding no row - an aborted or
            # rolled-back migration leaves exactly that state, and it is not
            # the same as being under Alembic control.
            rows = (await conn.execute(text("SELECT version_num FROM alembic_version"))).fetchall()
            stamped = len(rows) > 0
    await engine.dispose()

    if stamped:
        print("managed")
    elif not app_tables:
        print("empty")
    else:
        print("unstamped")

asyncio.run(main())
'@
    $probeFile = Join-Path $RunDir 'schema_probe.py'
    Set-Content -Path $probeFile -Value $probe -Encoding utf8

    $out = Join-Path $RunDir 'schema_probe.out'
    try {
        $p = Start-Process -FilePath $Python -ArgumentList @($probeFile) `
                           -WorkingDirectory $BackendDir -NoNewWindow -Wait -PassThru `
                           -RedirectStandardOutput $out -RedirectStandardError "$out.err"
        if ($p.ExitCode -ne 0) {
            # Surface the reason rather than silently degrading to 'unknown'.
            $err = (Get-Content "$out.err" -Tail 3 -ErrorAction SilentlyContinue) -join ' '
            if ($err) { Write-Warn "schema probe failed: $err" }
            return 'unknown'
        }
        $result = (Get-Content $out -Raw).Trim()
        if ($result -in @('empty', 'managed', 'unstamped')) { return $result }
        return 'unknown'
    } catch {
        return 'unknown'
    }
}

function Test-Environment {
    $envFile = Join-Path $BackendDir '.env'
    if (-not (Test-Path $envFile)) {
        Write-Err "backend\.env is missing."
        Write-Host "         Create it:  copy backend\.env.example backend\.env" -ForegroundColor DarkGray
        return $false
    }

    $cfg = Read-DotEnv

    if (-not $cfg.ContainsKey('SECRET_KEY') -or -not $cfg['SECRET_KEY']) {
        Write-Err "SECRET_KEY is empty in backend\.env - the API will refuse to start."
        Write-Host '         Generate one:  python -c "import secrets; print(secrets.token_urlsafe(48))"' -ForegroundColor DarkGray
        return $false
    }

    return $true
}

# --------------------------------------------------------------------------
# start
# --------------------------------------------------------------------------
function Start-One {
    # NOTE: not named $Args - that is a PowerShell automatic variable and a
    # parameter of that name silently resolves to the caller's empty array.
    # SettleMs: how long to wait before declaring the launch successful.
    # The bot authenticates against Telegram before it settles, so a bad
    # token kills it a second or two in - longer than a token-less start.
    param([string]$Key, [string]$Exe, [string[]]$ArgList, [int]$SettleMs = 1000)

    $svc = $Services[$Key]
    $existing = Get-ServiceProcess -Svc $svc
    if ($existing) {
        Write-Warn "$($svc.Name) already running (PID $($existing.Proc.ProcessId)) - leaving it alone."
        Save-PidFile -Path $svc.PidFile -ProcessId $existing.Proc.ProcessId
        return $true
    }

    $launch = [Diagnostics.Stopwatch]::StartNew()

    # Обрізаємо лог, щоб кожен запуск читався з чистого аркуша. Якщо файл
    # зайнятий, значить попередній екземпляр ще живий і його не розпізнали —
    # кажемо про це прямо, а не падаємо з IOException із надр Set-Content.
    Set-Content -Path $svc.Log -Value "=== $($svc.Name) started $(Get-Date -Format s) ===" -Encoding utf8

    try {
        # stdin НЕ перенаправляємо. Спроба підсунути порожній файл (щоб
        # батько не тримав консоль) завершилась тим, що vite, uvicorn і
        # cloudflared побачили EOF на stdin і чисто вийшли з кодом 0 —
        # dev-сервери сприймають закритий stdin як команду завершитись.
        # Проблему з перехопленням виводу це все одно не розв'язувало.
        $proc = Start-Process -FilePath $Exe `
                              -ArgumentList $ArgList `
                              -WorkingDirectory $svc.Dir `
                              -WindowStyle Hidden `
                              -RedirectStandardOutput $svc.Log `
                              -RedirectStandardError "$($svc.Log).err" `
                              -PassThru
    } catch {
        Write-Err "$($svc.Name) failed to launch: $($_.Exception.Message)"
        return $false
    }

    Save-PidFile -Path $svc.PidFile -ProcessId $proc.Id

    # Раніше цикл виходив достроково ЛИШЕ якщо процес помер, тож здоровий
    # сервіс завжди висиджував увесь бюджет: 6 с бот, 3 с web, 8 с тунель —
    # близько 17 с чистого сну на `start.bat tunnel`.
    #
    # Тепер SettleMs — це стеля, а не тривалість. Щойно сервіс сам написав у
    # лог, що готовий, чекати нема чого.
    $deadline = (Get-Date).AddMilliseconds($SettleMs)
    $ready = $false
    while ((Get-Date) -lt $deadline -and -not $proc.HasExited) {
        if ($svc.ReadyPattern) {
            $tail = Read-LogTail -Path @($svc.Log, "$($svc.Log).err")
            if ($tail -match $svc.ReadyPattern) { $ready = $true; break }
        }
        Start-Sleep -Milliseconds 200
    }

    if ($proc.HasExited) {
        # Refresh, or ExitCode can come back empty on a process we did not wait on.
        try { $proc.Refresh() } catch { }
        $code = try { $proc.ExitCode } catch { $null }
        $codeText = if ($null -ne $code) { "code $code" } else { 'unknown exit code' }
        Write-Err "$($svc.Name) exited immediately ($codeText). Last lines:"
        (Read-LogTail -Path @("$($svc.Log).err", $svc.Log) -MaxBytes 2048) -split "`n" |
            Select-Object -Last 8 | ForEach-Object { Write-Host "         $_" -ForegroundColor DarkGray }
        Remove-Item $svc.PidFile -Force -ErrorAction SilentlyContinue
        return $false
    }

    $how = if ($ready) { 'ready' } else { 'started' }
    $secs = $launch.Elapsed.TotalSeconds
    Write-Ok ("{0} {1} in {2:N1} s (PID {3})" -f $svc.Name, $how, $secs, $proc.Id)
    return $true
}

function Wait-ApiHealthy {
    param([int]$TimeoutSeconds = 25)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' `
                                   -UseBasicParsing -TimeoutSec 3
            if ($r.StatusCode -eq 200) {
                $body = $r.Content | ConvertFrom-Json
                Write-Ok "API healthy - environment=$($body.environment), version=$($body.version)"
                return $true
            }
        } catch { Start-Sleep -Milliseconds 700 }
    }
    Write-Warn "API did not answer /health within ${TimeoutSeconds}s. Check logs\api.log"
    return $false
}

function Invoke-Start {
    $startedAt = [Diagnostics.Stopwatch]::StartNew()
    Write-Head 'Starting Gremlins Health'
    Write-Host "  root: $ProjectRoot" -ForegroundColor DarkGray

    if (-not (Test-Environment)) { return 1 }

    $python = Get-PythonExe
    Write-Host "  python: $python" -ForegroundColor DarkGray

    $cfg = Read-DotEnv
    $wantApi = $Only -in @('all', 'api')
    $wantBot = $Only -in @('all', 'bot')
    $wantWeb = ($Only -eq 'web') -or ($WithWeb -and $Only -eq 'all')
    # The tunnel publishes the Vite dev server, so it implies -WithWeb.
    $wantTunnel = ($Only -eq 'tunnel') -or ($WithTunnel -and $Only -eq 'all')
    if ($wantTunnel -and $Only -eq 'all') { $wantWeb = $true }

    if ($wantApi -and -not $SkipMigrations) {
        Write-Step 'Applying database migrations...'
        $migLog = Join-Path $LogDir 'migrate.log'

        # A database created by the old create_all path has the tables but no
        # alembic_version row, so "upgrade head" would try to CREATE TABLE on
        # tables that already exist. Stamp it instead - but only in
        # development, where the schema provably came from the same metadata.
        $state = Get-SchemaState -Python $python
        if ($state -eq 'unstamped') {
            if ($cfg['ENVIRONMENT'] -eq 'development') {
                Write-Warn 'Database has tables but no Alembic version (legacy create_all).'
                $stamp = Start-Process -FilePath $python `
                                       -ArgumentList @('-m', 'alembic', 'stamp', 'head') `
                                       -WorkingDirectory $BackendDir `
                                       -NoNewWindow -Wait -PassThru `
                                       -RedirectStandardOutput "$migLog.stamp" `
                                       -RedirectStandardError "$migLog.stamp.err"
                if ($stamp.ExitCode -ne 0) {
                    Write-Err 'alembic stamp head failed - see logs\migrate.log.stamp.err'
                    return 1
                }
                Write-Ok 'Stamped at head; future changes go through migrations.'
            } else {
                Write-Err 'Database has tables but no Alembic version, and ENVIRONMENT is not development.'
                Write-Host '         Verify the schema matches, then run: alembic stamp head' -ForegroundColor DarkGray
                return 1
            }
        }

        # Alembic logs to stderr. In Windows PowerShell, "2>&1" on a native
        # command wraps each stderr line in an ErrorRecord, which under
        # ErrorActionPreference='Stop' throws even on a successful exit 0.
        # Redirect to a file and judge the result by the exit code instead.
        $proc = Start-Process -FilePath $python `
                              -ArgumentList @('-m', 'alembic', 'upgrade', 'head') `
                              -WorkingDirectory $BackendDir `
                              -NoNewWindow -Wait -PassThru `
                              -RedirectStandardOutput $migLog `
                              -RedirectStandardError "$migLog.err"

        if ($proc.ExitCode -ne 0) {
            Write-Err 'alembic upgrade head failed:'
            Get-Content "$migLog.err", $migLog -Tail 12 -ErrorAction SilentlyContinue |
                ForEach-Object { Write-Host "         $_" -ForegroundColor DarkGray }
            return 1
        }
        Write-Ok 'Schema up to date.'
    }

    $failed = $false

    if ($wantApi) {
        Write-Step 'Starting API...'
        if (Start-One -Key 'api' -Exe $python `
                      -ArgList @('-m', 'uvicorn', 'app.main:app',
                                 '--host', '127.0.0.1', '--port', '8000',
                                 '--app-dir', $BackendDir)) {
            Wait-ApiHealthy | Out-Null
        } else { $failed = $true }
    }

    if ($wantBot) {
        Write-Step 'Starting Telegram bot...'
        if (-not $cfg.ContainsKey('TELEGRAM_BOT_TOKEN') -or -not $cfg['TELEGRAM_BOT_TOKEN']) {
            # bot.py logs a warning and returns, so starting it would just
            # produce a process that exits. Say why instead.
            Write-Warn 'TELEGRAM_BOT_TOKEN is empty in backend\.env - bot NOT started.'
            Write-Host '         Get a token from @BotFather, then put it in backend\.env.' -ForegroundColor DarkGray
            Write-Host '         See SECURITY.md: the previously committed token must be revoked.' -ForegroundColor DarkGray
        } else {
            if (-not (Start-One -Key 'bot' -Exe $python `
                                -ArgList @('-m', 'app.bot.bot') -SettleMs 6000)) { $failed = $true }
        }
    }

    if ($wantWeb) {
        Write-Step 'Starting Mini App dev server...'
        $npm = Get-NpmExe
        if (-not $npm) {
            Write-Warn 'npm not found on PATH - web dev server skipped.'
        } elseif (-not (Test-Path (Join-Path $WebDir 'node_modules'))) {
            Write-Warn 'node_modules missing - run "npm install" in apps\telegram-mini-app first.'
        } else {
            if (-not (Start-One -Key 'web' -Exe $npm -ArgList @('run', 'dev') -SettleMs 3000)) { $failed = $true }
        }
    }

    if ($wantTunnel) {
        Write-Step 'Starting Cloudflare tunnel...'
        if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
            Write-Warn 'cloudflared is not on PATH - tunnel skipped.'
        } elseif (-not (Test-Path $TunnelToken)) {
            Write-Warn "No tunnel token at $TunnelToken - tunnel skipped."
            Write-Host '         Cloudflare dashboard -> Zero Trust -> Networks -> Tunnels' -ForegroundColor DarkGray
            Write-Host '         -> gremlins-health -> copy the connector token into that file.' -ForegroundColor DarkGray
        } else {
            $tok = (Get-Content $TunnelToken -Raw).Trim()
            # --pidfile веде в каталог проєкту, і саме тому він тут потрібен:
            # без нього командний рядок cloudflared не містить жодної згадки
            # про цей проєкт, і резервний пошук у Stop-One зіставлявся б із
            # БУДЬ-ЯКИМ cloudflared на машині — зокрема з чужими тунелями.
            $cfPid = Join-Path $RunDir 'cloudflared.pid'
            if (Start-One -Key 'tunnel' -Exe 'cloudflared' `
                          -ArgList @('tunnel', '--no-autoupdate',
                                     '--pidfile', $cfPid,
                                     'run', '--token', $tok) `
                          -SettleMs 8000) {
                Write-Host '         Public URL: https://your-tunnel.example.com' -ForegroundColor DarkGray
            } else { $failed = $true }
        }
    }

    Write-Head 'Endpoints'
    Write-Host '  API      http://127.0.0.1:8000'
    Write-Host '  Docs     http://127.0.0.1:8000/docs      (development only)'
    Write-Host '  Health   http://127.0.0.1:8000/health'
    if ($wantWeb) { Write-Host '  Mini App http://127.0.0.1:5173' }
    if ($wantTunnel) { Write-Host '  Public   https://your-tunnel.example.com   (what Telegram opens)' }
    Write-Host ''
    Write-Host ("  Ready in {0:N1} s" -f $startedAt.Elapsed.TotalSeconds) -ForegroundColor DarkGray
    Write-Host '  Logs:  logs\   |   Stop with:  stop.bat' -ForegroundColor DarkGray
    Write-Host ''

    return $(if ($failed) { 1 } else { 0 })
}

# --------------------------------------------------------------------------
# stop
# --------------------------------------------------------------------------
function Stop-One {
    param([string]$Key)

    $svc = $Services[$Key]
    $found = Get-ServiceProcess -Svc $svc

    if (-not $found) {
        Write-Host "  [ -- ] $($svc.Name) not running." -ForegroundColor DarkGray
        Remove-Item $svc.PidFile -Force -ErrorAction SilentlyContinue
        return $true
    }

    $proc = $found.Proc

    # Matched only by module signature: the command line carries no path, so
    # we cannot prove it is ours. Say so instead of quietly killing it.
    if ($found.Certainty -eq 'signature') {
        Write-Warn "$($svc.Name): PID $($proc.ProcessId) matched by signature, not by path."
        Write-Host "         $($proc.CommandLine)" -ForegroundColor DarkGray
        Write-Host '         It was started outside this script. Stopping it anyway.' -ForegroundColor DarkGray
    }

    $targets = @($proc.ProcessId)
    if ($Force) {
        # uvicorn --reload and npm both spawn workers that outlive the parent.
        $targets += Get-DescendantIds -ParentId $proc.ProcessId
    }

    foreach ($id in ($targets | Select-Object -Unique)) {
        try {
            Stop-Process -Id $id -Force -ErrorAction Stop
        } catch {
            Write-Warn "$($svc.Name): could not stop PID ${id}: $($_.Exception.Message)"
        }
    }

    Start-Sleep -Milliseconds 400
    $still = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
    if ($still) {
        Write-Err "$($svc.Name) (PID $($proc.ProcessId)) is still running."
        return $false
    }

    Write-Ok "$($svc.Name) stopped (PID $($proc.ProcessId))."
    Remove-Item $svc.PidFile -Force -ErrorAction SilentlyContinue
    return $true
}

function Invoke-Stop {
    Write-Head 'Stopping Gremlins Health'
    Write-Host "  root: $ProjectRoot" -ForegroundColor DarkGray
    Write-Host '  (only processes belonging to this project are touched)' -ForegroundColor DarkGray
    Write-Host ''

    $keys = if ($Only -eq 'all') { @('tunnel', 'web', 'bot', 'api') } else { @($Only) }

    $allOk = $true
    foreach ($k in $keys) {
        if (-not (Stop-One -Key $k)) { $allOk = $false }
    }

    # Sweep up anything the PID files missed - still project-scoped.
    $leftovers = @()
    foreach ($k in $keys) {
        $leftovers += (Get-ProjectProcesses -Signature $Services[$k].Match -PathOnly |
                       ForEach-Object { $_.Proc })
    }
    $leftovers = $leftovers | Sort-Object ProcessId -Unique
    if ($leftovers) {
        Write-Host ''
        Write-Warn "Still running in this project (started outside the script?):"
        foreach ($p in $leftovers) {
            if (-not $p -or -not $p.CommandLine) { continue }
            $short = $p.CommandLine.Substring(0, [Math]::Min(78, $p.CommandLine.Length))
            Write-Host "         PID $($p.ProcessId)  $short" -ForegroundColor DarkGray
        }
        Write-Host '         Re-run with -Force to include child processes.' -ForegroundColor DarkGray
        $allOk = $false
    }

    Write-Host ''
    return $(if ($allOk) { 0 } else { 1 })
}

# --------------------------------------------------------------------------
# status
# --------------------------------------------------------------------------
function Invoke-Status {
    Write-Head 'Gremlins Health status'
    Write-Host "  root: $ProjectRoot" -ForegroundColor DarkGray
    Write-Host ''

    foreach ($key in $Services.Keys) {
        $svc = $Services[$key]
        $found = Get-ServiceProcess -Svc $svc
        if ($found) {
            $how = if ($found.Certainty -eq 'signature') { ' (matched by signature)' } else { '' }
            Write-Host ("  {0,-4} " -f $svc.Name) -NoNewline
            Write-Host 'RUNNING' -ForegroundColor Green -NoNewline
            Write-Host "  PID $($found.Proc.ProcessId)  - $($svc.Desc)$how"
        } else {
            Write-Host ("  {0,-4} " -f $svc.Name) -NoNewline
            Write-Host 'stopped' -ForegroundColor DarkGray -NoNewline
            Write-Host "  - $($svc.Desc)"
        }
    }

    Write-Host ''
    try {
        $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 3
        $b = $r.Content | ConvertFrom-Json
        Write-Ok "/health -> $($b.status), environment=$($b.environment), network=$($b.solana_network)"
    } catch {
        Write-Host '  [ -- ] /health not answering.' -ForegroundColor DarkGray
    }
    Write-Host ''
    return 0
}

# --------------------------------------------------------------------------
# Dispatch
# --------------------------------------------------------------------------
function Test-LaunchedFromExplorer {
    <#
        Double-clicking a .bat opens a console that closes the moment the
        script ends, hiding any error. Pause only in that case - pausing when
        the script was run from an existing terminal (or from CI) would hang.

        Chain when double-clicked:  explorer.exe -> cmd.exe -> powershell.exe
    #>
    try {
        $me = Get-CimInstance Win32_Process -Filter "ProcessId = $PID" -ErrorAction Stop
        $parent = Get-CimInstance Win32_Process -Filter "ProcessId = $($me.ParentProcessId)" -ErrorAction SilentlyContinue
        if (-not $parent) { return $false }
        $grand = Get-CimInstance Win32_Process -Filter "ProcessId = $($parent.ParentProcessId)" -ErrorAction SilentlyContinue
        if (-not $grand) { return $false }
        return $grand.Name -ieq 'explorer.exe'
    } catch {
        return $false
    }
}

$exitCode = switch ($Action) {
    'start'   { Invoke-Start }
    'stop'    { Invoke-Stop }
    'status'  { Invoke-Status }
    'restart' {
        Invoke-Stop | Out-Null
        Start-Sleep -Seconds 1
        Invoke-Start
    }
}

if (Test-LaunchedFromExplorer) {
    Write-Host 'Press Enter to close...' -ForegroundColor DarkGray
    [void][System.Console]::ReadLine()
}

exit $exitCode
