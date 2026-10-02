@echo off
title GIGAMOGG Studio
start "" "%~dp0dist\GIGAMOGG\GIGAMOGG.exe" 2>nul || python "%~dp0desktop_app.py"
