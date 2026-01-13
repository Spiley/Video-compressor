@echo off
title Video Compressor Starter
echo ---------------------------------------------------
echo  Even geduld, het systeem wordt klaargemaakt...
echo  De eerste keer kan dit een paar minuten duren.
echo ---------------------------------------------------

REM Installeer Flask en static-ffmpeg (inclusief ffmpeg binaire bestanden)
pip install flask static-ffmpeg

REM Open de browser automatisch
start http://127.0.0.1:5000

REM Start de server
python app.py

pause