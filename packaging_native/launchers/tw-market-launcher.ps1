param(
    [ValidateSet('Gui','Status','Setup','Start','Stop','Doctor','WorkbenchUri')]
    [string]$Action = 'Gui',
    [switch]$Headless,
    [string]$PythonPath,
    [switch]$ConfirmStaleOwnership
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:BundleRoot = Split-Path -Parent $PSScriptRoot
$script:MarketCmd = Join-Path $script:BundleRoot 'tw-market.cmd'
$script:BootstrapPs1 = Join-Path $script:BundleRoot 'bootstrap\bootstrap.ps1'
$script:RuntimePython = Join-Path $script:BundleRoot 'runtime\venv\Scripts\python.exe'
$script:RuntimeMarker = Join-Path $script:BundleRoot 'runtime\runtime-marker.json'
$script:SelectedPython = $PythonPath
$script:LastTechnicalDetails = ''
$script:LastSnapshotDetails = ''
$script:CurrentSnapshot = $null

function New-LauncherResult {
    param([string]$Status, [string]$ReasonCode = '', [object]$Data = $null)
    $result = [ordered]@{ status = $Status }
    if ($ReasonCode) { $result.reason_code = $ReasonCode }
    if ($null -ne $Data) { $result.data = $Data }
    [pscustomobject]$result
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
    if ($after.status -eq 'RUNNING_READY') { return New-LauncherResult -Status 'START_COMPLETE' -Data $after.data }
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

function Invoke-DoctorAction {
    if ((Get-RuntimePresence) -ne 'PRESENT') {
        return New-LauncherResult -Status 'DOCTOR_BLOCKED' -ReasonCode 'PACKAGE_RUNTIME_NOT_READY'
    }
    $run = Invoke-Lifecycle -Command 'doctor'
    $script:LastTechnicalDetails = $run.raw
    if ($null -eq $run.payload) { return New-LauncherResult -Status 'DOCTOR_FAILED' -ReasonCode 'DOCTOR_COMMAND_FAILED' }
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
        'Doctor' { return Invoke-DoctorAction }
        'WorkbenchUri' { return Invoke-WorkbenchUriAction }
        default { return New-LauncherResult -Status 'ACTION_BLOCKED' -ReasonCode 'UNSUPPORTED_HEADLESS_ACTION' }
    }
}

function Write-HeadlessResult {
    param([object]$Result)
    $json = $Result | ConvertTo-Json -Depth 12 -Compress
    [Console]::Out.WriteLine($json)
    if ($Result.status -in @('STATUS_ERROR','SETUP_BLOCKED','PREREQUISITE_BLOCKED','START_FAILED','START_INCOMPLETE','STOP_FAILED','STOP_INCOMPLETE','DOCTOR_FAILED','DOCTOR_BLOCKED','ACTION_BLOCKED','CONFIRMATION_REQUIRED')) { return 1 }
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
    $form.Width = 620; $form.Height = 520; $form.StartPosition = 'CenterScreen'
    $form.FormBorderStyle = 'FixedDialog'; $form.MaximizeBox = $false

    $title = New-Object System.Windows.Forms.Label
    $title.Text = 'TW-Market Local Operator'; $title.AutoSize = $true
    $title.Font = New-Object System.Drawing.Font('Segoe UI',16,[System.Drawing.FontStyle]::Bold)
    $title.Location = New-Object System.Drawing.Point(24,20); $form.Controls.Add($title)
    $rows = @('Package Runtime','Python 3.13 x64','Local Installation','Local Runtime','Workbench','Security Master','Local MCP')
    $valueLabels = @{}
    $y = 70
    foreach ($name in $rows) {
        $nameLabel = New-Object System.Windows.Forms.Label
        $nameLabel.Text = $name; $nameLabel.Width = 170
        $nameLabel.Location = New-Object System.Drawing.Point(30,$y)
        $valueLabel = New-Object System.Windows.Forms.Label
        $valueLabel.Text = 'Checking...'; $valueLabel.Width = 330
        $valueLabel.Location = New-Object System.Drawing.Point(210,$y)
        $form.Controls.Add($nameLabel); $form.Controls.Add($valueLabel)
        $valueLabels[$name] = $valueLabel; $y += 28
    }

    $message = New-Object System.Windows.Forms.Label
    $message.Width = 550; $message.Height = 56
    $message.Location = New-Object System.Drawing.Point(30,270)
    $form.Controls.Add($message)

    $setupButton = New-Object System.Windows.Forms.Button
    $setupButton.Text = 'Set Up TW-Market'; $setupButton.Width = 150
    $setupButton.Location = New-Object System.Drawing.Point(30,340)
    $locateButton = New-Object System.Windows.Forms.Button
    $locateButton.Text = 'Locate Python 3.13...'; $locateButton.Width = 160
    $locateButton.Location = New-Object System.Drawing.Point(195,340)
    $startButton = New-Object System.Windows.Forms.Button
    $startButton.Text = 'Start TW-Market'; $startButton.Width = 130
    $startButton.Location = New-Object System.Drawing.Point(30,380)
    $openButton = New-Object System.Windows.Forms.Button
    $openButton.Text = 'Open Workbench'; $openButton.Width = 130
    $openButton.Location = New-Object System.Drawing.Point(170,380)
    $refreshButton = New-Object System.Windows.Forms.Button
    $refreshButton.Text = 'Refresh'; $refreshButton.Width = 90
    $refreshButton.Location = New-Object System.Drawing.Point(310,380)
    $doctorButton = New-Object System.Windows.Forms.Button
    $doctorButton.Text = 'Diagnose'; $doctorButton.Width = 90
    $doctorButton.Location = New-Object System.Drawing.Point(410,380)
    $stopButton = New-Object System.Windows.Forms.Button
    $stopButton.Text = 'Stop TW-Market'; $stopButton.Width = 130
    $stopButton.Location = New-Object System.Drawing.Point(30,420)
    $detailsButton = New-Object System.Windows.Forms.Button
    $detailsButton.Text = 'Technical Details'; $detailsButton.Width = 130
    $detailsButton.Location = New-Object System.Drawing.Point(170,420)
    $helpButton = New-Object System.Windows.Forms.Button
    $helpButton.Text = 'Installation Help'; $helpButton.Width = 120
    $helpButton.Location = New-Object System.Drawing.Point(310,420)
    $closeButton = New-Object System.Windows.Forms.Button
    $closeButton.Text = 'Close'; $closeButton.Width = 90
    $closeButton.Location = New-Object System.Drawing.Point(450,420)
    foreach ($button in @($setupButton,$locateButton,$startButton,$openButton,$refreshButton,$doctorButton,$stopButton,$detailsButton,$helpButton,$closeButton)) {
        $form.Controls.Add($button)
    }
    $script:CurrentSnapshot = $null
    $script:DiscoveredPython = $null

    $render = {
        param([switch]$UseCurrentSnapshot, [switch]$PreserveTechnicalDetails)
        if ($UseCurrentSnapshot -and $null -ne $script:CurrentSnapshot) {
            $snapshot = $script:CurrentSnapshot
        } else {
            $snapshot = Get-LauncherSnapshot -PreserveTechnicalDetails:$PreserveTechnicalDetails
            $script:CurrentSnapshot = $snapshot
        }
        $presence = Get-RuntimePresence
        if ($presence -eq 'MISSING') {
            $valueLabels['Package Runtime'].Text = 'Not set up'
            $script:DiscoveredPython = Find-Python313
            if ($script:DiscoveredPython) { $valueLabels['Python 3.13 x64'].Text = 'Ready' }
            else { $valueLabels['Python 3.13 x64'].Text = 'Required' }
        } elseif ($presence -eq 'PRESENT') {
            $valueLabels['Package Runtime'].Text = 'Ready'
            $valueLabels['Python 3.13 x64'].Text = 'Runtime ready'
        } else {
            $valueLabels['Package Runtime'].Text = 'Needs attention'
            $valueLabels['Python 3.13 x64'].Text = 'Not evaluated'
        }
        $payload = $null
        if ($snapshot.PSObject.Properties.Name -contains 'data') { $payload = $snapshot.data }
        $installationText = 'Not initialized'
        if ($payload -and ($payload.PSObject.Properties.Name -contains 'installation') -and $payload.installation) {
            $installationText = [string]$payload.installation.installation_status
        }
        $valueLabels['Local Installation'].Text = $installationText
        $valueLabels['Local Runtime'].Text = $snapshot.status
        $valueLabels['Workbench'].Text = if ($snapshot.status -eq 'RUNNING_READY') { 'Ready' } else { 'Unavailable' }
        $identityText = 'Unknown'
        $mcpText = 'Unknown'
        if ($payload -and ($payload.PSObject.Properties.Name -contains 'identity') -and $payload.identity) {
            $identityText = [string]$payload.identity.status
        }
        if ($payload -and ($payload.PSObject.Properties.Name -contains 'mcp') -and $payload.mcp) {
            $mcpText = [string]$payload.mcp.status
        }
        $valueLabels['Security Master'].Text = $identityText
        $valueLabels['Local MCP'].Text = $mcpText
        switch ($snapshot.status) {
            'SETUP_REQUIRED' { $message.Text = 'TW-Market needs initial local setup. No market data will be downloaded.' }
            'STOPPED' { $message.Text = 'TW-Market is ready. Start the Local Runtime when you want to use the Workbench.' }
            'STARTING' { $message.Text = 'TW-Market is starting. Use Refresh to check again.' }
            'RUNNING_READY' { $message.Text = 'Local Runtime and Workbench are ready.' }
            'RUNNING_UNHEALTHY' { $message.Text = 'The owned TW-Market process is running, but Local Runtime health is not ready.' }
            'PORT_CONFLICT' { $message.Text = 'The configured local port is being used by another process. TW-Market will not control it.' }
            'STALE_OWNERSHIP' { $message.Text = 'Stale TW-Market ownership metadata was detected. Start requires confirmation.' }
            'INSTALLATION_INCOMPLETE' { $message.Text = 'The local TW-Market installation needs attention.' }
            default { $message.Text = 'TW-Market status could not be determined safely. Use Diagnose or Technical Details.' }
        }
        $setupButton.Enabled = ($snapshot.status -eq 'SETUP_REQUIRED' -and $snapshot.reason_code -ne 'PACKAGE_RUNTIME_NEEDS_ATTENTION' -and (($presence -eq 'PRESENT') -or $script:DiscoveredPython))
        $locateButton.Enabled = ($presence -eq 'MISSING')
        $startButton.Enabled = $snapshot.status -in @('STOPPED','STALE_OWNERSHIP')
        $openButton.Enabled = $snapshot.status -eq 'RUNNING_READY'
        $refreshButton.Enabled = $true
        $doctorButton.Enabled = $presence -eq 'PRESENT'
        $stopButton.Enabled = $snapshot.status -in @('RUNNING_READY','RUNNING_UNHEALTHY')
        $detailsButton.Enabled = $true
        if (-not $PreserveTechnicalDetails) {
            $script:LastTechnicalDetails = ($snapshot | ConvertTo-Json -Depth 12)
        }
    }

    $setupButton.Add_Click({
        $form.UseWaitCursor = $true
        $setupUseCurrent = $false
        try {
            $result = Invoke-Setup
            $script:LastTechnicalDetails = ($result | ConvertTo-Json -Depth 12)
            if ($result.status -eq 'SETUP_COMPLETE') {
                $setupUseCurrent = $true
                [void][System.Windows.Forms.MessageBox]::Show('TW-Market local setup is complete. No market data was downloaded.','TW-Market Setup')
            } else {
                [void][System.Windows.Forms.MessageBox]::Show("Setup did not complete: $($result.reason_code)",'TW-Market Setup')
            }
        } finally {
            $form.UseWaitCursor = $false
            if ($setupUseCurrent) { & $render -UseCurrentSnapshot -PreserveTechnicalDetails }
            else { & $render -PreserveTechnicalDetails }
        }
    })

    $locateButton.Add_Click({
        $picker = New-Object System.Windows.Forms.OpenFileDialog
        $picker.Title = 'Locate CPython 3.13 x64 python.exe'; $picker.Filter = 'python.exe|python.exe|Executable files|*.exe'
        if ($picker.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            $candidate = Test-PythonExecutable -Executable $picker.FileName -Source 'user-selected'
            if ($candidate) {
                $script:SelectedPython = $candidate.executable
                $script:DiscoveredPython = $candidate
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
            $form.UseWaitCursor = $false
            $script:ConfirmStaleOwnership = $false
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
                [void][System.Windows.Forms.MessageBox]::Show("Diagnostics status: $($result.data.status)`r`nUse Technical Details for the canonical checks.",'TW-Market Diagnostics')
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
        if ($result.status -eq 'WORKBENCH_READY') {
            Start-Process ([string]$result.data.uri)
        } else {
            [void][System.Windows.Forms.MessageBox]::Show('Workbench is not available from the current Local Runtime state.','TW-Market')
        }
    })

    $detailsButton.Add_Click({ Show-TechnicalDetails -Text $script:LastTechnicalDetails })
    $helpButton.Add_Click({
        $readme = Join-Path $script:BundleRoot 'README-PACKAGE.md'
        if (Test-Path -LiteralPath $readme -PathType Leaf) { Start-Process 'notepad.exe' -ArgumentList $readme }
    })
    $closeButton.Add_Click({ $form.Close() })
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
