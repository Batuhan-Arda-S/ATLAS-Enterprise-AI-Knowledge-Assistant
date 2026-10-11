$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Show-HttpStatus([string]$Name, [string]$Url) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
        Write-Output "$Name`: HTTP $($response.StatusCode)"
    }
    catch {
        if ($_.Exception.Response) {
            Write-Output "$Name`: HTTP $([int]$_.Exception.Response.StatusCode)"
        }
        else {
            Write-Output "$Name`: unreachable"
        }
    }
}

Push-Location $projectRoot
try {
    & docker compose --env-file .env.compose ps
    $containers = @(& docker compose --env-file .env.compose ps -q)
    foreach ($container in $containers) {
        & docker inspect --format '{{.Name}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}not-configured{{end}}' $container
    }
    Show-HttpStatus 'Frontend' 'http://127.0.0.1:8088/'
    Show-HttpStatus 'Backend readiness' 'http://127.0.0.1:8088/api/health/ready'
    Show-HttpStatus 'Ollama model' 'http://127.0.0.1:8088/api/health/ollama'
}
finally {
    Pop-Location
}
