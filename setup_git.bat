@echo off
echo ========================================
echo Git Repository Setup
echo ========================================
echo.

echo Step 1: Initializing new Git repository...
git init
echo.

echo Step 2: Adding all files...
git add .
echo.

echo Step 3: Creating initial commit...
git commit -m "Initial commit: Multi-Agent Delivery System v3.0"
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create a new repository on GitHub/GitLab
echo 2. Run: git remote add origin YOUR_REPO_URL
echo 3. Run: git branch -M main
echo 4. Run: git push -u origin main
echo.
pause
