@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    set "CSV_PY=.venv\Scripts\python.exe"
    goto kontrol
)
if exist "..\.venv\Scripts\python.exe" (
    set "CSV_PY=..\.venv\Scripts\python.exe"
    goto kontrol
)
python -m venv .venv
if errorlevel 1 goto hata
set "CSV_PY=.venv\Scripts\python.exe"
:kontrol
"%CSV_PY%" -c "import streamlit, pandas, numpy; assert (streamlit.__version__, pandas.__version__, numpy.__version__) == ('1.67.0', '3.1.1', '2.5.5')" >nul 2>&1
if errorlevel 1 (
    "%CSV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 goto hata
)
"%CSV_PY%" -m streamlit run app.py --server.headless true
if errorlevel 1 goto hata
exit /b 0
:hata
echo Uygulama baslatilamadi. Yukaridaki hata mesajini kontrol et.
pause
exit /b 1
