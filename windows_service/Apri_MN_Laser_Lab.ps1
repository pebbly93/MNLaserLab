$ErrorActionPreference = "SilentlyContinue"

$ports = 8000..8019
$opened = $false

foreach ($p in $ports) {
    $url = "http://127.0.0.1:$p/api/health"
    try {
        $res = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1
        if ($res.StatusCode -eq 200) {
            Start-Process "http://127.0.0.1:$p/"
            $opened = $true
            break
        }
    } catch {}
}

if (-not $opened) {
    Start-Process "http://127.0.0.1:8000/"
}
