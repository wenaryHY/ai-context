@echo off
setlocal
if "%~1"=="" (
  echo Usage: scripts\release.cmd X.Y.Z
  exit /b 1
)
powershell -ExecutionPolicy Bypass -File "%~dp0release.ps1" -Version %1
