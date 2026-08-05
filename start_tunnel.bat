@echo off
:loop
echo [%date% %time%] Starting TradeMaster tunnel...
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -i "%USERPROFILE%\.ssh\serveo_key" -R 80:localhost:5000 localhost.run
echo [%date% %time%] Tunnel died, restarting in 10s...
timeout /t 10 /nobreak >nul
goto loop
