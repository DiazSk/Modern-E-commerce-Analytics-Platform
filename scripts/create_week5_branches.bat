@echo off
REM ==============================================================================
REM Week 5 Feature Branch Creation Script (Windows)
REM ==============================================================================
REM Purpose: Create feature branches for Week 5 implementation
REM Usage: scripts\create_week5_branches.bat
REM ==============================================================================

echo Starting Week 5 feature branch creation...
echo.

REM Ensure we're on develop branch
git checkout develop
if %errorlevel% neq 0 (
    echo Error: Failed to checkout develop branch
    exit /b %errorlevel%
)

REM Pull latest changes
git pull origin develop
if %errorlevel% neq 0 (
    echo Error: Failed to pull latest changes
    exit /b %errorlevel%
)

echo.
echo Creating Week 5 feature branches...
echo.

REM Feature 1: Query Optimization (Day 1-2)
echo Creating feature/week5-query-optimization...
git checkout -b feature/week5-query-optimization
if %errorlevel% neq 0 (
    echo Error: Failed to create query optimization branch
    exit /b %errorlevel%
)
git push -u origin feature/week5-query-optimization

REM Back to develop
git checkout develop

REM Feature 2: Great Expectations (Day 3-5)
echo Creating feature/week5-great-expectations...
git checkout -b feature/week5-great-expectations
if %errorlevel% neq 0 (
    echo Error: Failed to create great expectations branch
    exit /b %errorlevel%
)
git push -u origin feature/week5-great-expectations

REM Back to develop
git checkout develop

REM Feature 3: dbt Tests (Day 6-7)
echo Creating feature/week5-dbt-tests...
git checkout -b feature/week5-dbt-tests
if %errorlevel% neq 0 (
    echo Error: Failed to create dbt tests branch
    exit /b %errorlevel%
)
git push -u origin feature/week5-dbt-tests

REM Back to develop
git checkout develop

echo.
echo ✅ All Week 5 feature branches created successfully!
echo.
echo Branches created:
echo   - feature/week5-query-optimization
echo   - feature/week5-great-expectations
echo   - feature/week5-dbt-tests
echo.
echo To start working on query optimization:
echo   git checkout feature/week5-query-optimization
echo.

pause
