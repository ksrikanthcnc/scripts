$pswindow = (get-host).ui.rawui

#$newsize = $pswindow.buffersize
#$newsize.height = 3000
#$newsize.width = 150
#$pswindow.buffersize = $newsize
$newsize = $pswindow.windowsize
$newsize.height = 5
$newsize.width = 25
$pswindow.windowsize = $newsize

if ( [bool](get-job -Name pinger -ea silentlycontinue) )
{
    stop-job -name pinger
    receive-job -name pinger
}
$pinger = {
    $ms = 0
    while ($true){
        Test-Connection -ComputerName 8.8.8.8 -Quiet -OutVariable conn -Count 1 > $null
        if ($conn -eq $true){
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
$char = '.'
while ($true){
    $conn = Get-Job -Name pinger | Receive-Job
    if ($conn -eq $true){
        Write-Host '|'$count
        $char = '.'
        $count = 0
    }
    elseif ($conn -eq $false){
        Write-Host '[x]'$count
        $char = 'x'
        $count = 0
    }
    elseif ($conn -ne $null){
        Write-Host $conn
        $count = 0
    }
    Write-Host -NoNewline $char
    $count += 1
    Sleep -Milliseconds 100
}
