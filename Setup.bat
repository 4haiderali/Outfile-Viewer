@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "EXPECTED_MARKER=OUT_VIEWER_VERSION_MARKER=v1.26_BACKGROUND_LAUNCHER"
set "APP_NAME=Outfile Viewer"
set "INSTALL_DIR=%LOCALAPPDATA%\OutfileViewer"
set "APP_URL=http://localhost:8600"
set "DESKTOP_LNK=%USERPROFILE%\Desktop\Outfile Viewer.lnk"
set "SERVER_CMD=%INSTALL_DIR%\Run_OutViewer_Server.cmd"
set "LOG_FILE=%INSTALL_DIR%\out_viewer_server.log"
set "LAUNCHER_CMD=%INSTALL_DIR%\Start_Outfile_Viewer.cmd"
set "LAUNCHER_VBS=%INSTALL_DIR%\Start_Outfile_Viewer.vbs"

echo.
echo ============================================================
echo Outfile Viewer v1.26 - Install / Update / Run
echo ============================================================
echo Source folder:
echo %CD%
echo.
echo Stable install folder:
echo %INSTALL_DIR%
echo.
echo This launcher starts Streamlit in a minimized server window.
echo You can close this installer CMD after the browser opens.
echo ============================================================
echo.

REM Pick Python launcher without touching user's default Python 2.7.
set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 (
  py -3 --version >nul 2>nul
  if not errorlevel 1 set "PY_CMD=py -3"
)

if "%PY_CMD%"=="" (
  where python3 >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python3"
)

if "%PY_CMD%"=="" (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)

if "%PY_CMD%"=="" (
  echo ERROR: Could not find Python 3.
  echo Install Python 3, then run this BAT again.
  pause
  exit /b 1
)

echo Using Python:
%PY_CMD% --version
echo.

echo Closing old Outfile Viewer / Streamlit processes if any...

REM Kill anything listening on the app port.
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8600" ^| findstr "LISTENING"') do (
  taskkill /PID %%a /F >nul 2>nul
)

REM Kill only Python/Streamlit processes that belong to this local app install.
REM This avoids admin rights in most cases by releasing locked .venv/.pyd files.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$install = [Environment]::GetEnvironmentVariable('INSTALL_DIR'); " ^
  "$patterns = @($install, 'OutfileViewer', 'OutViewerStable', 'streamlit run'); " ^
  "$procs = Get-CimInstance Win32_Process | Where-Object { " ^
  "  $_.CommandLine -and (" ^
  "    $_.CommandLine -like ('*' + $install + '*') -or " ^
  "    ($_.Name -match 'python|py|streamlit' -and $_.CommandLine -like '*app.py*' -and $_.CommandLine -like '*8600*')" ^
  "  )" ^
  "}; " ^
  "foreach ($p in $procs) { try { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }"

timeout /t 2 /nobreak >nul

echo.
echo Recreating stable install folder to prevent stale files...
if exist "%INSTALL_DIR%" (
  rmdir /s /q "%INSTALL_DIR%" >nul 2>nul
)

if exist "%INSTALL_DIR%" (
  echo First delete attempt failed. Waiting for Windows to release locked files...
  timeout /t 4 /nobreak >nul
  rmdir /s /q "%INSTALL_DIR%" >nul 2>nul
)

if exist "%INSTALL_DIR%" (
  echo.
  echo ERROR: Could not remove the old install folder because Windows still has a file locked.
  echo.
  echo Do this, then run this BAT again normally:
  echo   1. Close the minimized "Out Viewer Server" window if it is open.
  echo   2. Open Task Manager.
  echo   3. End any python.exe / py.exe / streamlit.exe process related to Outfile Viewer.
  echo.
  echo No administrator mode should be needed after that.
  echo.
  echo Locked folder:
  echo   %INSTALL_DIR%
  echo.
  pause
  exit /b 1
)

mkdir "%INSTALL_DIR%"

echo.
echo Copying project files into stable install folder...
robocopy "%CD%" "%INSTALL_DIR%" /E /XD __pycache__ .pytest_cache .git /XF "*.zip" >nul
if errorlevel 8 (
  echo ERROR: Robocopy failed.
  pause
  exit /b 1
)

echo.
echo Verifying installed app.py version marker...
findstr /C:"%EXPECTED_MARKER%" "%INSTALL_DIR%\app.py" >nul
if errorlevel 1 (
  echo.
  echo ERROR: Installed app.py does not contain the expected marker.
  echo Expected:
  echo   %EXPECTED_MARKER%
  echo.
  echo Installed file:
  echo   %INSTALL_DIR%\app.py
  echo.
  echo First 10 lines of installed app.py:
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content '%INSTALL_DIR%\app.py' -TotalCount 10"
  pause
  exit /b 1
)

echo.
echo Creating/repairing virtual environment...
%PY_CMD% -m venv "%INSTALL_DIR%\.venv"
if errorlevel 1 (
  echo ERROR: Could not create virtual environment.
  pause
  exit /b 1
)

echo.
echo Installing requirements...
"%INSTALL_DIR%\.venv\Scripts\python.exe" -m pip install --upgrade pip >nul
"%INSTALL_DIR%\.venv\Scripts\python.exe" -m pip install -r "%INSTALL_DIR%\requirements.txt"
if errorlevel 1 (
  echo ERROR: Requirements install failed.
  pause
  exit /b 1
)

echo.
echo Writing server and desktop launcher scripts...

(
echo @echo off
echo cd /d "%INSTALL_DIR%"
echo echo Starting Outfile Viewer server at %APP_URL%
echo echo Log file: "%LOG_FILE%"
echo "%INSTALL_DIR%\.venv\Scripts\python.exe" -m streamlit run "%INSTALL_DIR%\app.py" --server.port 8600 --server.headless true --browser.gatherUsageStats false ^> "%LOG_FILE%" 2^>^&1
) > "%SERVER_CMD%"

(
echo @echo off
echo setlocal
echo set "APP_URL=%APP_URL%"
echo set "SERVER_CMD=%SERVER_CMD%"
echo REM Start server only if port 8600 is not already listening.
echo netstat -ano ^| findstr ":8600" ^| findstr "LISTENING" ^>nul
echo if errorlevel 1 start "Out Viewer Server" /min cmd /c ""%%SERVER_CMD%%""
echo timeout /t 4 /nobreak ^>nul
echo start "" "%%APP_URL%%"
echo exit /b 0
) > "%LAUNCHER_CMD%"

(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run """" ^& "%LAUNCHER_CMD%" ^& """", 0, False
) > "%LAUNCHER_VBS%"

echo.
echo Creating desktop shortcut that starts the app, then opens the browser...
set "ICON_FILE=%INSTALL_DIR%\out_viewer\Icon.ico"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut($env:DESKTOP_LNK); " ^
  "$s.TargetPath = $env:LAUNCHER_VBS; " ^
  "$s.WorkingDirectory = $env:INSTALL_DIR; " ^
  "$s.IconLocation = $env:ICON_FILE + ',0'; " ^
  "$s.Description = 'Start Outfile Viewer locally'; " ^
  "$s.Save()"

echo.
echo Starting Outfile Viewer through the same desktop launcher...
wscript "%LAUNCHER_VBS%"

echo Waiting a few seconds for Streamlit to start...
timeout /t 5 /nobreak >nul

echo.
echo Opening browser:
echo %APP_URL%
start "" "%APP_URL%"

echo.
echo ============================================================
echo Out Viewer is running locally.
echo.
echo You may close THIS installer CMD window.
echo.
echo The desktop shortcut starts the server if needed, then opens the browser.
echo You can close the server window; use the desktop shortcut to start it again.
echo.
echo URL:
echo   %APP_URL%
echo.
echo Log file:
echo   %LOG_FILE%
echo.
echo Desktop shortcut:
echo   %DESKTOP_LNK%
echo ============================================================
echo.
pause
exit /b 0
