# Lo ejecuta la tarea programada: trae historias nuevas del repo y rellena los huecos de publicación.
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo
$log = Join-Path $env:USERPROFILE ".dato-curioso\tarea.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
"[$(Get-Date -Format 'yyyy-MM-dd HH:mm')] inicio" | Out-File -Append -Encoding utf8 $log
try { git pull --ff-only 2>&1 | Out-File -Append -Encoding utf8 $log } catch { "git pull falló: $_" | Out-File -Append -Encoding utf8 $log }
& "$Repo\.venv\Scripts\python.exe" -m datocurioso lote 2>&1 | Out-File -Append -Encoding utf8 $log
