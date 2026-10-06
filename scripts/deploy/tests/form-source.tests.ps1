# Offline tests: docker/git below are mocks; no real engine or data is touched.
$ErrorActionPreference = 'Stop'
$legalragRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$legalragScript = Join-Path $legalragRoot 'scripts\deploy\form-source.ps1'
$legalragCases = @('check', 'preflight', 'up', 'wrong-project', 'wrong-service', 'missing-image', 'dirty-source', 'changed-environment')

foreach ($legalragCase in $legalragCases) {
    & {
        param($CaseName, $SourceRoot, $ScriptPath)
        $legalragTestState = @{CaseName=$CaseName;UpCalls=0;UpArguments=@()}
        function git {
            param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
            $global:LASTEXITCODE = 0
            if ($legalragTestState.CaseName -eq 'dirty-source') { Write-Output ' M frontend/src/example.ts' }
        }
        function docker {
            param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
            $global:LASTEXITCODE = 0
            if ($Arguments[0] -eq 'compose' -and $Arguments -contains 'config') {
                $legalragServices = [ordered]@{}
                $legalragUseSource = $Arguments -contains (Join-Path $SourceRoot 'prod\docker-compose.form-source.yml')
                foreach ($legalragService in @('frontend','query-service','form-service','llm-service')) {
                    $legalragImageSuffix = @{frontend='frontend';'query-service'='query';'form-service'='form'}[$legalragService]
                    $legalragServiceConfig = [ordered]@{
                        container_name = ('legalrag-' + $legalragImageSuffix)
                        image = ('old/' + $legalragService + ':v1.0.2')
                        environment = @{SENTINEL='fake-only'}
                        ports = @(@{target=8002;published='8002'})
                    }
                    if ($legalragUseSource -and $legalragService -ne 'llm-service') {
                        $legalragServiceConfig.image = "legalrag-source/${legalragImageSuffix}:test-revision"
                        $legalragServiceConfig.build = @{context=(Join-Path $SourceRoot $legalragService).Replace('\','/');dockerfile='Dockerfile'}
                        $legalragServiceConfig.pull_policy = 'never'
                        if ($legalragTestState.CaseName -eq 'changed-environment') { $legalragServiceConfig.environment = @{SENTINEL='changed'} }
                    }
                    $legalragServices[$legalragService] = $legalragServiceConfig
                }
                @{name='legalrag';services=$legalragServices;volumes=@{data=@{name='existing-data'}};networks=@{default=@{name='existing-network'}}} | ConvertTo-Json -Depth 12
            } elseif ($Arguments[0] -eq 'compose' -and $Arguments -contains 'up') {
                $legalragTestState.UpCalls++
                $legalragTestState.UpArguments = $Arguments
            } elseif ($Arguments[0] -eq 'info') {
                Write-Output 'linux'
            } elseif ($Arguments[0] -eq 'inspect') {
                if ($Arguments[2] -ne '{{json .Config.Labels}}') { throw 'Ownership lookup must use quote-free JSON.' }
                $legalragService = @{ 'legalrag-frontend'='frontend';'legalrag-query'='query-service';'legalrag-form'='form-service' }[$Arguments[-1]]
                $legalragProject = if ($legalragTestState.CaseName -eq 'wrong-project') {'unrelated'} else {'legalrag'}
                if ($legalragTestState.CaseName -eq 'wrong-service') { $legalragService = 'unrelated' }
                @{'com.docker.compose.project'=$legalragProject;'com.docker.compose.service'=$legalragService} | ConvertTo-Json -Compress
            } elseif ($Arguments[0] -eq 'image') {
                if ($legalragTestState.CaseName -eq 'missing-image') { $global:LASTEXITCODE=1 } else { Write-Output 'sha256:synthetic' }
            } else { throw ('Unexpected mock Docker invocation: ' + ($Arguments -join ' ')) }
        }
        $legalragFailed = $false
        $legalragAction = if ($CaseName -eq 'check') {'check'} elseif ($CaseName -eq 'up') {'up'} else {'preflight'}
        try {
            # Resolve-Path needs existing files. Mock Compose never reads their contents.
            & $ScriptPath -Action $legalragAction -ComposePath (Join-Path $SourceRoot 'prod\docker-compose.yml') -EnvPath $PSCommandPath -ProjectName legalrag -ImageTag test-revision 6>$null | Out-Null
        } catch { $legalragFailed = $true }
        $legalragMustFail = $CaseName -in @('wrong-project','wrong-service','missing-image','dirty-source','changed-environment')
        if ($legalragFailed -ne $legalragMustFail) { throw "Unexpected success/failure in $CaseName" }
        $legalragExpectedUpCalls = if ($CaseName -eq 'up') {1} else {0}
        if ($legalragTestState.UpCalls -ne $legalragExpectedUpCalls) { throw "Unexpected container mutation in $CaseName" }
        if ($CaseName -eq 'up') {
            foreach ($legalragFlag in @('--no-deps','--no-build','--pull','never','--wait','frontend','query-service','form-service')) {
                if ($legalragTestState.UpArguments -notcontains $legalragFlag) { throw "Missing guarded up argument $legalragFlag" }
            }
            if ($legalragTestState.UpArguments -contains 'llm-service') { throw 'Model service must not be upgraded.' }
        }
        Write-Output "PASS $CaseName"
    } $legalragCase $legalragRoot $legalragScript
}
Write-Output '8/8 source deployment guard tests PASS (mock-only).'
