' Created by: Shawn Brink
' Created on: February 2nd 2016
' Tutorial: http://www.tenforums.com/tutorials/39548-desktop-background-file-location-context-menu-add-windows-8-10-a.html


Const HKCU = &H80000001 'HKEY_CURRENT_USER

sComputer = "."   

Set oReg=GetObject("winmgmts:{impersonationLevel=impersonate}!\\" _
            & sComputer & "\root\default:StdRegProv")

sKeyPath = "Control Panel\Desktop\"
sValueName = "TranscodedImageCache"
oReg.GetBinaryValue HKCU, sKeyPath, sValueName, sValue


sContents = ""

For i = 24 To UBound(sValue)
  vByte = sValue(i)
  If vByte <> 0 And vByte <> "" Then
    sContents = sContents & Chr(vByte)
  End If
Next

'CreateObject("Wscript.Shell").Run "explorer.exe /select,""" & sContents & """"
CreateObject("Wscript.Shell").Run sContents

strFile=sContents
s = Split(strFile,":")
WScript.Echo s(1)
