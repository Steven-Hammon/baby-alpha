@echo off
echo Removing OLLAMA_CONTEXT_LENGTH from user environment...
reg delete "HKCU\Environment" /F /V OLLAMA_CONTEXT_LENGTH >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo ✔ OLLAMA_CONTEXT_LENGTH has been removed.
) else (
    echo ⚠ OLLAMA_CONTEXT_LENGTH was not set or could not be removed.
)

echo.
echo Please **quit** and then **re-open** your Ollama desktop app
echo so it reverts to its default context window size.
pause
