@echo off
REM Limit Ollama to ~15 GiB VRAM; spill the rest to CPU
setx OLLAMA_MAX_VRAM 16106127360 >nul  &REM 15 GiB in bytes
echo.
echo ✔ OLLAMA_MAX_VRAM set to 15 GiB for future sessions.
echo Ollama will use up to 15 GiB VRAM; excess layers go to CPU RAM.
echo.
pause
