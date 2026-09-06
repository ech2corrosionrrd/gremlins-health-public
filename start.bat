@echo off
REM ==========================================================================
REM  Gremlins Health - start the backend API and the Telegram bot.
REM
REM  Double-click, or run from a terminal:
REM      start.bat            API + bot
REM      start.bat web        + Mini App dev server (local only)
REM      start.bat tunnel     + dev server + Cloudflare tunnel
REM                             -> https://your-tunnel.example.com
REM                             This is what Telegram needs (HTTPS only).
REM      start.bat api        API only
REM      start.bat bot        bot only
REM      start.bat fast       skip database migrations
REM ==========================================================================
setlocal

REM Capture the script directory BEFORE any shift: shift moves %0 as well,
REM after which %~dp0 resolves against the current directory instead.
set "HERE=%~dp0"
set "PS_ARGS=-Action start"

:parse
if "%~1"=="" goto run
if /I "%~1"=="web"    (set "PS_ARGS=%PS_ARGS% -WithWeb"        ) & shift & goto parse
if /I "%~1"=="tunnel" (set "PS_ARGS=%PS_ARGS% -WithTunnel"     ) & shift & goto parse
if /I "%~1"=="api"    (set "PS_ARGS=%PS_ARGS% -Only api"       ) & shift & goto parse
if /I "%~1"=="bot"    (set "PS_ARGS=%PS_ARGS% -Only bot"       ) & shift & goto parse
if /I "%~1"=="fast"   (set "PS_ARGS=%PS_ARGS% -SkipMigrations" ) & shift & goto parse
echo Unknown option: %~1
echo Usage: start.bat [web^|tunnel^|api^|bot] [fast]
exit /b 2

:run
powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%scripts\service.ps1" %PS_ARGS%
exit /b %ERRORLEVEL%
