[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('up', 'build', 'logs', 'stop', 'status', 'frontend', 'test', 'check')]
    [string]$Action,
    [ValidateSet('query-service', 'form-service', 'storage-service')]
    [string]$Service = 'form-service'
)

$ErrorActionPreference = 'Stop'
$legalragRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$legalragCompose = Join-Path $legalragRoot 'docker-compose.form-dev.yml'
$legalragArgs = @('compose', '--project-name', 'legalrag-form-dev', '--file', $legalragCompose)

function Invoke-FormCompose {
    param([string[]]$Arguments)
    & docker @legalragArgs @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Form dev Docker command failed ($LASTEXITCODE)." }
}

Push-Location -LiteralPath $legalragRoot
try {
    if ($Action -eq 'frontend') {
        if (!(Test-Path -LiteralPath 'frontend\node_modules\vite\package.json')) {
            throw 'Frontend dependencies missing. Run npm.cmd ci in frontend first.'
        }
        $env:VITE_QUERY_SERVICE_URL = 'http://localhost:18002'
        $env:VITE_ADMIN_SERVICE_URL = 'http://localhost:18002'
        $env:VITE_FORM_SERVICE_URL = 'http://localhost:18015'
        $env:VITE_STORAGE_SERVICE_URL = 'http://localhost:18010'
        Push-Location -LiteralPath (Join-Path $legalragRoot 'frontend')
        try {
            & npm.cmd run dev -- --host 127.0.0.1 --port 3006 --strictPort
            if ($LASTEXITCODE -ne 0) { throw 'Frontend dev server failed.' }
        } finally { Pop-Location }
        return
    }

    if (!(Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker CLI is not available.' }
    if ($Action -eq 'check') {
        Invoke-FormCompose -Arguments @('config', '--quiet')
        Write-Host 'Form dev Compose configuration is valid.'
        return
    }

    $legalragDockerType = & docker info --format '{{.OSType}}'
    if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop with Linux containers first.' }
    if ($legalragDockerType -ne 'linux') { throw 'Switch Docker Desktop to Linux containers first.' }
    switch ($Action) {
        'up' {
            Invoke-FormCompose -Arguments @('up', '-d', '--build', '--wait', '--wait-timeout', '180')
            Write-Host 'FORM_DEV_READY'
            Write-Host 'Open Chrome: http://localhost:3006/forms/demo/Gi%E1%BA%A5y%20%C4%91%C4%83ng%20k%C3%BD%20khai%20sinh.docx'
            Write-Host 'Real QR/Word/router, read-only local template store; no RAG/DB/MinIO or dossier storage.'
        }
        'build' { Invoke-FormCompose -Arguments @('build', 'storage-service', 'form-service', 'query-service') }
        'logs' { Invoke-FormCompose -Arguments @('logs', '--follow', '--tail', '80', $Service) }
        'stop' {
            # Stop, do not remove containers or volumes. No production Compose.
            Invoke-FormCompose -Arguments @('stop')
            Write-Host 'Only legalrag-form-dev containers stopped; no data/volumes deleted.'
        }
        'status' { Invoke-FormCompose -Arguments @('ps', '--all') }
        'test' {
            Invoke-FormCompose -Arguments @('exec', '-T', 'form-service', 'python', '-B', '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-v')
            Invoke-FormCompose -Arguments @('exec', '-T', 'form-service', 'python', '-B', '/app/tests/smoke_form_dev.py')
        }
    }
} finally { Pop-Location }
