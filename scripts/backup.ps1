param(
    [string]$BackupRoot = (Join-Path $env:LOCALAPPDATA 'ATLAS\Backups')
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$dbContainer = $null
$remoteDump = $null

Push-Location $projectRoot
try {
    $dbContainer = ((& docker compose --env-file .env.compose ps -q db) | Out-String).Trim()
    $backendContainer = ((& docker compose --env-file .env.compose ps -q backend) | Out-String).Trim()
    if (-not $dbContainer -or -not $backendContainer) {
        throw 'ATLAS database and backend containers must be running.'
    }

    $backupFolder = Join-Path $BackupRoot ('atlas-' + (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $backupFolder | Out-Null
    $storageFolder = Join-Path $backupFolder 'storage'
    New-Item -ItemType Directory -Path $storageFolder | Out-Null

    # pg_dump writes inside the Linux container. PowerShell never redirects binary stdout.
    $remoteDump = '/tmp/atlas-backup-' + [guid]::NewGuid().ToString('N') + '.dump'
    & docker exec --user postgres $dbContainer pg_dump --username atlas_compose_user --dbname atlas_compose_db --format custom --file $remoteDump
    if ($LASTEXITCODE -ne 0) { throw 'pg_dump failed.' }

    & docker exec $dbContainer pg_restore --list $remoteDump | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'pg_restore could not read the database archive.' }

    $dumpPath = Join-Path $backupFolder 'database.dump'
    & docker cp "${dbContainer}:$remoteDump" $dumpPath
    if ($LASTEXITCODE -ne 0 -or (Get-Item -LiteralPath $dumpPath).Length -eq 0) {
        throw 'The database archive could not be copied to Windows.'
    }

    # A read-only count snapshot makes the later isolated restore check meaningful.
    $countQuery = 'SELECT (SELECT count(*) FROM users),(SELECT count(*) FROM documents),(SELECT count(*) FROM document_chunks),(SELECT count(*) FROM conversations),(SELECT count(*) FROM messages);'
    $countLine = ((& docker exec $dbContainer psql -X -A -t -F ',' -U atlas_compose_user -d atlas_compose_db -c $countQuery) | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Could not read source table counts.' }
    $counts = $countLine -split ','
    if ($counts.Count -ne 5) { throw 'Unexpected source table count result.' }

    $revision = ((& docker exec $dbContainer psql -X -A -t -U atlas_compose_user -d atlas_compose_db -c 'SELECT version_num FROM alembic_version;') | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $revision) { throw 'Could not read the source migration revision.' }

    # Uploaded files are a separate backup artifact from the database dump.
    & docker cp "${backendContainer}:/app/storage/." $storageFolder
    if ($LASTEXITCODE -ne 0) { throw 'Could not copy the uploaded-file storage volume.' }

    $storageFiles = @(
        Get-ChildItem -LiteralPath $storageFolder -File -Recurse | ForEach-Object {
            [ordered]@{
                path = $_.FullName.Substring($storageFolder.Length + 1).Replace('\', '/')
                length = $_.Length
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        }
    )
    $manifest = [ordered]@{
        format_version = 1
        created_utc = (Get-Date).ToUniversalTime().ToString('o')
        source_database = 'atlas_compose_db'
        dump_file = 'database.dump'
        dump_length = (Get-Item -LiteralPath $dumpPath).Length
        dump_sha256 = (Get-FileHash -LiteralPath $dumpPath -Algorithm SHA256).Hash.ToLowerInvariant()
        migration_revision = $revision
        counts = [ordered]@{
            users = [long]$counts[0]
            documents = [long]$counts[1]
            document_chunks = [long]$counts[2]
            conversations = [long]$counts[3]
            messages = [long]$counts[4]
        }
        storage_files = $storageFiles
    }
    $manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $backupFolder 'manifest.json') -Encoding UTF8
    Write-Output "Backup complete: $backupFolder"
    Write-Output "Database archive bytes: $($manifest.dump_length)"
    Write-Output "Uploaded files copied: $($storageFiles.Count)"
}
finally {
    if ($dbContainer -and $remoteDump) {
        & docker exec $dbContainer rm -f $remoteDump 2>$null | Out-Null
    }
    Pop-Location
}
