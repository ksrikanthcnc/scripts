Write-Output "...Connecting to broadband"
rasdial "Broadband Connection" "sudhakar" "123456"

Write-Output "...Starting netsh hotspot"
netsh wlan set hostednetwork mode=allow ssid=srika-lenovo key=passcode
netsh wlan start hostednetwork

Write-Output "...Sharing internet"
Write-Output "...dll"
regsvr32.exe /s hnetcfg.dll
$netShare = New-Object -ComObject HNetCfg.HNetShare

Write-Output "...src"
$src = $netshare.EnumEveryConnection | Where-Object {
    $netshare.NetConnectionProps($_).Name -eq "Broadband Connection"
}

Write-Output "...dest"
$dest = $netshare.EnumEveryConnection | Where-Object {
    $netshare.NetConnectionProps($_).Name -eq "Local Area Connection* 18"
}

Write-Output "...configs"
$srcConfig = $netShare.INetSharingConfigurationForINetConnection.Invoke($src)
$destConfig = $netShare.INetSharingConfigurationForINetConnection.Invoke($dest)

if (1){
    Write-Output "...Unsharing"

#    Write-Output "......dest"
#    $destConfig.DisableSharing()
#    Write-Output "done. press enter to continue execution"
#    pause

    Write-Output "......src"
    $srcConfig.DisableSharing()
    Write-Output "done. press enter to continue execution"
    pause
} 

Write-Output "...Re-Sharing"
Write-Output "......src"
$srcConfig.EnableSharing(0)
Write-Output "done. press enter to continue execution"
pause

Write-Output "......dest"
$destConfig.EnableSharing(1)
Write-Output "done. press enter to continue execution"
pause

Write-Output "...Enter to exit"
pause
