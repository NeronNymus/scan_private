# Get the path to Python executable
$python_path = (Get-Command python).Definition

echo $python_path
