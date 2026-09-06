@echo off
REM ==========================================================================
REM  Gremlins Health - stop the API, bot, dev server and Cloudflare tunnel.
REM
REM  Only processes belonging to THIS project directory are terminated.
REM  Other projects on this machine are left running.
REM
REM      stop.bat                    stop everything
REM      stop.bat api^|bot^|web^|tunnel  stop just one
REM      stop.bat force              also kill child processes
REM ==========================================================================
setlocal

REM See start.bat: capture %~dp0 before the first shift.
set "HERE=%~dp0"
set "PS_ARGS=-Action stop"

:parse
if "%~1"=="" goto run
if /I "%~1"=="api"    (set "PS_ARGS=%PS_ARGS% -Only api"    ) & shift & goto parse
if /I "%~1"=="bot"    (set "PS_ARGS=%PS_ARGS% -Only bot"    ) & shift & goto parse
if /I "%~1"=="web"    (set "PS_ARGS=%PS_ARGS% -Only web"    ) & shift & goto parse
if /I "%~1"=="tunnel" (set "PS_ARGS=%PS_ARGS% -Only tunnel" ) & shift & goto parse
if /I "%~1"=="force"  (set "PS_ARGS=%PS_ARGS% -Force"       ) & shift & goto parse
echo Unknown option: %~1
echo Usage: stop.bat [api^|bot^|web^|tunnel] [force]
exit /b 2

:run
powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%scripts\service.ps1" %PS_ARGS%
exit /b %ERRORLEVEL%
