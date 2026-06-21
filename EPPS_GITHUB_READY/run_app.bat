@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Membuat virtual environment...
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo Menginstall dependency...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Menjalankan aplikasi EPPS...
streamlit run app.py

