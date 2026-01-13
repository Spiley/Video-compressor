@echo off
title Video Compressor Starter
echo ---------------------------------------------------
echo  Even geduld, software wordt gecontroleerd...
echo  (Dit repareert ook als 'pip' niet wordt herkend)
echo ---------------------------------------------------

REM --- POGING 1: Via de Windows Python Launcher (werkt meestal wel) ---
py -m pip install flask static-ffmpeg
IF %ERRORLEVEL% EQU 0 GOTO START_WITH_PY

REM --- POGING 2: Via standaard Python commando (als back-up) ---
python -m pip install flask static-ffmpeg
IF %ERRORLEVEL% EQU 0 GOTO START_WITH_PYTHON

echo.
echo ---------------------------------------------------
echo  FOUTMELDING:
echo  Python kon niet worden gevonden.
echo.
echo  Oplossing:
echo  1. De-installeer Python.
echo  2. Installeer Python opnieuw.
echo  3. Zorg dat je onderaan het vinkje "Add Python to PATH" AANVINKT.
echo ---------------------------------------------------
pause
exit

:START_WITH_PY
echo Starten via Launcher...
start http://127.0.0.1:5000
py app.py
pause
exit

:START_WITH_PYTHON
echo Starten via Python...
start http://127.0.0.1:5000
python app.py
pause
exit