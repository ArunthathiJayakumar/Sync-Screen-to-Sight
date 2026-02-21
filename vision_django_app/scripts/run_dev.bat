@echo off
REM Wrapper to run the PowerShell setup_and_run script. Usage:
REM   scripts\run_dev.bat    (run lightweight install)
REM   scripts\run_dev.bat Full (run full install)

REM Pass all arguments directly through to the PowerShell script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0setup_and_run.ps1" %*
