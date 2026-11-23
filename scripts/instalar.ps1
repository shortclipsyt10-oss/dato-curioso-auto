# Instala Dato Curioso en Windows y programa la tarea automática.
# Uso (PowerShell, dentro de la carpeta del repo):
#   powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

Write-Host "== 1/4 Python ==" -ForegroundColor Cyan
$py = $null
foreach ($v in @("3.12", "3.13", "3.11", "3.10")) {
    try { & py "-$v" -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { $py = @("py", "-$v"); break } } catch {}
}
if (-not $py) { Write-Host "Necesitas Python 3.10-3.13: winget install Python.Python.3.12" -ForegroundColor Red; exit 1 }
Write-Host "Usando $($py -join ' ')"

Write-Host "== 2/4 Entorno virtual y dependencias ==" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) { & $py[0] $py[1] -m venv .venv }
$vpy = Join-Path $Repo ".venv\Scripts\python.exe"
& $vpy -m pip install --upgrade pip
& $vpy -m pip install -r requirements.txt

Write-Host "== 3/4 Comprobación y modelos de voz (la primera vez descarga ~350 MB) ==" -ForegroundColor Cyan
& $vpy -m datocurioso comprobar

Write-Host "== 4/4 Tarea programada cada 3 horas ==" -ForegroundColor Cyan
$accion = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Repo\scripts\ejecutar.ps1`"" -WorkingDirectory $Repo
$inicio = (Get-Date).Date.AddHours([math]::Ceiling((Get-Date).Hour / 3) * 3).AddMinutes(-40)
if ($inicio -lt (Get-Date)) { $inicio = $inicio.AddHours(3) }
$disparo = New-ScheduledTaskTrigger -Once -At $inicio -RepetitionInterval (New-TimeSpan -Hours 3)
$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 3) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "DatoCurioso" -Action $accion -Trigger $disparo -Settings $ajustes -Description "Genera y programa los shorts de Dato Curioso" -Force | Out-Null
Write-Host "Tarea 'DatoCurioso' creada. Primera ejecución: $inicio" -ForegroundColor Green
Write-Host "Siguiente paso: conectar YouTube con  .venv\Scripts\python -m datocurioso autorizar"
