[CmdletBinding()]
param(
    [ValidateSet('check', 'preflight', 'build', 'up', 'status')]
    [string]$Action = 'check',
    [Parameter(Mandatory = $true)]
    [string]$ComposePath,
    [Parameter(Mandatory = $true)]
    [string]$EnvPath,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9][a-z0-9_-]*$')]
    [string]$ProjectName,
    [ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$')]
    [string]$ImageTag
)

$ErrorActionPreference = 'Stop'
$legalragSourceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$legalragBase = (Resolve-Path -LiteralPath $ComposePath).Path
$legalragEnvFile = (Resolve-Path -LiteralPath $EnvPath).Path
$legalragOverride = Join-Path $legalragSourceRoot 'prod\docker-compose.form-source.yml'
$legalragServices = @('frontend', 'query-service', 'form-service')

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker CLI/Compose is required; check mode does not start the engine.'
}
if (!$ImageTag) {
    $ImageTag = (& git -C $legalragSourceRoot rev-parse --short=12 HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or !$ImageTag) { throw 'Cannot determine source revision.' }
}
$legalragPreviousRoot = [Environment]::GetEnvironmentVariable('LEGALRAG_SOURCE_ROOT', 'Process')
$legalragPreviousTag = [Environment]::GetEnvironmentVariable('LEGALRAG_SOURCE_TAG', 'Process')

function Invoke-CheckedDocker {
    param([string[]]$Arguments)
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed (exit $LASTEXITCODE)." }
}

function Read-ComposeConfig {
    param([string[]]$Arguments)
    # Capture JSON in memory. Never print resolved environment/secrets.
    $legalragJson = @(Invoke-CheckedDocker -Arguments ($Arguments + @('config', '--format', 'json')))
    return (($legalragJson -join [Environment]::NewLine) | ConvertFrom-Json)
}

function Read-ContainerOwnership {
    param([string]$ContainerName)
    # A quoted label key inside a Go template is mangled by Windows PowerShell 5
    # native argument passing. JSON needs no embedded quotes and preserves both
    # ownership checks without weakening the guard.
    $legalragLabelJson = @(Invoke-CheckedDocker -Arguments @('inspect', '--format', '{{json .Config.Labels}}', $ContainerName))
    $legalragLabels = ($legalragLabelJson -join [Environment]::NewLine) | ConvertFrom-Json
    if (!$legalragLabels) { throw "Missing Compose ownership labels for $ContainerName" }
    return [pscustomobject]@{
        Project = [string]$legalragLabels.'com.docker.compose.project'
        Service = [string]$legalragLabels.'com.docker.compose.service'
    }
}

function Assert-SameConfig {
    param($Before, $After, [string]$Label)
    $legalragBeforeJson = ConvertTo-Json -InputObject $Before -Depth 100 -Compress
    $legalragAfterJson = ConvertTo-Json -InputObject $After -Depth 100 -Compress
    if ($legalragBeforeJson -cne $legalragAfterJson) {
        throw "Source override changed a protected setting: $Label"
    }
}

try {
    $env:LEGALRAG_SOURCE_ROOT = $legalragSourceRoot.Replace('\', '/')
    $env:LEGALRAG_SOURCE_TAG = $ImageTag
    $legalragBaseArgs = @('compose', '--project-name', $ProjectName, '--env-file', $legalragEnvFile, '-f', $legalragBase)
    $legalragSourceArgs = $legalragBaseArgs + @('-f', $legalragOverride)
    $legalragBaseConfig = Read-ComposeConfig -Arguments $legalragBaseArgs
    $legalragSourceConfig = Read-ComposeConfig -Arguments $legalragSourceArgs

    foreach ($legalragSection in @('name', 'volumes', 'networks')) {
        Assert-SameConfig $legalragBaseConfig.$legalragSection $legalragSourceConfig.$legalragSection $legalragSection
    }
    Assert-SameConfig @($legalragBaseConfig.services.PSObject.Properties.Name) @($legalragSourceConfig.services.PSObject.Properties.Name) 'service set'
    foreach ($legalragProperty in $legalragBaseConfig.services.PSObject.Properties) {
        $legalragName = $legalragProperty.Name
        $legalragBefore = $legalragProperty.Value
        $legalragAfter = $legalragSourceConfig.services.$legalragName
        if ($legalragName -notin $legalragServices) {
            Assert-SameConfig $legalragBefore $legalragAfter "service $legalragName"
            continue
        }
        foreach ($legalragSetting in $legalragBefore.PSObject.Properties) {
            if ($legalragSetting.Name -in @('image', 'build', 'pull_policy', 'healthcheck')) { continue }
            Assert-SameConfig $legalragSetting.Value $legalragAfter.($legalragSetting.Name) "$legalragName.$($legalragSetting.Name)"
        }
        $legalragExpectedContext = (Join-Path $legalragSourceRoot $legalragName).Replace('\', '/')
        if ($legalragAfter.build.context.Replace('\', '/') -cne $legalragExpectedContext) {
            throw "Unexpected build context for $legalragName"
        }
        if ($legalragAfter.pull_policy -ne 'never') { throw "Unexpected pull policy for $legalragName" }
        if ($legalragAfter.image -notlike "legalrag-source/*:$ImageTag") { throw "Unexpected image for $legalragName" }
    }
    foreach ($legalragService in $legalragServices) {
        if (!$legalragBaseConfig.services.PSObject.Properties[$legalragService]) {
            throw "Existing Compose is missing $legalragService"
        }
    }
    Write-Host 'CHECK PASS: only frontend/query/form source images and frontend/query healthchecks are overridden.'
    Write-Host 'Existing environment, ports, dependencies, model services, networks and volumes are preserved.'
    Write-Host "Source image tag: $ImageTag"
    if ($Action -eq 'check') {
        Write-Host 'Configuration check only: no engine, image build or container change was performed.'
        return
    }

    if ($Action -in @('preflight', 'build', 'up')) {
        $legalragDirty = @(& git -C $legalragSourceRoot status --porcelain -- frontend query-service form-service prod/docker-compose.form-source.yml scripts/deploy/form-source.ps1)
        if ($LASTEXITCODE -ne 0 -or $legalragDirty.Count -gt 0) {
            throw 'Build inputs are not a clean Git revision. Commit or resolve them before source deployment.'
        }
    }
    $legalragDockerType = @(Invoke-CheckedDocker -Arguments @('info', '--format', '{{.OSType}}')) -join ''
    if ($legalragDockerType.Trim() -ne 'linux') { throw 'Docker Desktop must be running Linux containers.' }
    if ($Action -eq 'build') {
        Invoke-CheckedDocker -Arguments ($legalragSourceArgs + @('build', '--pull') + $legalragServices)
        Write-Host 'Images built on this machine. Containers have NOT been updated.'
    } elseif ($Action -in @('preflight', 'up')) {
        foreach ($legalragService in $legalragServices) {
            $legalragContainer = $legalragSourceConfig.services.$legalragService.container_name
            if (!$legalragContainer) { throw "Missing existing container name for $legalragService" }
            $legalragOwnership = Read-ContainerOwnership -ContainerName $legalragContainer
            if ($legalragOwnership.Project.Trim() -ne $ProjectName -or $legalragOwnership.Service.Trim() -ne $legalragService) {
                throw "Container ownership mismatch for $legalragService; refusing to recreate it."
            }
            Invoke-CheckedDocker -Arguments @('image', 'inspect', '--format', '{{.Id}}', $legalragSourceConfig.services.$legalragService.image)
        }
        if ($Action -eq 'preflight') {
            Write-Host 'PREFLIGHT PASS: existing container ownership and all three local images were verified; no container changed.'
            return
        }
        Invoke-CheckedDocker -Arguments ($legalragSourceArgs + @('up', '--detach', '--no-deps', '--no-build', '--pull', 'never', '--wait', '--wait-timeout', '180') + $legalragServices)
        Write-Host 'Only frontend/query/form were updated. Run the form and RAG acceptance checks.'
    } elseif ($Action -eq 'status') {
        Invoke-CheckedDocker -Arguments ($legalragSourceArgs + @('ps') + $legalragServices)
    }
} finally {
    [Environment]::SetEnvironmentVariable('LEGALRAG_SOURCE_ROOT', $legalragPreviousRoot, 'Process')
    [Environment]::SetEnvironmentVariable('LEGALRAG_SOURCE_TAG', $legalragPreviousTag, 'Process')
}
