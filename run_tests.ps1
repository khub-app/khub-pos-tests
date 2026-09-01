# Reads data/test_data.xlsx -> RunConfig sheet (Environment + Suite toggles)
# and runs the matching tests. Mirrors khub-web-tests' run_tests.ps1, scaled
# down to this project's setup: Appium drives ONE device (emulator or
# real_device) at a time, so there's no Headless/Workers/multi-env toggle
# here - just which environment to target and which suite(s) to run.
#
# Which test gets which suite marker is controlled by data/test_data.xlsx's
# Tags sheet (FilePath | smoke | regression columns) - conftest.py applies
# those markers automatically at collection time.
#
# The Allure HTML report is regenerated automatically after the run
# (conftest.py's pytest_sessionfinish hook) - no separate step needed here.

$cfg    = & "venv\Scripts\python.exe" scripts/read_run_config.py | ConvertFrom-Json
$envName = $cfg.environment
$suites  = $cfg.suites

if ($cfg.error) {
    Write-Host "[ERROR] $($cfg.error)"
    exit 1
}
if (-not $suites -or $suites.Count -eq 0) {
    Write-Host "[WARNING] No suites enabled in the RunConfig sheet. Set Smoke or Regression to Yes."
    exit 1
}

Write-Host ""
Write-Host "=== Config read from RunConfig sheet ==="
Write-Host "  Suite(s)     : $($suites -join ', ')"
Write-Host "  Environment  : $envName"
Write-Host "========================================="
Write-Host ""

$markerExpr = $suites -join " or "
& "venv\Scripts\python.exe" -m pytest tests/ -v -m "$markerExpr" --env=$envName
exit $LASTEXITCODE
