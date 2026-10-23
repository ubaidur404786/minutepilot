# Put the MinutePilot credentials and workflows into the running n8n.
# Run inside the docker\ folder, with the stack running:
#   powershell -ExecutionPolicy Bypass -File setup-n8n.ps1               (first time: credentials + workflows)
#   powershell -ExecutionPolicy Bypass -File setup-n8n.ps1 -WorkflowsOnly (after changing a workflow JSON file)
# Re-importing the Google credentials would erase their sign-in, so -WorkflowsOnly skips them.
param([switch]$WorkflowsOnly)
$ErrorActionPreference = 'Stop'

# read docker\.env
$cfg = @{}
foreach ($line in Get-Content .env) {
    if ($line -match '^\s*([A-Z_]+)=(.*)$') { $cfg[$Matches[1]] = $Matches[2].Trim() }
}

if (-not $WorkflowsOnly) {
    $creds = @(@{ id = 'MPollamaLocal001'; name = 'Ollama (local)'; type = 'ollamaApi'
                  data = @{ baseUrl = 'http://host.docker.internal:11434' } })
    if ($cfg['GOOGLE_CLIENT_ID'] -and $cfg['GOOGLE_CLIENT_SECRET']) {
        # same IDs as in the workflow JSON files, so every Google node finds its credential
        $google = @(
            @('MPgmail000000001', 'Gmail (MinutePilot)', 'gmailOAuth2'),
            @('MPtasks000000001', 'Google Tasks (MinutePilot)', 'googleTasksOAuth2Api'),
            @('MPcalendar000001', 'Google Calendar (MinutePilot)', 'googleCalendarOAuth2Api'),
            @('MPsheets00000001', 'Google Sheets (MinutePilot)', 'googleSheetsOAuth2Api')
        )
        foreach ($g in $google) {
            $creds += @{ id = $g[0]; name = $g[1]; type = $g[2]
                         data = @{ clientId = $cfg['GOOGLE_CLIENT_ID']; clientSecret = $cfg['GOOGLE_CLIENT_SECRET'] } }
        }
    } else {
        Write-Host 'GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET are empty in .env: only the Ollama credential is added.'
    }
    $json = ConvertTo-Json -InputObject $creds -Depth 5 -Compress
    # Windows PowerShell adds a BOM (EF BB BF) when piping to a program and n8n then
    # rejects the JSON, so the container drops those 3 bytes before importing.
    $json | docker compose exec -T n8n sh -c 'cat > /tmp/raw.json; if [ $(head -c 3 /tmp/raw.json | od -An -tx1 | tr -dc 0-9a-f) = efbbbf ]; then tail -c +4 /tmp/raw.json > /tmp/creds.json; else cp /tmp/raw.json /tmp/creds.json; fi; n8n import:credentials --input=/tmp/creds.json; rm -f /tmp/raw.json /tmp/creds.json'
}

# older installs had 6 separate workflows (now in n8n\archive\): switch them off, the webhook path is the same
$ErrorActionPreference = 'Continue'   # on a new install these IDs don't exist: ignore that
foreach ($id in 'MPchatAgent00001', 'MPmakeMinutes001', 'MPapprove0000001', 'MPagenda00000001', 'MPreminders00001', 'MPlookups0000001') {
    docker compose exec -T n8n n8n unpublish:workflow --id=$id 2>&1 | Out-Null
}
$ErrorActionPreference = 'Stop'
docker compose exec -T n8n n8n import:workflow --separate --input=/workflows
docker compose exec -T n8n n8n publish:workflow --id=MPallInOne000001
# n8n reads published workflows at start
docker compose restart n8n
Write-Host 'Done. Open http://localhost:5678 (n8n) and http://localhost:8000 (chat page).'
