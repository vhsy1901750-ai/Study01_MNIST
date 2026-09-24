@echo off
rem 2026-09-20 19:09 KST
rem 탐색기에서 더블클릭하면 콘솔 창 없이 손글씨 숫자 인식기를 실행한다.
cd /d "%~dp0"
start "" pythonw app.py
