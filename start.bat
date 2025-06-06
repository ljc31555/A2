@echo off
REM 自动激活虚拟环境并运行主程序
cd /d %~dp0
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python main.py
pause 