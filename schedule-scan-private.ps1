# Get the path to Python executable
$python_path = (Get-Command python).Definition

# Define the action
$action = New-ScheduledTaskAction -Execute "$python_path" -Argument 'C:\Users\Public\Other\Schedule\schedule.py'

$t1 = New-ScheduledTaskTrigger -Daily -At 18:40pm
$t2 = New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Hours 1) -At 18:40pm
$t1.Repetition = $t2.Repetition
Register-ScheduledTask -Action $action -Trigger $t1 -TaskName "RunPrivate" -Force
