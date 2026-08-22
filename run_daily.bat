@echo off

title LeetCode Daily Automator

cd /d "%~dp0"

echo.
echo ==============================================
echo       LEETCODE DAILY AUTOMATOR
echo ==============================================
echo.

python scripts\automation.py

echo.
pause