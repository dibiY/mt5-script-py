@echo off
REM ============================================================
REM  Double-click 3la had fichier f Windows bach tlanci kolchi.
REM  Kaykhddem setup.sh b Git Bash.
REM ============================================================
cd /d "%~dp0"

set "BASH_EXE="
if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%LocalAppData%\Programs\Git\bin\bash.exe" set "BASH_EXE=%LocalAppData%\Programs\Git\bin\bash.exe"

if not defined BASH_EXE (
  echo [X] Git Bash ma kaynch.
  echo     Telechargih mn: https://git-scm.com/download/win
  echo     Installih b les options par defaut, w 3awed double-click 3la run.bat
  pause
  exit /b 1
)

"%BASH_EXE%" setup.sh %*
