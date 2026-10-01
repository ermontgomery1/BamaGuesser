# Creates a Python virtual environment and installs dependencies.

$VenvPath = ".venv"

# Create the Python virtual environment
if (Test-Path $VenvPath) {
    Write-Host "Python virtual environment already exists."
}
else {
    Write-Host "Creating Python virtual environment..."
    python3 -m venv $VenvPath
}

# Install dependencies into the virtual environment
Write-Host "Installing Python dependencies..."
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

Write-Host ""
Write-Host "Setup complete."
Write-Host "Repository: $(Get-Location)"
Write-Host "Virtual environment: $(Join-Path (Get-Location) $VenvPath)"
Write-Host ""
Write-Host "To activate the environment, run:"
Write-Host ".\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "To exit the environment when finished, run:"
Write-Host "deactivate"
Write-Host ""
Write-Host "To start the program, run:"
Write-Host "python3 app.py"