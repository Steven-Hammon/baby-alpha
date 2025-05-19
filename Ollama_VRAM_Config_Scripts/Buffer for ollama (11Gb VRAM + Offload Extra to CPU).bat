@echo off
REM Limit Ollama to ~11 GiB VRAM; spill the rest to CPU
setx OLLAMA_MAX_VRAM 11811160064 >nul  &REM 11 GiB in bytes
echo.
echo ✔ OLLAMA_MAX_VRAM set to 11 GiB for future sessions.
echo Ollama will use up to 11 GiB VRAM; excess layers go to CPU RAM.
echo.
pause
