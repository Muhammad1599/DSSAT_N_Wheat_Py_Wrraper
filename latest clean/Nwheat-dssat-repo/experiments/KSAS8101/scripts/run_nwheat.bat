@echo off
echo ========================================
echo KSAS8101 NWheat Experiment Runner
echo ========================================
echo.
echo Running DSSAT NWheat model for KSAS8101...
echo Kansas State University Winter Wheat Study
echo.

REM Run DSSAT with correct arguments (Mode A = All treatments in FileX)
DSCSM048.EXE A KSAS8101.WHX

echo.
echo ========================================
echo Simulation completed!
echo ========================================
echo.
echo Output files generated:
dir *.SUM *.PLT *.OUT *.ETH 2>nul

echo.
echo Press any key to view summary results...
pause >nul

REM Try to display summary file if it exists
if exist *.SUM (
    echo.
    echo ========================================
    echo SUMMARY RESULTS:
    echo ========================================
    type *.SUM
) else (
    echo No summary file found.
)

echo.
echo Press any key to exit...
pause >nul
