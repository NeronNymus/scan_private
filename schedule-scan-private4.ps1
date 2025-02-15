# Get the path to Python executable
$python_path = (Get-Command pythonw -ErrorAction SilentlyContinue).Definition

if (-not $python_path) {
    Write-Error "Pythonw.exe not found. Ensure Python is installed and in PATH."
    exit 1
}

# Define paths using Join-Path for better cross-platform compatibility
$batFilePath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup\private.bat"
$pythonScriptPath = "$HOME\Other\scan_private\scan_private5.py" -replace "/", "\"

# Create the .bat file with hidden execution if it doesn’t exist
if (-not (Test-Path $batFilePath)) {
    $batContent = "@echo off`nstart /b `"$python_path`" `"$pythonScriptPath`""
    $batContent | Set-Content -Path $batFilePath -Encoding UTF8
    Write-Output "Startup script created at: $batFilePath"
} else {
    Write-Output "Startup script already exists: $batFilePath"
}

# Run the Python script immediately in the background (hidden, no console)
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $python_path
$psi.Arguments = "`"$pythonScriptPath`""
$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$psi.CreateNoWindow = $true
$psi.UseShellExecute = $false

# Start the process and suppress output
[System.Diagnostics.Process]::Start($psi) | Out-Null
Write-Output "Python script executed in background."

