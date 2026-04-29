@echo off
echo ========================================
echo   追忆 - AI数字人系统
echo   此情可待成追忆，只是当时已惘然
echo ========================================
echo.

echo [1/2] 启动后端服务...
cd /d "%~dp0backend"
start "追忆-后端" cmd /k "D:\python3\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] 启动前端服务...
cd /d "%~dp0"
timeout /t 3 /nobreak >nul
start "追忆-前端" cmd /k "set PATH=C:\Program Files\nodejs;%%PATH%% && npm run dev"

echo.
echo 服务启动中...
echo 前端: http://localhost:1420
echo 后端: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
pause
