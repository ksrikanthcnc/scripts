<#
.SYNOPSIS
    Pings continuously to constantly monitor internet connection
.DESCRIPTION
    Pings continuously to constantly monitor internet connection
.PARAMETER Path
    The path to the .
.PARAMETER LiteralPath
    Specifies a path to one or more locations. Unlike Path, the value of 
    LiteralPath is used exactly as it is typed. No characters are interpreted 
    as wildcards. If the path includes escape characters, enclose it in single
    quotation marks. Single quotation marks tell Windows PowerShell not to 
    interpret any characters as escape sequences.
.EXAMPLE
    <scritp> -Server 8.8.8.8
.NOTES
    Author: Srikanth
    Date:   Mar 21, 2021
#>

param (
#Display help
    [Switch]$help = $false,
#Text to display
    [string]$Text = "Ping,",
#Resize window
    [Switch]$ReSize = $false, 
#Beta features
    [Switch]$Beta = $false,
#Server addess to use
    [string]$Server = "8.8.8.8",
#Sleep MS between pings
    [string]$SleepMS = 1000,
#Sleep MS between '.' prints, only applicable if type if WhileTrue
    [string]$WhileSleepMS = 100,
#Len of array to use for getting average
    [string]$avgLen = 10,
#Type to use
    [ValidateSet("Event","WhileTrue")]$type = 'Event'
)

if($help){
    Get-Help $PSCommandPath
    exit
}

if($type -ne 'WhileTrue' -and $PSBoundParameters.ContainsKey('WhileSleepMS')){
    Write-Host "WhileSleepMS applicable only if type is WhileTrue" -ForegroundColor Red
}

$pswindow = (get-host).ui.rawui
if ($ReSize){
    $newsize = $pswindow.windowsize
    $newsize.height = 4
    $newsize.width = 30
    $pswindow.windowsize = $newsize

    $newsize = $pswindow.buffersize
    $newsize.height = 100
    $newsize.width = 30
    $pswindow.buffersize = $newsize
}

stop-job -name pinger -ea SilentlyContinue
receive-job -name pinger -ea SilentlyContinue > $null
remove-job -name pinger -ea SilentlyContinue
Unregister-Event DataAdded -ErrorAction SilentlyContinue

$pinger = {
    while ($true){
        Test-Connection -ComputerName $args[0] -Count 1 -ErrorVariable err -WarningVariable warn -OutVariable out > $null
        if ($err -ne $null){Write-Output $err}
        else{Write-Output $out}
        Sleep -MilliSeconds $args[1]
    }
}

$job = Start-Job -Name 'pinger' -ScriptBlock $pinger -ArgumentList $server,$sleepms
$color = 'Yellow'
Write-Host "TYPE: [$type]" -ForegroundColor $color

if($type -eq 'Event'){
    Register-ObjectEvent -InputObject $job.ChildJobs[0].Output -EventName 'DataAdded' -SourceIdentifier DataAdded
    Register-ObjectEvent -InputObject $job -EventName StateChanged

    $arr = 1..$avgLen
    $index = 0

    Write-Host -NoNewline $Text -ForegroundColor $color
    while ($true)
    {
        Wait-Event |
    #        ? {  $_.SourceIdentifier -eq 'DataAdded' } |
            % {
    #            Get-Event |
    #            % {
                    $eve = $_
                    $eve | Remove-Event

                    if($eve.SourceIdentifier -ne 'DataAdded'){
                        break
                    }

                    $op = $job | Receive-Job -ErrorVariable err -ErrorAction SilentlyContinue
                    ForEach($ping in $op){
#                        if ($err[0].CategoryInfo.Reason -eq 'PingException'){
                        if ($ping.ErrorCategory_Reason -eq 'PingException'){
                            $color = 'Red'
                            Write-Host '[x]' -NoNewline -ForegroundColor $color
                            Write-Host "";Write-Host -NoNewline $Text -ForegroundColor $color
                        }else{
                            $arr[$index] = $ping.ResponseTime;
                            $index += 1;
                            if ($index -eq $arr.count){$index = 0;}

                            $avg = 0
                            ForEach($ele in $arr){$avg += $ele}
                            $avg /= $arr.count

                            $color = 'Green'
                            Write-Host -NoNewLine "[$($arr.count) avg:$avg $('.'*$avg)]" -ForegroundColor $color
                            Write-Host -NoNewLine "($($ping.ResponseTime))" -ForegroundColor $color
                            Write-Host -NoNewline $("."*$($ping.ResponseTime)) -ForegroundColor $color
                            Write-Host "";Write-Host -NoNewline $Text -ForegroundColor $color
                        }
                    }
                    $job.ChildJobs[0].Output.Clear()
     #           }
            }
    }
    if($Beta){
        stop-job -name pinger
        receive-job -name pinger
        Get-Event | Remove-Event
        Unregister-Event DataAdded
    }
}elseif($type -eq 'WhileTrue'){
    $count = 0
    $char = '?'
    while ($true){
        $op = $job | Receive-Job -ErrorVariable err -ErrorAction SilentlyContinue
        ForEach($ping in $op){
            if ($ping.ErrorCategory_Reason -eq 'PingException'){
                #Write-Host '[x]'$count
                $color = 'Red'
                Write-Host '[x]NA' -ForegroundColor $color
                $char = 'x'
            }
            elseif ($ping.ResponseTime -gt 0){
                #Write-Host '|'$count
                $color = 'Green'
                Write-Host 'ok'-ForegroundColor $color
                $char = '.'
            }
            elseif ($ping -ne $null){
                Write-Host $conn
            }

            if ($ping -ne $null){
                Write-Host -NoNewline $Text -ForegroundColor $color
                $count = 0
            }
        }
        Write-Host -NoNewline $char -ForegroundColor $color
        $count += 1
        Sleep -Milliseconds $WhileSleepMS
        if ($char -ne 'x'){
            if ([int]$WhileSleepMS*$count -lt $SleepMS){
                $char = '.'
            }else{
                $color = 'Yellow'
                $char = '?'
            }
        }
    }
}
else{
    Write-Host "Use type:'Event' or 'WhileTrue'" -ForegroundColor Red
}