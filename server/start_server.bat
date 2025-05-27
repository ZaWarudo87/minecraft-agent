@echo off
cd /d %~dp0
java -Xmx2G -Xms1G -jar server.jar nogui
pause
