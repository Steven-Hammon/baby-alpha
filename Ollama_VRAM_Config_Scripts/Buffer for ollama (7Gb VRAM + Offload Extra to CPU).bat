@echo off
REM Limit Ollama to ~7 GiB VRAM; spill the rest to CPU
setx OLLAMA_MAX_VRAM 7516192768 >nul  &REM 7 GiB in bytes
echo.
echo ✔ OLLAMA_MAX_VRAM set to 7 GiB for future sessions.
echo Ollama will use up to 7 GiB VRAM; excess layers go to CPU RAM.
echo.
pause
