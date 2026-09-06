@echo off
REM  Gremlins Health - show which services are running.
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\service.ps1" -Action status
exit /b %ERRORLEVEL%
