param(
    [ValidateSet('Gui','Status','Setup','Start','Stop','Restart','Doctor','WorkbenchUri','SecurityStatus','SecurityUpdate')]
    [string]$Action = 'Gui',
    [switch]$Headless,
    [string]$PythonPath,
    [switch]$ConfirmStaleOwnership,
    [switch]$ConfirmSecurityNetwork,
    [switch]$ConfirmSecurityCompatibility
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:BundleRoot = Split-Path -Parent $PSScriptRoot
$script:MarketCmd = Join-Path $script:BundleRoot 'tw-market.cmd'
$script:SecurityMasterCmd = Join-Path $script:BundleRoot 'tw-market-security-master.cmd'
$script:BootstrapPs1 = Join-Path $script:BundleRoot 'bootstrap\bootstrap.ps1'
$script:RuntimePython = Join-Path $script:BundleRoot 'runtime\venv\Scripts\python.exe'
$script:RuntimeMarker = Join-Path $script:BundleRoot 'runtime\runtime-marker.json'
$script:ProductVersionPath = Join-Path $script:BundleRoot 'app\VERSION'
$script:SelectedPython = $PythonPath
$script:LastTechnicalDetails = ''
$script:LastSnapshotDetails = ''
$script:CurrentSnapshot = $null
$script:SecurityRestartRequired = $false
$script:SecurityLastOperation = ''
$script:SecurityLastReason = ''
$script:SecurityCompatibilityRetryAvailable = $false
$script:SecurityCompatibilityDiagnostic = $null

function New-LauncherResult {
    param([string]$Status, [string]$ReasonCode = '', [object]$Data = $null)
    $result = [ordered]@{ status = $Status }
    if ($ReasonCode) { $result.reason_code = $ReasonCode }
    if ($null -ne $Data) { $result.data = $Data }
    [pscustomobject]$result
}

function ConvertFrom-LastJsonPayload {
    param([string]$Raw)
    if (-not $Raw) { return $null }
    try { return ($Raw.Trim() | ConvertFrom-Json) } catch {}
    $lines = @($Raw -split "`r?`n")
    for ($i = $lines.Count - 1; $i -ge 0; $i--) {
        $trimmed = $lines[$i].TrimStart()
        if (-not ($trimmed.StartsWith('{') -or $trimmed.StartsWith('['))) { continue }
        $candidate = ($lines[$i..($lines.Count - 1)] -join [Environment]::NewLine).Trim()
        try { return ($candidate | ConvertFrom-Json) } catch {}
    }
    return $null
}

function Invoke-ExternalCommand {
    param([string]$FilePath, [string[]]$Arguments)
    try {
        $output = & $FilePath @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        $text = (@($output) | ForEach-Object { [string]$_ }) -join [Environment]::NewLine
        return [pscustomobject]@{ exit_code = $exitCode; output = $text; launch_error = $null }
    } catch {
        return [pscustomobject]@{ exit_code = -1; output = ''; launch_error = $_.Exception.Message }
    }
}

function Get-ProductVersion {
    if (-not (Test-Path -LiteralPath $script:ProductVersionPath -PathType Leaf)) { return 'Unknown' }
    try {
        $value = (Get-Content -LiteralPath $script:ProductVersionPath -Raw).Trim()
        if ($value) { return $value }
    } catch {}
    return 'Unknown'
}

function Get-RuntimePresence {
    $pythonExists = Test-Path -LiteralPath $script:RuntimePython -PathType Leaf
    $markerExists = Test-Path -LiteralPath $script:RuntimeMarker -PathType Leaf
    if (-not $pythonExists -and -not $markerExists) { return 'MISSING' }
    if ($pythonExists -and $markerExists) { return 'PRESENT' }
    return 'INCOMPLETE'
}

function Test-PythonExecutable {
    param([string]$Executable, [string[]]$PrefixArguments = @(), [string]$Source = 'candidate')
    if (-not $Executable) { return $null }
    $probe = "import json,os,platform,struct,sys;print(json.dumps({'executable':sys.executable,'implementation':platform.python_implementation(),'version':[sys.version_info.major,sys.version_info.minor],'bits':struct.calcsize('P')*8,'machine':platform.machine().lower(),'os_name':os.name}))"
    $run = Invoke-ExternalCommand -FilePath $Executable -Arguments @($PrefixArguments + @('-c', $probe))
    if ($run.exit_code -ne 0 -or -not $run.output) { return $null }
    try { $data = $run.output.Trim() | ConvertFrom-Json } catch { return $null }
    $valid = $data.implementation -eq 'CPython' -and
        [int]$data.version[0] -eq 3 -and [int]$data.version[1] -eq 13 -and
        [int]$data.bits -eq 64 -and $data.machine -in @('amd64','x86_64') -and
        $data.os_name -eq 'nt'
    if (-not $valid) { return $null }
    $resolved = [string]$data.executable
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) { return $null }
    return [pscustomobject]@{ executable = $resolved; source = $Source }
}

function Find-Python313 {
    if ($script:SelectedPython) {
        $explicit = Test-PythonExecutable -Executable $script:SelectedPython -Source 'explicit'
        if ($explicit) { return $explicit }
    }
    $py = Get-Command 'py.exe' -ErrorAction SilentlyContinue
    if ($py) {
        $candidate = Test-PythonExecutable -Executable $py.Source -PrefixArguments @('-3.13') -Source 'py-launcher'
        if ($candidate) { return $candidate }
    }
    $python = Get-Command 'python.exe' -ErrorAction SilentlyContinue
    if ($python) {
        $candidate = Test-PythonExecutable -Executable $python.Source -Source 'path'
        if ($candidate) { return $candidate }
    }
    return $null
}

function Invoke-Lifecycle {
    param([ValidateSet('init','start','status','stop','doctor')][string]$Command)
    if (-not (Test-Path -LiteralPath $script:MarketCmd -PathType Leaf)) {
        return [pscustomobject]@{ exit_code = -1; payload = $null; raw = ''; error = 'MARKET_LAUNCHER_NOT_FOUND' }
    }
    $run = Invoke-ExternalCommand -FilePath $script:MarketCmd -Arguments @($Command, '--json')
    if ($run.launch_error) {
        return [pscustomobject]@{ exit_code = -1; payload = $null; raw = ''; error = $run.launch_error }
    }
    $raw = $run.output.Trim()
    try { $payload = $raw | ConvertFrom-Json } catch { $payload = $null }
    return [pscustomobject]@{ exit_code = $run.exit_code; payload = $payload; raw = $raw; error = $null }
}

function Invoke-SecurityMasterCommand {
    param(
        [ValidateSet('status','update')][string]$Command,
        [ValidateSet('strict','compatibility')][string]$SslPolicy = 'strict'
    )
    if (-not (Test-Path -LiteralPath $script:SecurityMasterCmd -PathType Leaf)) {
        return [pscustomobject]@{ exit_code = -1; payload = $null; raw = ''; error = 'SECURITY_MASTER_LAUNCHER_NOT_FOUND' }
    }
    $arguments = @($Command)
    if ($Command -eq 'update') {
        $arguments += '--live'
        if ($SslPolicy -eq 'compatibility') { $arguments += @('--ssl-policy','compatibility') }
    }
    $run = Invoke-ExternalCommand -FilePath $script:SecurityMasterCmd -Arguments $arguments
    if ($run.launch_error) {
        return [pscustomobject]@{ exit_code = -1; payload = $null; raw = ''; error = $run.launch_error }
    }
    $raw = $run.output.Trim()
    $payload = ConvertFrom-LastJsonPayload -Raw $raw
    return [pscustomobject]@{ exit_code = $run.exit_code; payload = $payload; raw = $raw; error = $null }
}

function Get-SecurityMasterStrictCompatibilityEvidence {
    param([object]$RuntimeSnapshot, [datetime]$NotBeforeUtc)
    try {
        if ($null -eq $RuntimeSnapshot -or -not ($RuntimeSnapshot.PSObject.Properties.Name -contains 'data')) { return $null }
        $payload = $RuntimeSnapshot.data
        if ($null -eq $payload -or -not ($payload.PSObject.Properties.Name -contains 'installation') -or $null -eq $payload.installation) { return $null }
        if (-not ($payload.installation.PSObject.Properties.Name -contains 'temp_root') -or -not $payload.installation.temp_root) { return $null }
        $securityTemp = Join-Path ([string]$payload.installation.temp_root) 'security-master'
        if (-not (Test-Path -LiteralPath $securityTemp -PathType Container)) { return $null }
        $cutoff = $NotBeforeUtc.AddSeconds(-2)
        $manifests = @(Get-ChildItem -LiteralPath $securityTemp -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -eq 'source_evidence_manifest.json' -and ($_.LastWriteTimeUtc -ge $cutoff -or $_.CreationTimeUtc -ge $cutoff) } |
            Sort-Object LastWriteTimeUtc -Descending)
        foreach ($manifest in $manifests) {
            try { $evidence = Get-Content -LiteralPath $manifest.FullName -Raw | ConvertFrom-Json } catch { continue }
            if ([string]$evidence.principal_decision -ne 'BLOCKED_BY_OFFICIAL_SOURCE_PROBE_FAILURE') { continue }
            $probes = @($evidence.source_probes)
            if ($probes.Count -lt 1) { continue }
            $strictFailures = @($probes | Where-Object {
                $_.transport_success -eq $false -and [string]$_.transport_reason_code -eq 'PYTHON_X509_STRICT_COMPATIBILITY'
            })
            if ($strictFailures.Count -ne $probes.Count) { continue }
            return [pscustomobject]@{
                reason_code = 'PYTHON_X509_STRICT_COMPATIBILITY'
                source_count = $probes.Count
                diagnostic_path = $manifest.FullName
                tls_verification = 'enabled'
                hostname_verification = 'enabled'
                retry_ssl_policy = 'compatibility'
            }
        }
    } catch {}
    return $null
}

function Get-SecurityMasterSnapshot {
    if ((Get-RuntimePresence) -ne 'PRESENT') {
        return New-LauncherResult -Status 'UNAVAILABLE' -ReasonCode 'PACKAGE_RUNTIME_NOT_READY'
    }
    $run = Invoke-SecurityMasterCommand -Command 'status'
    if ($null -eq $run.payload) {
        return New-LauncherResult -Status 'UNAVAILABLE' -ReasonCode 'SECURITY_MASTER_STATUS_FAILED'
    }
    $state = [string]$run.payload.status
    if ($state -in @('NOT_INITIALIZED','ACTIVE')) {
        return New-LauncherResult -Status $state -Data $run.payload
    }
    $reason = 'SECURITY_MASTER_STATE_UNREADABLE'
    if ($run.payload.PSObject.Properties.Name -contains 'reason_code' -and $run.payload.reason_code) { $reason = [string]$run.payload.reason_code }
    return New-LauncherResult -Status 'UNAVAILABLE' -ReasonCode $reason -Data $run.payload
}

function Invoke-SecurityMasterUpdateAction {
    param(
        [switch]$Confirmed,
        [ValidateSet('strict','compatibility')][string]$SslPolicy = 'strict',
        [switch]$CompatibilityConfirmed
    )
    $runtime = Get-LauncherSnapshot
    if ($runtime.status -in @('SETUP_REQUIRED','INSTALLATION_INCOMPLETE','STATUS_ERROR')) {
        return New-LauncherResult -Status 'ACTION_BLOCKED' -ReasonCode 'SECURITY_MASTER_REQUIRES_READY_INSTALLATION'
    }
    if ($runtime.status -notin @('STOPPED','RUNNING_READY','RUNNING_UNHEALTHY')) {
        return New-LauncherResult -Status 'ACTION_BLOCKED' -ReasonCode ('SECURITY_MASTER_REQUIRES_STABLE_RUNTIME_STATE_' + $runtime.status)
    }
    $before = Get-SecurityMasterSnapshot
    if ($before.status -notin @('NOT_INITIALIZED','ACTIVE')) {
        return New-LauncherResult -Status 'ACTION_BLOCKED' -ReasonCode ('SECURITY_MASTER_UPDATE_NOT_ALLOWED_FROM_' + $before.status)
    }
    if (-not $Confirmed) {
        return New-LauncherResult -Status 'CONFIRMATION_REQUIRED' -ReasonCode 'SECURITY_MASTER_EXTERNAL_ACQUISITION'
    }
    if ($SslPolicy -eq 'compatibility' -and -not $CompatibilityConfirmed) {
        return New-LauncherResult -Status 'CONFIRMATION_REQUIRED' -ReasonCode 'SECURITY_MASTER_TLS_COMPATIBILITY_RETRY'
    }
    $mode = if ($before.status -eq 'NOT_INITIALIZED') { 'INSTALL' } else { 'UPDATE' }
    $attemptStartedUtc = [datetime]::UtcNow
    $run = Invoke-SecurityMasterCommand -Command 'update' -SslPolicy $SslPolicy
    $script:LastTechnicalDetails = $run.raw
    if ($null -eq $run.payload -or $run.exit_code -ne 0 -or [string]$run.payload.status -ne 'ACTIVE') {
        $reason = 'SECURITY_MASTER_UPDATE_FAILED'
        if ($run.payload -and ($run.payload.PSObject.Properties.Name -contains 'reason_code') -and $run.payload.reason_code) { $reason = [string]$run.payload.reason_code }
        if ($SslPolicy -eq 'strict' -and $reason -eq 'official_acquisition_or_qualification_failed') {
            $compatibility = Get-SecurityMasterStrictCompatibilityEvidence -RuntimeSnapshot $runtime -NotBeforeUtc $attemptStartedUtc
            if ($null -ne $compatibility) {
                $script:SecurityCompatibilityRetryAvailable = $true
                $script:SecurityCompatibilityDiagnostic = $compatibility
                $script:SecurityLastOperation = 'COMPATIBILITY_RETRY_AVAILABLE'
                $script:SecurityLastReason = 'PYTHON_X509_STRICT_COMPATIBILITY'
                return New-LauncherResult -Status 'SECURITY_MASTER_TLS_COMPATIBILITY_RETRY_AVAILABLE' -ReasonCode 'PYTHON_X509_STRICT_COMPATIBILITY' -Data ([pscustomobject]@{
                    mode = $mode
                    runtime_state = $runtime.status
                    compatibility = $compatibility
                    security_master = $run.payload
                })
            }
        }
        $script:SecurityCompatibilityRetryAvailable = $false
        $script:SecurityCompatibilityDiagnostic = $null
        $script:SecurityLastOperation = 'FAILED'
        $script:SecurityLastReason = $reason
        return New-LauncherResult -Status 'SECURITY_MASTER_UPDATE_FAILED' -ReasonCode $reason -Data $run.payload
    }
    $restartRequired = $false
    if ($run.payload.PSObject.Properties.Name -contains 'restart_required') { $restartRequired = [bool]$run.payload.restart_required }
    $script:SecurityRestartRequired = $restartRequired
    $script:SecurityCompatibilityRetryAvailable = $false
    $script:SecurityCompatibilityDiagnostic = $null
    $script:SecurityLastOperation = $mode + '_COMPLETE'
    $script:SecurityLastReason = ''
    return New-LauncherResult -Status 'SECURITY_MASTER_UPDATE_COMPLETE' -Data ([pscustomobject]@{
        mode = $mode
        ssl_policy = $SslPolicy
        restart_required = $restartRequired
        runtime_state = $runtime.status
        security_master = $run.payload
    })
}
function Get-WorkbenchUri {
    param([object]$Payload)
    if ($null -eq $Payload -or $null -eq $Payload.service -or -not $Payload.service.alive) { return $null }
    $hostName = [string]$Payload.service.host
    $port = [int]$Payload.service.port
    if ($hostName -notin @('127.0.0.1','localhost','::1') -or $port -lt 1 -or $port -gt 65535) { return $null }
    $authority = $hostName
    if ($hostName -eq '::1') { $authority = '[::1]' }
    return "http://${authority}:$port/workbench/"
}

function Get-LauncherSnapshot {
    param([switch]$PreserveTechnicalDetails)
    $presence = Get-RuntimePresence
    if ($presence -eq 'MISSING') {
        return New-LauncherResult -Status 'SETUP_REQUIRED' -ReasonCode 'PACKAGE_RUNTIME_NOT_READY'
    }
    if ($presence -eq 'INCOMPLETE') {
        return New-LauncherResult -Status 'SETUP_REQUIRED' -ReasonCode 'PACKAGE_RUNTIME_NEEDS_ATTENTION'
    }
    $statusRun = Invoke-Lifecycle -Command 'status'
    if ($null -eq $statusRun.payload) {
        if (-not $PreserveTechnicalDetails) { $script:LastTechnicalDetails = $statusRun.raw }
        return New-LauncherResult -Status 'STATUS_ERROR' -ReasonCode 'STATUS_COMMAND_FAILED'
    }
    $payload = $statusRun.payload
    if (-not $PreserveTechnicalDetails) { $script:LastTechnicalDetails = $statusRun.raw }
    if (-not ($payload.PSObject.Properties.Name -contains 'installation') -or $null -eq $payload.installation -or
        -not ($payload.installation.PSObject.Properties.Name -contains 'installation_status')) {
        $reason = 'STATUS_PAYLOAD_INCOMPLETE'
        if ($payload.PSObject.Properties.Name -contains 'reason_code' -and $payload.reason_code) { $reason = [string]$payload.reason_code }
        return New-LauncherResult -Status 'STATUS_ERROR' -ReasonCode $reason -Data $payload
    }
    $installationStatus = [string]$payload.installation.installation_status
    if ($installationStatus -eq 'INSTALLATION_NOT_INITIALIZED') {
        return New-LauncherResult -Status 'SETUP_REQUIRED' -ReasonCode 'INSTALLATION_NOT_INITIALIZED' -Data $payload
    }
    if ($installationStatus -ne 'READY') {
        return New-LauncherResult -Status 'INSTALLATION_INCOMPLETE' -ReasonCode $installationStatus -Data $payload
    }
    if (-not ($payload.PSObject.Properties.Name -contains 'service') -or $null -eq $payload.service -or
        -not ($payload.service.PSObject.Properties.Name -contains 'process') -or
        -not ($payload.service.PSObject.Properties.Name -contains 'alive')) {
        return New-LauncherResult -Status 'STATUS_ERROR' -ReasonCode 'SERVICE_STATUS_PAYLOAD_INCOMPLETE' -Data $payload
    }
    $processState = [string]$payload.service.process
    $alive = [bool]$payload.service.alive
    switch ($processState) {
        'NOT_RUNNING' { $state = 'STOPPED' }
        'START_IN_PROGRESS' { $state = 'STARTING' }
        'PORT_OCCUPIED_NOT_OWNED' { $state = 'PORT_CONFLICT' }
        'STALE_PROCESS_OWNERSHIP' { $state = 'STALE_OWNERSHIP' }
        'RUNNING' {
            if ($alive) { $state = 'RUNNING_READY' } else { $state = 'RUNNING_UNHEALTHY' }
        }
        default { $state = 'STATUS_ERROR' }
    }
    $reason = ''
    if ($state -eq 'STATUS_ERROR') { $reason = 'UNRECOGNIZED_LIFECYCLE_STATE' }
    return New-LauncherResult -Status $state -ReasonCode $reason -Data $payload
}

function Invoke-Setup {
    $presence = Get-RuntimePresence
    if ($presence -eq 'INCOMPLETE') {
        return New-LauncherResult -Status 'SETUP_BLOCKED' -ReasonCode 'PACKAGE_RUNTIME_NEEDS_ATTENTION'
    }
    if ($presence -eq 'MISSING') {
        $python = Find-Python313
        if (-not $python) {
            return New-LauncherResult -Status 'PREREQUISITE_BLOCKED' -ReasonCode 'CPYTHON_3_13_X64_REQUIRED'
        }
        if (-not (Test-Path -LiteralPath $script:BootstrapPs1 -PathType Leaf)) {
            return New-LauncherResult -Status 'SETUP_BLOCKED' -ReasonCode 'BOOTSTRAP_NOT_FOUND'
        }
        $bootstrap = Invoke-ExternalCommand -FilePath 'powershell.exe' -Arguments @(
            '-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File',$script:BootstrapPs1,
            '-Python',$python.executable,'-BundleRoot',$script:BundleRoot
        )
        $script:LastTechnicalDetails = $bootstrap.output
        if ($bootstrap.exit_code -ne 0) {
            return New-LauncherResult -Status 'SETUP_BLOCKED' -ReasonCode 'BOOTSTRAP_FAILED' -Data $bootstrap.output
        }
    }
    $statusRun = Invoke-Lifecycle -Command 'status'
    if ($null -eq $statusRun.payload) {
        $script:LastTechnicalDetails = $statusRun.raw
        return New-LauncherResult -Status 'SETUP_BLOCKED' -ReasonCode 'RUNTIME_VERIFICATION_FAILED'
    }
    if (-not ($statusRun.payload.PSObject.Properties.Name -contains 'installation') -or
        $null -eq $statusRun.payload.installation -or
        -not ($statusRun.payload.installation.PSObject.Properties.Name -contains 'installation_status')) {
        return New-LauncherResult -Status 'SETUP_BLOCKED' -ReasonCode 'RUNTIME_VERIFICATION_INCOMPLETE' -Data $statusRun.payload
    }
    $installationStatus = [string]$statusRun.payload.installation.installation_status
    if ($installationStatus -eq 'INSTALLATION_NOT_INITIALIZED') {
        $initRun = Invoke-Lifecycle -Command 'init'
        $script:LastTechnicalDetails = $initRun.raw
        if ($null -eq $initRun.payload -or [string]$initRun.payload.status -ne 'INSTALLATION_READY') {
            $reason = 'INSTALLATION_INIT_FAILED'
            if ($initRun.payload -and $initRun.payload.reason_code) { $reason = [string]$initRun.payload.reason_code }
            return New-LauncherResult -Status 'SETUP_BLOCKED' -ReasonCode $reason -Data $initRun.payload
        }
    } elseif ($installationStatus -ne 'READY') {
        return New-LauncherResult -Status 'SETUP_BLOCKED' -ReasonCode $installationStatus -Data $statusRun.payload
    }
    $final = Get-LauncherSnapshot
    $script:CurrentSnapshot = $final
    if ($final.status -eq 'STOPPED') {
        return New-LauncherResult -Status 'SETUP_COMPLETE' -Data $final.data
    }
    $reason = 'SETUP_FINAL_STATE_' + [string]$final.status
    if ($final.PSObject.Properties.Name -contains 'reason_code' -and $final.reason_code) {
        $reason = [string]$final.reason_code
    }
    return New-LauncherResult -Status 'SETUP_BLOCKED' -ReasonCode $reason -Data $final
}

function Invoke-StartAction {
    $before = Get-LauncherSnapshot
    $script:CurrentSnapshot = $before
    if ($before.status -eq 'STALE_OWNERSHIP' -and -not $ConfirmStaleOwnership) {
        return New-LauncherResult -Status 'CONFIRMATION_REQUIRED' -ReasonCode 'STALE_PROCESS_OWNERSHIP'
    }
    if ($before.status -notin @('STOPPED','STALE_OWNERSHIP')) {
        return New-LauncherResult -Status 'ACTION_BLOCKED' -ReasonCode ('START_NOT_ALLOWED_FROM_' + $before.status)
    }
    $run = Invoke-Lifecycle -Command 'start'
    $script:LastTechnicalDetails = $run.raw
    $after = Get-LauncherSnapshot -PreserveTechnicalDetails
    $script:CurrentSnapshot = $after
    if ($null -eq $run.payload) { return New-LauncherResult -Status 'START_FAILED' -ReasonCode 'START_COMMAND_FAILED' }
    if ($after.status -eq 'RUNNING_READY') {
        $script:SecurityRestartRequired = $false
        if ($script:SecurityLastOperation -in @('INSTALL_COMPLETE','UPDATE_COMPLETE')) { $script:SecurityLastOperation = '' }
        return New-LauncherResult -Status 'START_COMPLETE' -Data $after.data
    }
    $reason = [string]$run.payload.status
    if ($run.payload.reason_code) { $reason = [string]$run.payload.reason_code }
    return New-LauncherResult -Status 'START_INCOMPLETE' -ReasonCode $reason -Data $after
}

function Invoke-StopAction {
    $before = Get-LauncherSnapshot
    $script:CurrentSnapshot = $before
    if ($before.status -notin @('RUNNING_READY','RUNNING_UNHEALTHY')) {
        return New-LauncherResult -Status 'ACTION_BLOCKED' -ReasonCode ('STOP_NOT_ALLOWED_FROM_' + $before.status)
    }
    $run = Invoke-Lifecycle -Command 'stop'
    $script:LastTechnicalDetails = $run.raw
    $after = Get-LauncherSnapshot -PreserveTechnicalDetails
    $script:CurrentSnapshot = $after
    if ($null -eq $run.payload) { return New-LauncherResult -Status 'STOP_FAILED' -ReasonCode 'STOP_COMMAND_FAILED' }
    if ($after.status -eq 'STOPPED') { return New-LauncherResult -Status 'STOP_COMPLETE' -Data $after.data }
    $reason = [string]$run.payload.status
    if ($run.payload.reason_code) { $reason = [string]$run.payload.reason_code }
    return New-LauncherResult -Status 'STOP_INCOMPLETE' -ReasonCode $reason -Data $after
}

function Invoke-RestartAction {
    $before = Get-LauncherSnapshot
    if ($before.status -notin @('RUNNING_READY','RUNNING_UNHEALTHY')) {
        return New-LauncherResult -Status 'ACTION_BLOCKED' -ReasonCode ('RESTART_NOT_ALLOWED_FROM_' + $before.status)
    }
    $stopped = Invoke-StopAction
    if ($stopped.status -ne 'STOP_COMPLETE' -or $script:CurrentSnapshot.status -ne 'STOPPED') {
        return New-LauncherResult -Status 'RESTART_FAILED' -ReasonCode 'RESTART_STOP_FAILED' -Data $stopped
    }
    $started = Invoke-StartAction
    if ($started.status -eq 'START_COMPLETE' -and $script:CurrentSnapshot.status -eq 'RUNNING_READY') {
        $script:SecurityRestartRequired = $false
        $script:SecurityLastOperation = ''
        $script:SecurityLastReason = ''
        return New-LauncherResult -Status 'RESTART_COMPLETE' -Data $started.data
    }
    return New-LauncherResult -Status 'RESTART_FAILED' -ReasonCode 'RESTART_START_FAILED' -Data $started
}

function Invoke-DoctorAction {
    if ((Get-RuntimePresence) -ne 'PRESENT') {
        return New-LauncherResult -Status 'DOCTOR_BLOCKED' -ReasonCode 'PACKAGE_RUNTIME_NOT_READY'
    }
    $run = Invoke-Lifecycle -Command 'doctor'
    $script:LastTechnicalDetails = $run.raw
    if ($null -eq $run.payload) { return New-LauncherResult -Status 'DOCTOR_FAILED' -ReasonCode 'DOCTOR_COMMAND_FAILED' }
    if ($run.exit_code -ne 0 -or [string]$run.payload.status -eq 'FAIL') {
        $reason = 'DOCTOR_COMMAND_FAILED'
        if ($run.payload.PSObject.Properties.Name -contains 'reason_code' -and $run.payload.reason_code) { $reason = [string]$run.payload.reason_code }
        return New-LauncherResult -Status 'DOCTOR_FAILED' -ReasonCode $reason -Data $run.payload
    }
    return New-LauncherResult -Status 'DOCTOR_COMPLETE' -Data $run.payload
}
function Invoke-WorkbenchUriAction {
    $snapshot = Get-LauncherSnapshot
    if ($snapshot.status -ne 'RUNNING_READY') {
        return New-LauncherResult -Status 'ACTION_BLOCKED' -ReasonCode ('WORKBENCH_NOT_AVAILABLE_FROM_' + $snapshot.status)
    }
    $uri = Get-WorkbenchUri -Payload $snapshot.data
    if (-not $uri) { return New-LauncherResult -Status 'ACTION_BLOCKED' -ReasonCode 'WORKBENCH_URI_INVALID' }
    return New-LauncherResult -Status 'WORKBENCH_READY' -Data ([pscustomobject]@{ uri = $uri })
}

function Invoke-RequestedAction {
    param([string]$RequestedAction)
    switch ($RequestedAction) {
        'Status' { return Get-LauncherSnapshot }
        'Setup' { return Invoke-Setup }
        'Start' { return Invoke-StartAction }
        'Stop' { return Invoke-StopAction }
        'Restart' { return Invoke-RestartAction }
        'Doctor' { return Invoke-DoctorAction }
        'WorkbenchUri' { return Invoke-WorkbenchUriAction }
        'SecurityStatus' { return Get-SecurityMasterSnapshot }
        'SecurityUpdate' {
            $policy = if ($ConfirmSecurityCompatibility) { 'compatibility' } else { 'strict' }
            return Invoke-SecurityMasterUpdateAction -Confirmed:$ConfirmSecurityNetwork -SslPolicy $policy -CompatibilityConfirmed:$ConfirmSecurityCompatibility
        }
        default { return New-LauncherResult -Status 'ACTION_BLOCKED' -ReasonCode 'UNSUPPORTED_HEADLESS_ACTION' }
    }
}

function Write-HeadlessResult {
    param([object]$Result)
    $json = $Result | ConvertTo-Json -Depth 12 -Compress
    [Console]::Out.WriteLine($json)
    if ($Result.status -in @('STATUS_ERROR','SETUP_BLOCKED','PREREQUISITE_BLOCKED','START_FAILED','START_INCOMPLETE','STOP_FAILED','STOP_INCOMPLETE','RESTART_FAILED','SECURITY_MASTER_UPDATE_FAILED','SECURITY_MASTER_TLS_COMPATIBILITY_RETRY_AVAILABLE','DOCTOR_FAILED','DOCTOR_BLOCKED','ACTION_BLOCKED','CONFIRMATION_REQUIRED')) { return 1 }
    return 0
}
function Show-TechnicalDetails {
    param([string]$Text)
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.Form
    $dialog.Text = 'TW-Market Technical Details'
    $dialog.Width = 760; $dialog.Height = 520; $dialog.StartPosition = 'CenterParent'
    $box = New-Object System.Windows.Forms.TextBox
    $box.Multiline = $true; $box.ReadOnly = $true; $box.ScrollBars = 'Both'
    $box.WordWrap = $false; $box.Dock = 'Fill'; $box.Text = $Text
    $dialog.Controls.Add($box)
    [void]$dialog.ShowDialog()
}

function Show-LauncherGui {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    [System.Windows.Forms.Application]::EnableVisualStyles()

    $form = New-Object System.Windows.Forms.Form
    $form.Text = 'TW-Market'
    $form.Width = 720; $form.Height = 620; $form.StartPosition = 'CenterScreen'
    $form.FormBorderStyle = 'FixedDialog'; $form.MaximizeBox = $false
    $form.BackColor = [System.Drawing.Color]::White

    $title = New-Object System.Windows.Forms.Label
    $title.Text = 'TW-Market'; $title.AutoSize = $true
    $title.Font = New-Object System.Drawing.Font('Segoe UI',18,[System.Drawing.FontStyle]::Bold)
    $title.Location = New-Object System.Drawing.Point(24,18); $form.Controls.Add($title)

    $subtitle = New-Object System.Windows.Forms.Label
    $subtitle.Text = 'Taiwan Market Intelligence'; $subtitle.AutoSize = $true
    $subtitle.ForeColor = [System.Drawing.Color]::DimGray
    $subtitle.Location = New-Object System.Drawing.Point(27,52); $form.Controls.Add($subtitle)

    $versionLabel = New-Object System.Windows.Forms.Label
    $productVersion = Get-ProductVersion
    $versionLabel.Text = if ($productVersion -eq 'Unknown') { 'Version unknown' } else { 'v' + $productVersion }
    $versionLabel.AutoSize = $true; $versionLabel.TextAlign = 'MiddleRight'
    $versionLabel.Location = New-Object System.Drawing.Point(610,26); $form.Controls.Add($versionLabel)

    $setupPanel = New-Object System.Windows.Forms.Panel
    $setupPanel.Location = New-Object System.Drawing.Point(20,82)
    $setupPanel.Size = New-Object System.Drawing.Size(665,465)
    $form.Controls.Add($setupPanel)

    $setupHeading = New-Object System.Windows.Forms.Label
    $setupHeading.Text = 'First-time setup'; $setupHeading.AutoSize = $true
    $setupHeading.Font = New-Object System.Drawing.Font('Segoe UI',12,[System.Drawing.FontStyle]::Bold)
    $setupHeading.Location = New-Object System.Drawing.Point(8,8); $setupPanel.Controls.Add($setupHeading)

    $setupRows = @('Package Runtime','Python 3.13 x64','Local Installation')
    $setupValues = @{}
    $setupY = 55
    foreach ($name in $setupRows) {
        $nameLabel = New-Object System.Windows.Forms.Label
        $nameLabel.Text = $name; $nameLabel.Width = 180
        $nameLabel.Location = New-Object System.Drawing.Point(24,$setupY)
        $valueLabel = New-Object System.Windows.Forms.Label
        $valueLabel.Text = 'Checking...'; $valueLabel.Width = 360
        $valueLabel.Font = New-Object System.Drawing.Font('Segoe UI',9,[System.Drawing.FontStyle]::Bold)
        $valueLabel.Location = New-Object System.Drawing.Point(215,$setupY)
        $setupPanel.Controls.Add($nameLabel); $setupPanel.Controls.Add($valueLabel)
        $setupValues[$name] = $valueLabel; $setupY += 42
    }

    $setupMessage = New-Object System.Windows.Forms.Label
    $setupMessage.Width = 600; $setupMessage.Height = 62
    $setupMessage.Location = New-Object System.Drawing.Point(24,195)
    $setupPanel.Controls.Add($setupMessage)

    $setupButton = New-Object System.Windows.Forms.Button
    $setupButton.Text = 'Set Up TW-Market'; $setupButton.Width = 190; $setupButton.Height = 38
    $setupButton.Location = New-Object System.Drawing.Point(24,275); $setupPanel.Controls.Add($setupButton)

    $locateButton = New-Object System.Windows.Forms.Button
    $locateButton.Text = 'Locate Python 3.13...'; $locateButton.Width = 170; $locateButton.Height = 38
    $locateButton.Location = New-Object System.Drawing.Point(226,275); $setupPanel.Controls.Add($locateButton)

    $setupDetailsButton = New-Object System.Windows.Forms.Button
    $setupDetailsButton.Text = 'Technical Details'; $setupDetailsButton.Width = 150; $setupDetailsButton.Height = 34
    $setupDetailsButton.Location = New-Object System.Drawing.Point(24,335); $setupPanel.Controls.Add($setupDetailsButton)

    $helpButton = New-Object System.Windows.Forms.Button
    $helpButton.Text = 'Installation Help'; $helpButton.Width = 150; $helpButton.Height = 34
    $helpButton.Location = New-Object System.Drawing.Point(186,335); $setupPanel.Controls.Add($helpButton)

    $setupDoctorButton = New-Object System.Windows.Forms.Button
    $setupDoctorButton.Text = 'Diagnose'; $setupDoctorButton.Width = 110; $setupDoctorButton.Height = 34
    $setupDoctorButton.Location = New-Object System.Drawing.Point(348,335); $setupPanel.Controls.Add($setupDoctorButton)

    $dailyPanel = New-Object System.Windows.Forms.Panel
    $dailyPanel.Location = New-Object System.Drawing.Point(20,82)
    $dailyPanel.Size = New-Object System.Drawing.Size(665,475)
    $dailyPanel.Visible = $false; $form.Controls.Add($dailyPanel)

    $statusHeading = New-Object System.Windows.Forms.Label
    $statusHeading.Text = 'System Status'; $statusHeading.AutoSize = $true
    $statusHeading.Font = New-Object System.Drawing.Font('Segoe UI',11,[System.Drawing.FontStyle]::Bold)
    $statusHeading.Location = New-Object System.Drawing.Point(8,4); $dailyPanel.Controls.Add($statusHeading)

    function New-LauncherCard {
        param([string]$Name,[int]$X,[int]$Y)
        $panel = New-Object System.Windows.Forms.Panel
        $panel.BorderStyle = 'FixedSingle'; $panel.BackColor = [System.Drawing.Color]::WhiteSmoke
        $panel.Location = New-Object System.Drawing.Point($X,$Y); $panel.Size = New-Object System.Drawing.Size(300,105)
        $nameLabel = New-Object System.Windows.Forms.Label
        $nameLabel.Text = $Name; $nameLabel.AutoSize = $true
        $nameLabel.Font = New-Object System.Drawing.Font('Segoe UI',10,[System.Drawing.FontStyle]::Bold)
        $nameLabel.Location = New-Object System.Drawing.Point(16,12); [void]$panel.Controls.Add($nameLabel)
        $indicator = New-Object System.Windows.Forms.Label
        $indicator.Text = 'o'; $indicator.AutoSize = $true
        $indicator.Font = New-Object System.Drawing.Font('Segoe UI Symbol',14,[System.Drawing.FontStyle]::Bold)
        $indicator.Location = New-Object System.Drawing.Point(16,46); [void]$panel.Controls.Add($indicator)
        $value = New-Object System.Windows.Forms.Label
        $value.Text = 'Checking...'; $value.Width = 235; $value.Height = 38
        $value.Font = New-Object System.Drawing.Font('Segoe UI',9,[System.Drawing.FontStyle]::Bold)
        $value.Location = New-Object System.Drawing.Point(48,50); [void]$panel.Controls.Add($value)
        [void]$dailyPanel.Controls.Add($panel)
        return [pscustomobject]@{ panel=$panel; indicator=$indicator; value=$value }
    }

    $runtimeCard = New-LauncherCard -Name 'Local Runtime' -X 8 -Y 34
    $workbenchCard = New-LauncherCard -Name 'Workbench' -X 328 -Y 34
    $securityCard = New-LauncherCard -Name 'Security Master' -X 8 -Y 151
    $mcpCard = New-LauncherCard -Name 'Local MCP' -X 328 -Y 151

    $securityCard.value.Width = 145
    $securityActionButton = New-Object System.Windows.Forms.Button
    $securityActionButton.Text = 'Install'; $securityActionButton.Width = 100; $securityActionButton.Height = 30
    $securityActionButton.Location = New-Object System.Drawing.Point(188,48)
    $securityCard.panel.Controls.Add($securityActionButton)

    $openButton = New-Object System.Windows.Forms.Button
    $openButton.Text = 'Open Workbench'; $openButton.Width = 230; $openButton.Height = 42
    $openButton.Font = New-Object System.Drawing.Font('Segoe UI',10,[System.Drawing.FontStyle]::Bold)
    $openButton.Location = New-Object System.Drawing.Point(216,276); $dailyPanel.Controls.Add($openButton)

    $startButton = New-Object System.Windows.Forms.Button
    $startButton.Text = 'Start'; $startButton.Width = 95; $startButton.Height = 34
    $startButton.Location = New-Object System.Drawing.Point(112,337); $dailyPanel.Controls.Add($startButton)
    $stopButton = New-Object System.Windows.Forms.Button
    $stopButton.Text = 'Stop'; $stopButton.Width = 95; $stopButton.Height = 34
    $stopButton.Location = New-Object System.Drawing.Point(217,337); $dailyPanel.Controls.Add($stopButton)
    $refreshButton = New-Object System.Windows.Forms.Button
    $refreshButton.Text = 'Refresh'; $refreshButton.Width = 95; $refreshButton.Height = 34
    $refreshButton.Location = New-Object System.Drawing.Point(322,337); $dailyPanel.Controls.Add($refreshButton)
    $doctorButton = New-Object System.Windows.Forms.Button
    $doctorButton.Text = 'Diagnose'; $doctorButton.Width = 95; $doctorButton.Height = 34
    $doctorButton.Location = New-Object System.Drawing.Point(427,337); $dailyPanel.Controls.Add($doctorButton)

    $detailsButton = New-Object System.Windows.Forms.Button
    $detailsButton.Text = 'Advanced / Technical Details'; $detailsButton.Width = 220; $detailsButton.Height = 32
    $detailsButton.Location = New-Object System.Drawing.Point(8,392); $dailyPanel.Controls.Add($detailsButton)

    $message = New-Object System.Windows.Forms.Label
    $message.Width = 620; $message.Height = 48
    $message.ForeColor = [System.Drawing.Color]::DimGray
    $message.Location = New-Object System.Drawing.Point(8,432); $dailyPanel.Controls.Add($message)

    $script:CurrentSnapshot = $null
    $script:DiscoveredPython = $null

    $setCardState = {
        param($Card,[string]$Text,[ValidateSet('ready','neutral','warning','error','info')][string]$Severity)
        $Card.value.Text = $Text
        switch ($Severity) {
            'ready' { $Card.indicator.Text = '*'; $Card.indicator.ForeColor = [System.Drawing.Color]::ForestGreen }
            'warning' { $Card.indicator.Text = '*'; $Card.indicator.ForeColor = [System.Drawing.Color]::DarkOrange }
            'error' { $Card.indicator.Text = '*'; $Card.indicator.ForeColor = [System.Drawing.Color]::Firebrick }
            'info' { $Card.indicator.Text = '*'; $Card.indicator.ForeColor = [System.Drawing.Color]::SteelBlue }
            default { $Card.indicator.Text = 'o'; $Card.indicator.ForeColor = [System.Drawing.Color]::Gray }
        }
    }

    $render = {
        param([switch]$UseCurrentSnapshot, [switch]$PreserveTechnicalDetails)
        if ($UseCurrentSnapshot -and $null -ne $script:CurrentSnapshot) {
            $snapshot = $script:CurrentSnapshot
        } else {
            $snapshot = Get-LauncherSnapshot -PreserveTechnicalDetails:$PreserveTechnicalDetails
            $script:CurrentSnapshot = $snapshot
        }
        $presence = Get-RuntimePresence
        $payload = $null
        if ($snapshot.PSObject.Properties.Name -contains 'data') { $payload = $snapshot.data }

        if ($snapshot.status -in @('SETUP_REQUIRED','INSTALLATION_INCOMPLETE')) {
            $dailyPanel.Visible = $false; $setupPanel.Visible = $true
            if ($presence -eq 'MISSING') {
                $setupValues['Package Runtime'].Text = 'Not set up'
                $script:DiscoveredPython = Find-Python313
                $setupValues['Python 3.13 x64'].Text = if ($script:DiscoveredPython) { 'Ready' } else { 'Required' }
            } elseif ($presence -eq 'PRESENT') {
                $setupValues['Package Runtime'].Text = 'Ready'
                $setupValues['Python 3.13 x64'].Text = 'Runtime ready'
            } else {
                $setupValues['Package Runtime'].Text = 'Needs attention'
                $setupValues['Python 3.13 x64'].Text = 'Not evaluated'
            }
            $installationText = 'Not initialized'
            if ($payload -and ($payload.PSObject.Properties.Name -contains 'installation') -and $payload.installation) {
                $installationText = [string]$payload.installation.installation_status
            }
            $setupValues['Local Installation'].Text = $installationText
            if ($snapshot.status -eq 'INSTALLATION_INCOMPLETE') {
                $setupMessage.Text = 'The local installation needs attention. Automatic repair is not performed. Use Technical Details or Diagnose.'
            } else {
                $setupMessage.Text = 'Set up the local runtime and installation. Security Master is installed separately after setup.'
            }
            $setupButton.Enabled = ($snapshot.status -eq 'SETUP_REQUIRED' -and $snapshot.reason_code -ne 'PACKAGE_RUNTIME_NEEDS_ATTENTION' -and (($presence -eq 'PRESENT') -or $script:DiscoveredPython))
            $locateButton.Enabled = ($snapshot.status -eq 'SETUP_REQUIRED' -and $presence -eq 'MISSING')
            $setupDoctorButton.Enabled = ($presence -eq 'PRESENT')
            if (-not $PreserveTechnicalDetails) { $script:LastTechnicalDetails = ($snapshot | ConvertTo-Json -Depth 12) }
            return
        }

        $setupPanel.Visible = $false; $dailyPanel.Visible = $true

        switch ($snapshot.status) {
            'STOPPED' { & $setCardState $runtimeCard 'Stopped' 'neutral' }
            'STARTING' { & $setCardState $runtimeCard 'Starting' 'info' }
            'RUNNING_READY' { & $setCardState $runtimeCard 'Running' 'ready' }
            'RUNNING_UNHEALTHY' { & $setCardState $runtimeCard 'Needs attention' 'warning' }
            'PORT_CONFLICT' { & $setCardState $runtimeCard 'Port conflict' 'error' }
            'STALE_OWNERSHIP' { & $setCardState $runtimeCard 'Needs attention' 'warning' }
            default { & $setCardState $runtimeCard 'Needs attention' 'error' }
        }

        $workbenchReady = $snapshot.status -eq 'RUNNING_READY' -and $payload -and (Get-WorkbenchUri -Payload $payload)
        if ($workbenchReady) { & $setCardState $workbenchCard 'Ready' 'ready' }
        else { & $setCardState $workbenchCard 'Unavailable' 'neutral' }

        $identityState = 'UNAVAILABLE'
        $releaseId = ''
        if ($payload -and ($payload.PSObject.Properties.Name -contains 'identity') -and $payload.identity) {
            $identityState = [string]$payload.identity.status
            if ($payload.identity.PSObject.Properties.Name -contains 'release_id' -and $payload.identity.release_id) { $releaseId = [string]$payload.identity.release_id }
        }

        $securityActionButton.Visible = $true
        if ($script:SecurityCompatibilityRetryAvailable) {
            & $setCardState $securityCard 'Compatibility retry available' 'warning'
            $securityActionButton.Text = 'Retry TLS'; $securityActionButton.Enabled = $true
        } elseif ($script:SecurityLastOperation -eq 'FAILED') {
            $failedText = if ($identityState -eq 'ACTIVE') { 'Update failed; current release retained' } else { 'Install failed' }
            & $setCardState $securityCard $failedText 'warning'
            if ($identityState -eq 'ACTIVE') { $securityActionButton.Text = 'Update'; $securityActionButton.Enabled = $true }
            elseif ($identityState -eq 'NOT_INITIALIZED') { $securityActionButton.Text = 'Install'; $securityActionButton.Enabled = $true }
            else { $securityActionButton.Text = 'Diagnose'; $securityActionButton.Enabled = $false }
        } elseif ($script:SecurityRestartRequired) {
            if ($snapshot.status -in @('RUNNING_READY','RUNNING_UNHEALTHY')) {
                & $setCardState $securityCard 'Restart required' 'warning'
                $securityActionButton.Text = 'Restart TW-Market'; $securityActionButton.Enabled = $true
            } else {
                & $setCardState $securityCard 'Ready for next start' 'ready'
                $securityActionButton.Visible = $false
            }
        } elseif ($identityState -eq 'NOT_INITIALIZED') {
            & $setCardState $securityCard 'Not installed' 'neutral'
            $securityActionButton.Text = 'Install'; $securityActionButton.Enabled = $true
        } elseif ($identityState -eq 'ACTIVE') {
            $securityText = if ($releaseId) { 'Ready - ' + $releaseId } else { 'Ready' }
            & $setCardState $securityCard $securityText 'ready'
            $securityActionButton.Text = 'Update'; $securityActionButton.Enabled = $true
        } else {
            & $setCardState $securityCard 'Needs attention' 'error'
            $securityActionButton.Text = 'Diagnose'; $securityActionButton.Enabled = $false
        }
        if ($snapshot.status -notin @('STOPPED','RUNNING_READY','RUNNING_UNHEALTHY')) { $securityActionButton.Enabled = $false }

        $mcpState = 'UNKNOWN'
        if ($payload -and ($payload.PSObject.Properties.Name -contains 'mcp') -and $payload.mcp) { $mcpState = [string]$payload.mcp.status }
        switch ($mcpState) {
            'READY' { & $setCardState $mcpCard 'Ready for MCP clients' 'ready' }
            'SERVICE_UNREACHABLE' { & $setCardState $mcpCard 'Runtime stopped' 'neutral' }
            'MCP_RUNTIME_MISMATCH' { & $setCardState $mcpCard 'Needs attention' 'warning' }
            default { & $setCardState $mcpCard 'Unknown' 'neutral' }
        }

        $startButton.Enabled = $snapshot.status -in @('STOPPED','STALE_OWNERSHIP')
        $stopButton.Enabled = $snapshot.status -in @('RUNNING_READY','RUNNING_UNHEALTHY')
        $openButton.Enabled = [bool]$workbenchReady
        $refreshButton.Enabled = $true
        $doctorButton.Enabled = ($presence -eq 'PRESENT')

        switch ($snapshot.status) {
            'STOPPED' { $message.Text = 'TW-Market is ready. Start the Local Runtime when you want to use the Workbench.' }
            'STARTING' { $message.Text = 'TW-Market is starting. Use Refresh to check again.' }
            'RUNNING_READY' { $message.Text = 'Local Runtime and Workbench are ready.' }
            'RUNNING_UNHEALTHY' { $message.Text = 'The owned TW-Market process is running, but Local Runtime health needs attention.' }
            'PORT_CONFLICT' { $message.Text = 'The configured local port belongs to another process. TW-Market will not control it.' }
            'STALE_OWNERSHIP' { $message.Text = 'Stale TW-Market ownership metadata was detected. Start requires confirmation.' }
            'INSTALLATION_INCOMPLETE' { $message.Text = 'The local TW-Market installation needs attention.' }
            default { $message.Text = 'TW-Market status could not be determined safely. Use Diagnose or Technical Details.' }
        }

        if (-not $PreserveTechnicalDetails) {
            $details = [ordered]@{
                product_version = $productVersion
                launcher = $snapshot
                security_session = [ordered]@{ restart_required = $script:SecurityRestartRequired; last_operation = $script:SecurityLastOperation; last_reason = $script:SecurityLastReason; compatibility_retry_available = $script:SecurityCompatibilityRetryAvailable; compatibility_diagnostic = $script:SecurityCompatibilityDiagnostic }
            }
            $script:LastTechnicalDetails = ($details | ConvertTo-Json -Depth 12)
        }
    }

    $setupButton.Add_Click({
        $form.UseWaitCursor = $true
        try {
            $result = Invoke-Setup
            $script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12)
            if ($result.status -eq 'SETUP_COMPLETE') {
                [void][System.Windows.Forms.MessageBox]::Show('TW-Market local setup is complete. Security Master can now be installed separately.','TW-Market Setup')
            } else {
                [void][System.Windows.Forms.MessageBox]::Show("Setup did not complete: $($result.reason_code)",'TW-Market Setup')
            }
        } finally {
            $form.UseWaitCursor = $false
            & $render -PreserveTechnicalDetails
        }
    })

    $locateButton.Add_Click({
        $picker = New-Object System.Windows.Forms.OpenFileDialog
        $picker.Title = 'Locate CPython 3.13 x64 python.exe'; $picker.Filter = 'python.exe|python.exe|Executable files|*.exe'
        if ($picker.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            $candidate = Test-PythonExecutable -Executable $picker.FileName -Source 'user-selected'
            if ($candidate) {
                $script:SelectedPython = $candidate.executable; $script:DiscoveredPython = $candidate
                [void][System.Windows.Forms.MessageBox]::Show('CPython 3.13 x64 is valid and ready for setup.','TW-Market Setup')
            } else {
                [void][System.Windows.Forms.MessageBox]::Show('The selected executable is not a supported Windows CPython 3.13 x64 runtime.','TW-Market Setup')
            }
            & $render
        }
    })

    $startButton.Add_Click({
        if ($script:CurrentSnapshot.status -eq 'STALE_OWNERSHIP') {
            $answer = [System.Windows.Forms.MessageBox]::Show(
                'Stale TW-Market ownership metadata was detected. Continue with the canonical Start action? Only stale ephemeral ownership metadata may be cleaned by the existing lifecycle.',
                'TW-Market Start',[System.Windows.Forms.MessageBoxButtons]::YesNo,[System.Windows.Forms.MessageBoxIcon]::Warning)
            if ($answer -ne [System.Windows.Forms.DialogResult]::Yes) { return }
            $script:ConfirmStaleOwnership = $true
        }
        $form.UseWaitCursor = $true
        try { $result = Invoke-StartAction; $script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12) }
        finally {
            $form.UseWaitCursor = $false; $script:ConfirmStaleOwnership = $false
            & $render -UseCurrentSnapshot -PreserveTechnicalDetails
        }
    })

    $stopButton.Add_Click({
        $form.UseWaitCursor = $true
        try { $result = Invoke-StopAction; $script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12) }
        finally {
            $form.UseWaitCursor = $false
            & $render -UseCurrentSnapshot -PreserveTechnicalDetails
        }
    })

    $refreshButton.Add_Click({ & $render })

    $doctorButton.Add_Click({
        $form.UseWaitCursor = $true
        try {
            $result = Invoke-DoctorAction
            $script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12)
            if ($result.status -eq 'DOCTOR_COMPLETE') {
                [void][System.Windows.Forms.MessageBox]::Show("Diagnostics status: $($result.data.status)`r`nUse Technical Details for canonical checks.",'TW-Market Diagnostics')
            } else {
                [void][System.Windows.Forms.MessageBox]::Show("Diagnostics unavailable: $($result.reason_code)",'TW-Market Diagnostics')
            }
        } finally {
            $form.UseWaitCursor = $false
            & $render -UseCurrentSnapshot -PreserveTechnicalDetails
        }
    })

    $openButton.Add_Click({
        $result = Invoke-WorkbenchUriAction
        if ($result.status -eq 'WORKBENCH_READY') { Start-Process ([string]$result.data.uri) }
        else { [void][System.Windows.Forms.MessageBox]::Show('Workbench is not available from the current Local Runtime state.','TW-Market') }
    })

    $detailsButton.Add_Click({ Show-TechnicalDetails -Text $script:LastTechnicalDetails })
    $setupDetailsButton.Add_Click({ Show-TechnicalDetails -Text $script:LastTechnicalDetails })
    $setupDoctorButton.Add_Click({
        $form.UseWaitCursor = $true
        try {
            $result = Invoke-DoctorAction
            $script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12)
            if ($result.status -eq 'DOCTOR_COMPLETE') {
                [void][System.Windows.Forms.MessageBox]::Show("Diagnostics status: $($result.data.status)`r`nUse Technical Details for canonical checks.",'TW-Market Diagnostics')
            } else {
                [void][System.Windows.Forms.MessageBox]::Show("Diagnostics unavailable: $($result.reason_code)",'TW-Market Diagnostics')
            }
        } finally {
            $form.UseWaitCursor = $false
            & $render -PreserveTechnicalDetails
        }
    })
    $helpButton.Add_Click({
        $readme = Join-Path $script:BundleRoot 'README-PACKAGE.md'
        if (Test-Path -LiteralPath $readme -PathType Leaf) { Start-Process 'notepad.exe' -ArgumentList $readme }
    })

    $securityActionButton.Add_Click({
        if ($securityActionButton.Text -eq 'Restart TW-Market') {
            $form.UseWaitCursor = $true
            try {
                $result = Invoke-RestartAction
                $script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12)
                if ($result.status -ne 'RESTART_COMPLETE') {
                    [void][System.Windows.Forms.MessageBox]::Show("Restart did not complete: $($result.reason_code)",'TW-Market Security Master')
                }
            } finally {
                $form.UseWaitCursor = $false
                & $render -UseCurrentSnapshot -PreserveTechnicalDetails
            }
            return
        }

        $compatibilityRetry = $securityActionButton.Text -eq 'Retry TLS'
        if ($compatibilityRetry) {
            $answer = [System.Windows.Forms.MessageBox]::Show(
                "The official TWSE source was blocked by Python's strict X.509 compatibility rules.`r`n`r`nTW-Market can retry using verified TLS compatibility mode. Certificate validation and hostname verification remain enabled; only Python's additional X.509 strict flag is relaxed for this bounded acquisition.`r`n`r`nRetry now?",
                'TW-Market Security Master',[System.Windows.Forms.MessageBoxButtons]::YesNo,[System.Windows.Forms.MessageBoxIcon]::Information)
            if ($answer -ne [System.Windows.Forms.DialogResult]::Yes) { return }
        } else {
            $verb = if ($securityActionButton.Text -eq 'Install') { 'install' } else { 'update' }
            $answer = [System.Windows.Forms.MessageBox]::Show(
                "Security Master $verb performs one explicit bounded acquisition from official public sources. Continue?",
                'TW-Market Security Master',[System.Windows.Forms.MessageBoxButtons]::YesNo,[System.Windows.Forms.MessageBoxIcon]::Information)
            if ($answer -ne [System.Windows.Forms.DialogResult]::Yes) { return }
        }

        if ($compatibilityRetry) { & $setCardState $securityCard 'Retrying...' 'info' }
        else { & $setCardState $securityCard 'Updating...' 'info' }
        $securityActionButton.Enabled = $false
        [System.Windows.Forms.Application]::DoEvents()
        $form.UseWaitCursor = $true
        try {
            if ($compatibilityRetry) {
                $result = Invoke-SecurityMasterUpdateAction -Confirmed -SslPolicy 'compatibility' -CompatibilityConfirmed
            } else {
                $result = Invoke-SecurityMasterUpdateAction -Confirmed -SslPolicy 'strict'
            }
            $script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12)

            if ($result.status -eq 'SECURITY_MASTER_TLS_COMPATIBILITY_RETRY_AVAILABLE') {
                $retry = [System.Windows.Forms.MessageBox]::Show(
                    "The official TWSE source could not be validated under Python's strict X.509 rules.`r`n`r`nA verified TLS compatibility retry is available. Certificate and hostname verification remain enabled. This will perform one more explicit bounded acquisition.`r`n`r`nRetry with compatibility mode now?",
                    'TW-Market Security Master',[System.Windows.Forms.MessageBoxButtons]::YesNo,[System.Windows.Forms.MessageBoxIcon]::Information)
                if ($retry -eq [System.Windows.Forms.DialogResult]::Yes) {
                    & $setCardState $securityCard 'Retrying...' 'info'
                    [System.Windows.Forms.Application]::DoEvents()
                    $result = Invoke-SecurityMasterUpdateAction -Confirmed -SslPolicy 'compatibility' -CompatibilityConfirmed
                    $script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12)
                } else {
                    [void][System.Windows.Forms.MessageBox]::Show(
                        'Security Master was not installed. You can use Retry TLS later; no unverified TLS mode will be used.',
                        'TW-Market Security Master')
                }
            }

            if ($result.status -eq 'SECURITY_MASTER_UPDATE_COMPLETE') {
                if (-not $result.data.restart_required) {
                    $notice = 'Security Master is ready.'
                } elseif ($result.data.runtime_state -eq 'STOPPED') {
                    $notice = 'Security Master is ready. The new release will be used the next time TW-Market starts.'
                } else {
                    $notice = 'Security Master is ready. Restart TW-Market to use the new release.'
                }
                [void][System.Windows.Forms.MessageBox]::Show($notice,'TW-Market Security Master')
            } elseif ($result.status -eq 'SECURITY_MASTER_TLS_COMPATIBILITY_RETRY_AVAILABLE') {
                # The operator declined the explicit compatibility retry. The card remains actionable.
            } else {
                [void][System.Windows.Forms.MessageBox]::Show(
                    'Security Master could not retrieve or qualify the official source data. No release was activated. Use Advanced / Technical Details for the governed reason code and diagnostics.',
                    'TW-Market Security Master')
            }
        } finally {
            $form.UseWaitCursor = $false
            & $render -PreserveTechnicalDetails
        }
    })
    & $render
    [void]$form.ShowDialog()
}

if ($Action -ne 'Gui' -or $Headless) {
    if ($Action -eq 'Gui') { $Action = 'Status' }
    $result = Invoke-RequestedAction -RequestedAction $Action
    $code = Write-HeadlessResult -Result $result
    exit $code
}

Show-LauncherGui
exit 0
