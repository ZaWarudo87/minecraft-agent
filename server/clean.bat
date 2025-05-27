@echo off

echo Clean world files.

rmdir /s /q libraries
rmdir /s /q logs
rmdir /s /q versions
rmdir /s /q world

del /q *.json

echo Finished.
pause