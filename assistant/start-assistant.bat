@echo off
REM Start the RAYA AI receptionist kiosk using the prebuilt virtual environment.
pushd %~dp0
..\RAYA-MODULES\TOKENN\env\Scripts\python.exe app.py
popd
