@echo off
REM install.bat

REM ------------------------------------------------
REM 1) Create & activate virtualenv
REM ------------------------------------------------
python -m venv venv
call venv\Scripts\activate

REM ------------------------------------------------
REM 2) Upgrade pip & install requirements
REM ------------------------------------------------
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM ------------------------------------------------
REM 3) Pull your Ollama models
REM ------------------------------------------------
ollama pull gemma3:4b
ollama pull gemma3:12b-it-qat
ollama pull mxbai-embed-large


echo.
echo Virtual environment setup complete, dependencies installed, and llama3.2 model pulled.
echo To activate the virtual environment in the future, run:
echo     call venv\Scripts\activate
pause
