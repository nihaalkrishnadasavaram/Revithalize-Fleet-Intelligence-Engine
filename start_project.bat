@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ============================================
echo   RFIE - ReVithalize Fleet Intelligence Engine
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Install Python 3.10 or newer from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js was not found.
    echo Install the LTS version from https://nodejs.org/ and run this file again.
    pause
    exit /b 1
)

if not exist "backend\venv\Scripts\python.exe" (
    echo Creating the Python virtual environment...
    python -m venv backend\venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
)

if not exist "backend\venv\deps_installed.txt" (
    echo Installing backend dependencies. This can take a few minutes...
    "backend\venv\Scripts\python.exe" -m pip install --upgrade pip
    "backend\venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo [ERROR] Backend dependency installation failed.
        pause
        exit /b 1
    )
    echo installed> "backend\venv\deps_installed.txt"
)

if not exist "frontend\node_modules" (
    echo Installing frontend dependencies. This can take a few minutes...
    pushd frontend
    call npm install
    if errorlevel 1 (
        popd
        echo [ERROR] Frontend dependency installation failed.
        pause
        exit /b 1
    )
    popd
)

echo Starting the backend on http://127.0.0.1:8000 ...
start "RFIE Backend" /D "%ROOT%backend" cmd /k "venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo Starting the frontend on http://localhost:5173 ...
start "RFIE Frontend" /D "%ROOT%frontend" cmd /k "npm run dev"

echo.
echo The first backend start creates the database and generates 3,000 vehicles.
echo This takes a few seconds. The browser will open shortly.
timeout /t 8 /nobreak >nul
start "" http://localhost:5173

echo.
echo Dashboard : http://localhost:5173
echo API docs  : http://127.0.0.1:8000/docs
echo Close the two server windows to stop the project.
endlocal
