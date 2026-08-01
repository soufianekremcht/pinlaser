@echo off
setlocal
cd /d "%~dp0.."

py packaging\make_icon.py assets\app_icon_pin-laser.png packaging\pinlaser.ico || goto :error
py -m PyInstaller --noconfirm --clean --windowed --onefile --name PinLaser ^
    --icon "%CD%\packaging\pinlaser.ico" ^
    --version-file "%CD%\packaging\version_info.txt" ^
    --add-data "%CD%\assets\app_icon_pin-laser.png;." ^
    --specpath packaging --workpath build --distpath dist ^
    main.py || goto :error

echo.
echo Build complete: dist\PinLaser.exe
exit /b 0

:error
echo Build FAILED.
exit /b 1
