@echo off
rem safe_commit.bat - clears a stale .git/index.lock or HEAD.lock before
rem committing, then reports the TRUE push state (ahead of origin means
rem nothing has reached the remote yet, regardless of this repo's own
rem deploy trigger).
rem Usage:
rem   scripts\safe_commit.bat --check                       Lock + push-state check only
rem   scripts\safe_commit.bat -m "message" file1 file2       Add specific files, commit, report
rem   scripts\safe_commit.bat -m "message" --staged          Commit what's already staged
setlocal
set "REPO=%~dp0.."
cd /d "%REPO%"
where python >nul 2>nul
if errorlevel 1 (
    echo [safe_commit] "python" not found on PATH. Install Python or add it to PATH.
    exit /b 1
)
python "scripts\safe_commit.py" %*
endlocal
