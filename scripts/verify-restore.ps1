param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$backupFolder = (Resolve-Path -LiteralPath $BackupDirectory).Path
$manifestPath = Join-Path $backupFolder 'manifest.json'
$dumpPath = Join-Path $backupFolder 'database.dump'
$storageFolder = Join-Path $backupFolder 'storage'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

if ($manifest.format_version -ne 1 -or $manifest.dump_file -ne 'database.dump') {
    throw 'Unsupported backup manifest.'
}
if ((Get-Item -LiteralPath $dumpPath).Length -ne $manifest.dump_length -or
    (Get-FileHash -LiteralPath $dumpPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.dump_sha256) {
    throw 'Database archive integrity check failed.'
}

$listedFiles = @($manifest.storage_files | Where-Object { $null -ne $_ })
$actualFiles = @(Get-ChildItem -LiteralPath $storageFolder -File -Recurse)
if ($listedFiles.Count -ne $actualFiles.Count) { throw 'Storage file count does not match the manifest.' }
$seenPaths = @{}
foreach ($item in $listedFiles) {
    if ($item.path -notmatch '^[A-Za-z0-9_.-][A-Za-z0-9_./-]*$' -or
        $item.path -match '(^|/)\.\.?(/|$)' -or $seenPaths.ContainsKey($item.path)) {
        throw 'Invalid storage path in manifest.'
    }
    $seenPaths[$item.path] = $true
    $filePath = Join-Path $storageFolder ($item.path.Replace('/', [IO.Path]::DirectorySeparatorChar))
    if ((Get-Item -LiteralPath $filePath).Length -ne $item.length -or
        (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) {
        throw 'Uploaded-file integrity check failed.'
    }
}

# The temporary PostgreSQL server has no network and no host port. --rm removes its
# own anonymous volume after docker stop; existing ATLAS volumes are never mounted.
$restoreContainer = 'atlas-restore-' + [guid]::NewGuid().ToString('N').Substring(0, 12)
try {
    & docker run --detach --rm --network none --name $restoreContainer -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=atlas_restore_verify -e POSTGRES_USER=atlas_restore_user pgvector/pgvector:0.8.6-pg18-trixie | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Could not start the isolated restore container.' }

    $ready = $false
    for ($attempt = 0; $attempt -lt 45; $attempt++) {
        & docker exec $restoreContainer pg_isready -U atlas_restore_user -d atlas_restore_verify 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw 'Isolated PostgreSQL did not become ready.' }

    & docker cp $dumpPath "${restoreContainer}:/tmp/database.dump"
    if ($LASTEXITCODE -ne 0) { throw 'Could not copy the backup into the isolated container.' }
    & docker exec $restoreContainer pg_restore --exit-on-error --no-owner --no-acl -U atlas_restore_user -d atlas_restore_verify /tmp/database.dump
    if ($LASTEXITCODE -ne 0) { throw 'Isolated pg_restore failed.' }

    $countQuery = 'SELECT (SELECT count(*) FROM users),(SELECT count(*) FROM documents),(SELECT count(*) FROM document_chunks),(SELECT count(*) FROM conversations),(SELECT count(*) FROM messages);'
    $countLine = ((& docker exec $restoreContainer psql -X -A -t -F ',' -U atlas_restore_user -d atlas_restore_verify -c $countQuery) | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Could not verify restored table counts.' }
    $counts = $countLine -split ','
    if ($counts.Count -ne 5 -or
        [long]$counts[0] -ne $manifest.counts.users -or
        [long]$counts[1] -ne $manifest.counts.documents -or
        [long]$counts[2] -ne $manifest.counts.document_chunks -or
        [long]$counts[3] -ne $manifest.counts.conversations -or
        [long]$counts[4] -ne $manifest.counts.messages) {
        throw 'Restored record counts do not match the source snapshot.'
    }

    $revision = ((& docker exec $restoreContainer psql -X -A -t -U atlas_restore_user -d atlas_restore_verify -c 'SELECT version_num FROM alembic_version;') | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $revision -ne $manifest.migration_revision) {
        throw 'Restored migration revision does not match.'
    }
    Write-Output 'Isolated restore verified: five table counts, migration revision, archive hash and uploaded-file hashes match.'
}
finally {
    & docker stop $restoreContainer 2>$null | Out-Null
}
