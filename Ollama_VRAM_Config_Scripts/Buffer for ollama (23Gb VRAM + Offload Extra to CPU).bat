@echo off
REM Limit Ollama to ~23 GiB VRAM; spill the rest to CPU
setx OLLAMA_MAX_VRAM 24696061952 >nul  &REM 23 GiB in bytes
echo.
echo ✔ OLLAMA_MAX_VRAM set to 23 GiB for future sessions.
echo Ollama will use up to 23 GiB VRAM; excess layers go to CPU RAM.
echo.
pause
