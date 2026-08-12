param (
    [Parameter(Mandatory=$true)]
    [int]$ParentPid,

    [Parameter(Mandatory=$true)]
    [string]$WorkspacePath
)

# Terminate parent OpenCode TUI process immediately
try {
    if (Get-Process -Id $ParentPid -ErrorAction SilentlyContinue) {
        Stop-Process -Id $ParentPid -Force
    }
} catch {
    # Process already exited or permission denied
}

# Relaunch opencode -c in workspace directory
try {
    if (Get-Command "wt.exe" -ErrorAction SilentlyContinue) {
        Start-Process -FilePath "wt.exe" -ArgumentList "opencode -c" -WorkingDirectory $WorkspacePath
    } else {
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "opencode -c" -WorkingDirectory $WorkspacePath
    }
} catch {
    Write-Error "Failed to relaunch OpenCode: $_"
}
