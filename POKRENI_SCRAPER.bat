@echo off
cd /d "%~dp0"
echo Pokrecem CompanyWall Scraper...
echo.
echo Aktiviram Python virtual environment...
call .venv_new\Scripts\activate.bat
echo.
echo Otvaram browser na: http://localhost:8505
echo.
start "" "http://localhost:8505"
echo.
echo Pokrecem Streamlit aplikaciju...
streamlit run streamlit_ui_clean.py --server.port 8505
pause