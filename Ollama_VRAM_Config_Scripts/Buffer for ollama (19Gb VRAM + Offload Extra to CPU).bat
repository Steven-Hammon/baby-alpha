@echo off
REM Limit Ollama to ~19 GiB VRAM; spill the rest to CPU
setx OLLAMA_MAX_VRAM 20401094656 >nul  &REM 19 GiB in bytes
echo.
echo ✔ OLLAMA_MAX_VRAM set to 19 GiB for future sessions.
echo Ollama will use up to 19 GiB VRAM; excess layers go to CPU RAM.
echo.
pause
