$pswindow = (get-host).ui.rawui

if ($true){
    $newsize = $pswindow.windowsize
    $newsize.height = 4
    $newsize.width = 30
    $pswindow.windowsize = $newsize

    $newsize = $pswindow.buffersize
    $newsize.height = 100
    $newsize.width = 30
    $pswindow.buffersize = $newsize
}

if ( [bool](get-job -Name pinger -ea silentlycontinue) )
{
    stop-job -name pinger
    receive-job -name pinger
}
$threshold = 1000
$pinger = {
    $ms = 0
    while ($true){
        Test-Connection -ComputerName 8.8.8.8 -Quiet -OutVariable conn -Count 1 > $null
        if ($conn -eq 1000){ #$threshold
            if ($ms -le 1000){ 
                $ms += 100
            }
        }
        elseif (!$conn){
            $ms = 0
        }
        elseif ($conn -ne $null){
            $ms = 0
        }
        Sleep -MilliSeconds $ms
        Write-Output $conn
    }
}

$job = Start-Job -Name 'pinger' -ScriptBlock $pinger
#Sleep -Seconds 1
#Debug-Job $job

$count = 0
$sleepms = 100
$char = '?'
while ($true){
    $conn = Get-Job -Name pinger | Receive-Job
    if ($conn -eq $true){
        #Write-Host '|'$count
        Write-Host 'ok'
        $char = '.'
    }
    elseif ($conn -eq $false){
        #Write-Host '[x]'$count
        Write-Host '[x]NA'
        $char = 'x'
    }
    elseif ($conn -ne $null){
        Write-Host $conn
    }

    if ($conn -ne $null){
        Write-Host -NoNewline 'Internet'
        $count = 0
    }
    Write-Host -NoNewline $char
    $count += 1
    Sleep -Milliseconds $sleepms
    if ($char -ne 'x'){
        if ($sleepms*$count -lt $threshold){
            $char = '.'
        }else{
            $char = '?'
        }
    }
}
