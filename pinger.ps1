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
    [Switch]$Help = $false,
#Text to display
    [string]$Text = "",
#Resize window
    [Switch]$ReSize = $false, 
#Beta features
    [Switch]$Beta = $false,
#TimeStamp
    [Switch]$Time = $false,
#Server addess to use
    [string]$Server = "8.8.8.8",
#Sleep MS between pings
    [int]$SleepMS = 1000,
#Sleep MS between '.' prints, only applicable if type if WhileTrue
    [string]$WhileSleepMS = 100,
#Len of array to use for getting average
    [int]$avgLen = 10,
#Round to ? for clean output, makes sense with full Verbose
    [int]$tabRound = 5,
#Avg to use 'Avg'/'Max'
    [ValidateSet("Avg","Max")]$Func = 'Avg',
#Type to display
    [ValidateSet("Avg","Ping","Both")]$Disp = 'Both',
#Len to convert '.' to ':'
    [int]$VerbLen = 50,
#'.'s and ':'s (Verbose)
    [ValidateSet(".",":",$false,$true)]$Verbose = $false,
#Short verbose char
    [string]$VerbChar = ":",
#Beep sound
    [Switch]$Beep = $false,
#Beep duration
    [int]$BeepDur = 100,
#Beep pitch
    [int]$BeepPitch = 500,
#Type to use
    [ValidateSet("Event","WhileTrue")]$Type = 'Event'
)

Write-Host ""
Write-Host "Exiting Previous ... " -NoNewline
stop-job -name pinger -ea SilentlyContinue
remove-job -name pinger -ea SilentlyContinue
Unregister-Event DataAdded -ea SilentlyContinue
Write-Host "Done"


if($help){
    Get-Help $PSCommandPath
    exit
}

Get-Variable -Include ('Help','Text','ReSize','Beta','Server','SleepMS','WhileSleepMS','avgLen','Disp','Verbose','Type')

if($type -ne 'WhileTrue' -and $PSBoundParameters.ContainsKey('WhileSleepMS')){
    Write-Host "WhileSleepMS applicable only if type is WhileTrue" -ForegroundColor Red
}

if($PSBoundParameters.ContainsKey('BeepDur') -or $PSBoundParameters.ContainsKey('BeepPitch')){
    $Beep = $true
}

if($Verbose -eq $true){$Verbose = ':'}
if($Text -eq ""){$Text = (Get-NetConnectionProfile).InterfaceAlias.SubString(0,5)}
try{
    $pswindow = (get-host).ui.rawui
    if ($ReSize){
        $newsize = $pswindow.windowsize
        $newsize.height = 4
        $newsize.width = 20
        $pswindow.windowsize = $newsize

        $newsize = $pswindow.buffersize
        $newsize.height = 100
        $newsize.width = 20
        $pswindow.buffersize = $newsize
    }

    $pinger = {
        while ($true){
            Test-Connection -ComputerName $args[0] -Count 1 2>&1
            if($args[1]-gt 0){
                Sleep -MilliSeconds $args[1]
            }
        }
    }

    $job = Start-Job -Name 'pinger' -ScriptBlock $pinger -ArgumentList $server,$sleepms
    $color = 'Yellow'
    $OriginalText = $Text

    function printPing($ping, $avg, $color = 'Green'){
        if($Time){
            $date = (Get-Date).TimeOfDay
            Write-Host -NoNewLine ("{0}:{1}:{2}" -f $date.Hours, $date.Minutes, $date.Seconds)
        }
        if($disp -eq 'Avg' -or $disp -eq 'Both'){
            $avg = "{0:F1}" -f $avg
            Write-Host -NoNewLine "{$avgLen`:$avg}" -ForegroundColor $color
            if($Verbose -ne $false){
                $char = '.'
                if([int]$avg -gt $VerbLen -and $Verbose -eq ':'){
                    $avg /= 10
                    $char = $VerbChar
                }
                Write-Host -NoNewLine "$($char*$([math]::Floor($avg)))" -ForegroundColor $color
                $spaces = $tabRound - [math]::Floor($avg) % $tabRound
                Write-Host -NoNewline $(" "*$spaces) -ForegroundColor $color
            }
        }
        if($disp -eq 'Ping' -or $disp -eq 'Both'){
            Write-Host -NoNewLine "($ping)" -ForegroundColor $color
            if($Verbose -ne $false){
                $char = '.'
                $correctedPing = $ping
                if($ping -gt $VerbLen -and $Verbose -eq ':'){
                    $correctedPing /= 10
                    $char = $VerbChar
                }
            }
            Write-Host -NoNewline $("$char"*$correctedPing) -ForegroundColor $color
        }
    }

    function IsVPN{
        ForEach($profile in Get-NetConnectionProfile){
            if(($profile.InterfaceAlias -ne 'Wi-Fi' -and $profile.IntefaceAlias -ne 'Ethernet') -and 
                $profile.IPv4Connectivity -eq 'Internet'){
                return $true
            }
        }
        return $false
    }

    $arr = 1..$avgLen
    $index = 0

    if($type -eq 'Event'){
        Register-ObjectEvent -InputObject $job.ChildJobs[0].Output -EventName 'DataAdded' -SourceIdentifier DataAdded
        Register-ObjectEvent -InputObject $job -EventName StateChanged

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
                            Write-Host "--------------------------$($eve.SourceIdentifier) Received"
    #                        break
                        }

                        $op = $job | Receive-Job #-ErrorVariable err -ErrorAction SilentlyContinue
                        ForEach($ping in $op){
                            if ($ping.ErrorCategory_Reason -eq $null){
                                $color = 'Green'

                                $arr[$index] = $ping.ResponseTime;
                                $index += 1;
                                if ($index -eq $arr.count){$index = 0;}
                                $avg = 0
                                if($Func -eq 'Avg'){
                                    ForEach($ele in $arr){$avg += $ele}
                                    $avg /= $arr.count
                                }elseif($Func -eq 'Max'){
                                    $avg = ($arr | measure -Maximum).Maximum
                                }

                                printPing $ping.ResponseTime $avg
                                if (IsVPN){
                                    $Text = "[$OriginalText]"
                                }else{
                                    $Text =$OriginalText
                                }
                                Write-Host "";Write-Host -NoNewline $Text -ForegroundColor $color
                                if ($Beep) {
                                    [console]::beep($BeepPitch,$BeepDur)
                                }
                            }else{
                                $color = 'Red'
                                Write-Host "[x]$($ping.ErrorCategory_Reason)" -NoNewline -ForegroundColor $color
                                Write-Host "";Write-Host -NoNewline $Text -ForegroundColor $color
                            }
                        }
                        $job.ChildJobs[0].Output.Clear()
         #           }
                }
        }
    }elseif($type -eq 'WhileTrue'){
        $count = 0
        $char = '?'
        while ($true){
            $op = $job | Receive-Job #-ErrorVariable err -ErrorAction SilentlyContinue
            ForEach($ping in $op){
                if ($ping.ErrorCategory_Reason -eq 'PingException'){
                    #Write-Host '[x]'$count
                    $color = 'Red'
                    Write-Host '[x]NA' -ForegroundColor $color
                    $char = 'x'
                }
                elseif ($ping.ResponseTime -gt 0){
                    #Write-Host '|'$count
                    $arr[$index] = $ping.ResponseTime;
                    $index += 1;
                    if ($index -eq $arr.count){$index = 0;}
                    $avg = 0
                    ForEach($ele in $arr){$avg += $ele}
                    $avg /= $arr.count

                    $color = 'Green'
                    printPing $ping.ResponseTime $avg
                    Write-Host ""
                    $char = '.'
                }
                elseif ($ping -ne $null){
                    Write-Host $conn
                }

                if ($ping -ne $null){
                    if (IsVPN){
                        $Text = "[$OriginalText]"
                    }else{
                        $Text =$OriginalText
                    }
                    Write-Host -NoNewline $Text -ForegroundColor $color
                    if ($Beep) {
                        [console]::beep($BeepPitch,$BeepDur)
                    }
                    $count = 0
                }
            }
            Write-Host -NoNewline $char -ForegroundColor Red
            $count += 1
            if($WhileSleepMS -gt 0){
                Sleep -Milliseconds $WhileSleepMS
            }
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
}
finally{
    Write-Host ""
    Write-Host "Exiting ... " -NoNewline
    stop-job -name pinger -ErrorAction Inquire
    remove-job -name pinger -ErrorAction Inquire
    Get-Event | Remove-Event
    if($Type -eq 'Event'){
        Unregister-Event DataAdded -ErrorAction Inquire
    }
    Write-Host "Done"
}