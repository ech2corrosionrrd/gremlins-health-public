@echo off
REM  Gremlins Health - stop, then start again.
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\service.ps1" -Action restart
exit /b %ERRORLEVEL%
