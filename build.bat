@echo off
:: aegisScout - Build Launcher v3.2
:: Double-click or run: build.bat
::
:: Build modes:
::   1) Hizli Build (default) - .env, config, data, logs preserved
::   2) Temiz Build           - Everything deleted, fresh build
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
set "BUILD_SCRIPT=%ROOT%scripts\build_exe.py"

:: ASCII Banner
echo.
echo  ==========================================
echo     aegisScout Build Launcher v3.2 
echo     Optimized ^| Fast ^| Production-Ready
echo  ==========================================
echo.

:: ---- Build Mode Selection ----
set BUILD_MODE=
echo Build mode:
echo   [1] Hizli Build (default) - .env, config, data, logs preserved  
echo   [2] Temiz Build           - Full clean rebuild
echo.
set /p "BUILD_MODE=Choice [1/2] (Enter = 1): "
if "%BUILD_MODE%"=="" set "BUILD_MODE=1"
echo.

:: ---- Terminate running aegisScout.exe if active ----
taskkill /f /im aegisScout.exe 2>nul

if "%BUILD_MODE%"=="2" (
    echo [PREP] TEMIZ BUILD - all old files will be deleted
    echo.
    if exist "%ROOT%dist\." (
        rmdir /s /q "%ROOT%dist" 2>nul && echo [OK] dist/ fully removed
    )
) else (
    echo [PREP] HIZLI BUILD - user data will be preserved
    echo.
)

:: Clean build/ (PyInstaller temp dir - always safe)
if exist "%ROOT%build\." (
    rmdir /s /q "%ROOT%build" 2>nul && echo [OK] build/ cleaned
)
rmdir /s /q "%ROOT%build\aegisScout" 2>nul
rmdir /s /q "%ROOT%build\build_exe" 2>nul
del /q "%ROOT%*.spec" 2>nul
echo.

:: ---- Check UPX (optional) ----
where upx >nul 2>nul
if !errorlevel! equ 0 (
    echo [OK] UPX detected - EXE compression enabled
) else (
    echo [!] UPX not found - EXE will be larger
)
echo.

:: ---- Detect Python ----
echo [..] Detecting Python 3.11+
set "PYTHON_CMD="

:: Try py launcher first
where py >nul 2>nul
if !errorlevel! equ 0 (
    for %%v in (3.11 3.12 3.13) do (
        if not defined PYTHON_CMD (
            for /f "delims=" %%i in ('py -%%v -c "import sys;print(sys.executable)" 2^>nul') do set "PYTHON_CMD=%%i"
            if defined PYTHON_CMD (
                if exist !PYTHON_CMD! (echo [OK] Found Python %%v) else set "PYTHON_CMD="
            )
        )
    )
)

:: Fallback: direct path checks
if not defined PYTHON_CMD (
    for %%p in (
        "C:\Users\mrSpy\AppData\Local\Programs\Python\Python311\python.exe"
        "C:\Users\mrSpy\AppData\Local\Programs\Python\Python312\python.exe"
        "C:\Users\mrSpy\AppData\Local\Programs\Python\Python313\python.exe"
        "C:\Python311\python.exe"
        "C:\Python312\python.exe"
        "C:\Python313\python.exe"
        "C:\Program Files\Python311\python.exe"
        "C:\Program Files\Python312\python.exe"
        "C:\Program Files\Python313\python.exe"
        "C:\Program Files (x86)\Python311\python.exe"
        "C:\Program Files (x86)\Python312\python.exe"
        "C:\Program Files (x86)\Python313\python.exe"
    ) do (
        if not defined PYTHON_CMD (
            if exist %%p (set "PYTHON_CMD=%%~p")
        )
    )
)

:: Final fallback: python from PATH
if not defined PYTHON_CMD (
    where python >nul 2>nul
    if !errorlevel! equ 0 (
        for /f "delims=" %%i in ('python -c "import sys;print(sys.executable)" 2^>nul') do set "PYTHON_CMD=%%i"
    )
)

if not defined PYTHON_CMD (
    echo [ERROR] Python 3.11+ not found
    echo Install: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Strip any quotes from PYTHON_CMD  
set "PYTHON_CMD=!PYTHON_CMD:"=!"
echo [OK] Python: !PYTHON_CMD!
"!PYTHON_CMD!" --version 2>nul
echo.

:: ---- Validate Packages ----
echo [..] Checking required packages...
"!PYTHON_CMD!" -c "import PyInstaller" 2>nul
if !errorlevel! neq 0 (
    echo [!] PyInstaller not found - installing...
    "!PYTHON_CMD!" -m pip install pyinstaller
    if !errorlevel! neq 0 (
        echo [ERROR] PyInstaller install failed
        pause
        exit /b 1
    )
)
echo [OK] PyInstaller

"!PYTHON_CMD!" -c "import webview" 2>nul
if !errorlevel! neq 0 (
    echo [!] pywebview not found - GUI will not work
) else (
    echo [OK] pywebview
)
echo.

:: ---- Validate Project Files ----
echo [..] Validating project structure...
set MISSING=0
if not exist "%ROOT%scripts\build_exe.spec" (
    echo [ERROR] scripts\build_exe.spec not found
    set MISSING=1
)
if not exist "%ROOT%src\aegisScout\main.py" (
    echo [ERROR] src\aegisScout\main.py not found
    set MISSING=1
)
if exist "%ROOT%src\aegisScout\assets\logo.ico" (
    echo [OK] logo.ico found - EXE icon will be used
) else (
    echo [WARN] logo.ico not found
)
if !MISSING! equ 1 (
    echo [ERROR] Critical files missing. Build cancelled.
    pause
    exit /b 1
)
echo [OK] Project structure validated.
echo.

:: ---- Build ----
echo [..] Starting PyInstaller build...
echo.
if "%BUILD_MODE%"=="2" (
    "!PYTHON_CMD!" "!BUILD_SCRIPT!" --clean
) else (
    "!PYTHON_CMD!" "!BUILD_SCRIPT!"
)

:: Check result and branch
if errorlevel 1 goto build_failed
if not errorlevel 0 goto build_failed

:: ---- Build Success ----
echo.
echo ==========================================
echo     [OK] BUILD SUCCESSFUL
echo ==========================================
echo.
echo  Output: dist\aegisScout.exe
if exist "%ROOT%dist\aegisScout.exe" (
    for %%f in ("%ROOT%dist\aegisScout.exe") do (
        set FSIZE=%%~zf
        set /a FSIZE_MB=!FSIZE! / 1048576
        echo  Size: !FSIZE_MB! MB
    )
)
echo.

:: Copy .env to dist
if exist "%ROOT%.env" (
    copy /Y "%ROOT%.env" "%ROOT%dist\.env" >nul
    echo [OK] .env copied to dist/
) else (
    echo [WARN] .env not found - API keys missing
    if exist "%ROOT%.env.example" (
        copy /Y "%ROOT%.env.example" "%ROOT%dist\.env" >nul
        echo [OK] .env.example copied as .env - keys are empty
    )
)

:: Copy config to dist
if exist "%ROOT%config" (
    xcopy /E /I /Y "%ROOT%config" "%ROOT%dist\config" >nul 2>nul
    echo [OK] config/ copied to dist/
)

echo.
echo  Run: dist\aegisScout.exe
echo.
goto build_end

:: ---- Build Failed ----
:build_failed
echo.
echo ==========================================
echo     [ERROR] BUILD FAILED
echo ==========================================
echo.
echo  Tips:
echo   1. Make sure you have Python 3.11+
echo   2. pip install pyinstaller
echo   3. pip install -e .
echo   4. pip install pywebview bottle proxy_tools

:build_end
echo.
pause
