# This script already schedules with NoWindow

# Get the path to Python executable
$python_path = (Get-Command python).Definition

# Define the action
#$action = New-ScheduledTaskAction -Execute "$python_path" -Argument 'C:\Users\jesus\Other\scan_private\scan_private2.py'
$action = New-ScheduledTaskAction -Execute "Powershell.exe" `
    -Argument "-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -Command `"& '$python_path' 'C:\Users\jesus\Other\scan_private\scan_private3.py'`""


#$t1 = New-ScheduledTaskTrigger -Daily -At 13:00pm
$time = "13:00pm"
$t1 = New-ScheduledTaskTrigger -Daily -At "$time"
$t2 = New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Hours 24) -At "$time"
$t1.Repetition = $t2.Repetition
Register-ScheduledTask -Action $action -Trigger $t1 -TaskName "RunPrivate" -Force
