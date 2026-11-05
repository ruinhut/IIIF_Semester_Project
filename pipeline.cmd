@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
if exist "%~dp0Code_git\.venv\Scripts\python.exe" (
  "%~dp0Code_git\.venv\Scripts\python.exe" "%~dp0pipeline.py" %*
) else (
  py -3 "%~dp0pipeline.py" %*
)
exit /b %errorlevel%
