$ErrorActionPreference = 'Stop'
$env:PATH = 'C:\Windows\System32;C:\Windows'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
$work = 'C:\twmarket_temp\l7-a3\guest'
$output = 'C:\a3-output'
$result = @{status='FAIL';stage='identity'}
try {
    $os = Get-CimInstance Win32_OperatingSystem
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $fresh = @{
        timestamp=(Get-Date).ToUniversalTime().ToString('o')
        edition=$os.Caption;build=$os.BuildNumber;version=$os.Version;architecture=$os.OSArchitecture
        username=$identity.Name;sid=$identity.User.Value;profile=$env:USERPROFILE
        localappdata=$env:LOCALAPPDATA;computer=$env:COMPUTERNAME
        preexisting_TWMarket=(Test-Path -LiteralPath "$env:LOCALAPPDATA\TW-Market")
        preexisting_acceptance_root=(Test-Path -LiteralPath $work)
        python_on_PATH=[bool](Get-Command python.exe -ErrorAction SilentlyContinue)
        git_on_PATH=[bool](Get-Command git.exe -ErrorAction SilentlyContinue)
        preexisting_python_processes=@(Get-Process python -ErrorAction SilentlyContinue).Count
        source_checkout_mapped=$false;developer_venv_mapped=$false;host_profile_mapped=$false
        networking='Disabled by WSB'
    }
    $fresh | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$output\fresh-state.json" -Encoding utf8
    if ($fresh.preexisting_TWMarket -or $fresh.preexisting_acceptance_root -or $fresh.python_on_PATH -or $fresh.git_on_PATH -or $fresh.preexisting_python_processes) { throw 'Guest is not fresh' }
    if ($os.Caption -notlike '*Windows 11*' -or $os.OSArchitecture -ne '64-bit') { throw 'Genuine Windows11 x64 required' }
    New-Item -ItemType Directory -Force -Path "$work\provision-temp" | Out-Null
    $env:TEMP="$work\provision-temp";$env:TMP=$env:TEMP
    $expected=Get-Content -LiteralPath C:\a3-input\artifact-identity.json -Raw | ConvertFrom-Json
    $observed=(Get-FileHash -LiteralPath C:\a3-input\native.zip -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($observed -ne $expected.sha256) { throw 'Native ZIP hash mismatch' }
    @{expected=$expected;observed_sha256=$observed;verified=$true} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$output\artifact-verification.json" -Encoding utf8
    $result.stage='prerequisite'
    $prerequisite=Get-Content -LiteralPath C:\a3-input\prerequisite-identity.json -Raw | ConvertFrom-Json
    $zip='C:\a3-input\python-prerequisite.zip'
    if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $prerequisite.sha256) { throw 'Official CPython prerequisite package hash mismatch' }
    Copy-Item -LiteralPath $zip -Destination "$work\python-prerequisite.zip"
    Expand-Archive -LiteralPath "$work\python-prerequisite.zip" -DestinationPath "$work\prerequisite"
    $python="$work\prerequisite\tools\python.exe"
    if ((Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash.ToLowerInvariant() -ne $prerequisite.python_exe_sha256) { throw 'CPython signed executable hash mismatch' }
    $version=& $python -B -c "import sys,json;print(json.dumps({'version':sys.version,'executable':sys.executable,'bits':64 if sys.maxsize>2**32 else 32}))"
    if ($LASTEXITCODE -ne 0) { throw 'Guest prerequisite cannot execute' }
    @{runtime=($version | ConvertFrom-Json);official_package_sha256=$prerequisite.sha256;catalog_SHA512_verified=$prerequisite.official_catalog_hash_verified;network_requests=0;scope='disposable guest prerequisite only';provisioning='official CPython NuGet 3.13.9 archive, no MSI or Registry/PATH installation'} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$output\prerequisite.json" -Encoding utf8
    $result.stage='native-acceptance'
    $startInfo=New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName=$python
    $startInfo.Arguments="-B C:\a3-input\scripts\accept_native_distribution.py --zip C:\a3-input\native.zip --python $python --run $work\acceptance --guard-base C:\twmarket_temp\l7-a3"
    $startInfo.WorkingDirectory=$work
    $startInfo.UseShellExecute=$false
    $startInfo.CreateNoWindow=$true
    $startInfo.RedirectStandardOutput=$true
    $startInfo.RedirectStandardError=$true
    $accept=New-Object System.Diagnostics.Process
    $accept.StartInfo=$startInfo
    [void]$accept.Start()
    $stdoutTask=$accept.StandardOutput.ReadToEndAsync()
    $stderrTask=$accept.StandardError.ReadToEndAsync()
    $finished=$false
    for ($attempt=0; $attempt -lt 180; $attempt++) {
        if ($accept.WaitForExit(5000)) { $finished=$true }
        @{stage='native-acceptance';attempt=$attempt;process_id=$accept.Id;finished=$finished;timestamp=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath "$output\heartbeat.json" -Encoding utf8
        if ($finished) { break }
    }
    if (-not $finished) { throw 'Bounded guest Native acceptance timeout' }
    $accept.WaitForExit()
    $exitCode=$accept.ExitCode
    if ($null -eq $exitCode) { throw 'Missing guest child exit code' }
    $result.acceptance_exit=$exitCode
    [System.IO.File]::WriteAllText("$work\acceptance-stdout.log",$stdoutTask.Result)
    [System.IO.File]::WriteAllText("$work\acceptance-stderr.log",$stderrTask.Result)
    $final=Get-Content -LiteralPath "$work\acceptance\final_result.json" -Raw | ConvertFrom-Json
    if ($accept.ExitCode -ne 0 -or $final.status -ne 'PASS') { throw 'Native guest acceptance did not pass' }
    $result.status='PASS';$result.stage='complete';$result.source_commit=$final.source_commit
} catch {
    $result.error=$_.Exception.Message
} finally {
    New-Item -ItemType Directory -Force -Path "$output\acceptance\logs" | Out-Null
    if (Test-Path -LiteralPath "$work\acceptance") {
        Get-ChildItem -LiteralPath "$work\acceptance" -File | Where-Object { $_.Extension -eq '.json' -or $_.Name -eq 'guard-events.jsonl' } | Copy-Item -Destination "$output\acceptance"
        if (Test-Path -LiteralPath "$work\acceptance\logs") { Get-ChildItem -LiteralPath "$work\acceptance\logs" -File | Copy-Item -Destination "$output\acceptance\logs" }
    }
    foreach ($name in @('acceptance-stdout.log','acceptance-stderr.log','python-install.log')) { if (Test-Path -LiteralPath "$work\$name") { Copy-Item -LiteralPath "$work\$name" -Destination "$output\$name" } }
    $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$output\result.json" -Encoding utf8
    Set-Content -LiteralPath "$output\done.txt" -Value $result.status -Encoding ascii
    & C:\Windows\System32\shutdown.exe /s /t 0
}
