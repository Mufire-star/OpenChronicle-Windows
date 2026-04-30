param(
    [switch]$Dev
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is required. Install it first: https://docs.astral.sh/uv/"
}

if ($Dev) {
    uv sync --all-extras
} else {
    uv tool install .
}

Write-Host "OpenChronicle Windows install complete."
