@echo off
echo ==========================================
echo   DONG GOI NEURALIS AI TUTOR THANH .EXE
echo ==========================================
echo Dang cai dat cong cu PyInstaller...
python -m pip install pyinstaller

echo.
echo Dang dong goi Source Code...
python -m PyInstaller --name "Neuralis-AI-Tutor" --onefile --windowed --add-data "web;web" main.py

echo.
echo ==========================================
echo HOAN TAT! 
echo Ban co the tim thay file chay tai:
echo d:\New Code\AIAgent\dist\Neuralis-AI-Tutor.exe
echo ==========================================
pause
