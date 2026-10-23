$ErrorActionPreference='Stop'
$inputRoot=Join-Path $env:USERPROFILE 'Desktop\input'
$out=Join-Path $env:USERPROFILE 'Desktop\output'
try {
  $identity=[ordered]@{timestamp=[DateTime]::UtcNow.ToString('o');username=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name;sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value;profile=$env:USERPROFILE;localappdata=$env:LOCALAPPDATA;computer=[Environment]::MachineName;os=(Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture);twmarket_home_existed=(Test-Path "$env:LOCALAPPDATA\TW-Market");python_on_path=[bool](Get-Command python.exe -ErrorAction SilentlyContinue);git_on_path=[bool](Get-Command git.exe -ErrorAction SilentlyContinue);guest_prerequisite_existed=(Test-Path C:\A5\Python313\python.exe)}
  $identity | ConvertTo-Json -Depth 6 | Set-Content "$out\fresh-environment.json" -Encoding UTF8
  if ($identity.twmarket_home_existed -or $identity.guest_prerequisite_existed) { throw 'guest is not fresh for A5' }
  New-Item -ItemType Directory -Path C:\A5\Temp -Force | Out-Null
  $expected=Get-Content "$inputRoot\installer-identity.json" -Raw | ConvertFrom-Json
  $installer="$inputRoot\python-3.13.9-amd64.exe"
  if ((Get-FileHash $installer -Algorithm SHA256).Hash.ToLower() -ne $expected.sha256 -or $expected.signature_status -ne 'Valid') { throw 'prerequisite identity mismatch' }
  Copy-Item -LiteralPath $installer -Destination C:\A5\python-installer.exe
  'INSTALLING_OFFICIAL_GUEST_PYTHON' | Set-Content "$out\stage.txt"
  $args='/quiet /norestart InstallAllUsers=0 TargetDir=C:\A5\Python313 PrependPath=0 Include_launcher=0 Include_test=0 Include_doc=0 Include_tcltk=0 Include_dev=0 Include_tools=0 CompileAll=0 Shortcuts=0 AssociateFiles=0 /log C:\Users\WDAGUtilityAccount\Desktop\output\python-install.log'
  $p=Start-Process -FilePath C:\A5\python-installer.exe -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
  if ($p.ExitCode -ne 0) { throw "prerequisite exit $($p.ExitCode)" }
  $env:TEMP='C:\A5\Temp';$env:TMP=$env:TEMP;$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1';$env:PYTHONPATH=$null;$env:PYTHONHOME=$null
  $zip=Get-Item "$inputRoot\TW-Market-1.0.0-windows-x64.zip"
  Expand-Archive -LiteralPath $zip.FullName -DestinationPath 'C:\A5\Unicode 路徑\deeper app' -Force
  $bundle=(Get-ChildItem -LiteralPath 'C:\A5\Unicode 路徑\deeper app' -Directory | Select-Object -First 1).FullName
  @{bundle=$bundle;zip_sha256=(Get-FileHash $zip.FullName -Algorithm SHA256).Hash.ToLower();venv_existed_before=(Test-Path "$bundle\runtime\venv");git_existed=(Test-Path "$bundle\.git");python_installer_sha256=$expected.sha256;installer_exit_code=$p.ExitCode} | ConvertTo-Json | Set-Content "$out\package-before-bootstrap.json" -Encoding UTF8
  'OFFLINE_PACKAGE_BOOTSTRAP' | Set-Content "$out\stage.txt"
  $p=Start-Process -FilePath C:\A5\Python313\python.exe -ArgumentList @('-B',"`"$bundle\bootstrap\bootstrap.py`"",'--bundle',"`"$bundle`"") -RedirectStandardOutput "$out\bootstrap.stdout.log" -RedirectStandardError "$out\bootstrap.stderr.log" -Wait -PassThru -WindowStyle Hidden
  if ($p.ExitCode -ne 0) { throw "bootstrap exit $($p.ExitCode)" }
  'PRODUCT_RUNTIME_ACCEPTANCE' | Set-Content "$out\stage.txt"
  $p=Start-Process -FilePath "$bundle\runtime\venv\Scripts\python.exe" -ArgumentList @('-B',"$inputRoot\fresh_runtime.py") -RedirectStandardOutput "$out\runtime.stdout.log" -RedirectStandardError "$out\runtime.stderr.log" -Wait -PassThru -WindowStyle Hidden
  @{exit_code=$p.ExitCode;timestamp=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content "$out\runtime-exit.json" -Encoding UTF8
  if ($p.ExitCode -ne 0) { throw "runtime exit $($p.ExitCode)" }
  'COMPLETE' | Set-Content "$out\stage.txt"
} catch { @{status='FAIL';error=$_.Exception.Message} | ConvertTo-Json | Set-Content "$out\failed.json" -Encoding UTF8 }
