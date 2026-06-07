@echo off
cd /d "%~dp0"
echo Avvio Gestionale Studio...
python -m streamlit run app_studio.py --server.address 0.0.0.0
pause