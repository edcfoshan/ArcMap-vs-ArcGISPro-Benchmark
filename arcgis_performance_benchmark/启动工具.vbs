' ArcGIS Python Benchmark GUI Launcher
' Run without showing CMD window

Dim WshShell, fso, strPath, strPython, strScript, cmd

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get script directory
strPath = fso.GetParentFolderName(WScript.ScriptFullName)

' Try ArcGIS Pro Python first
strPython = "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
strScript = strPath & "\benchmark_gui.py"

If fso.FileExists(strPython) Then
    ' Use ArcGIS Pro Python
    cmd = Chr(34) & strPython & Chr(34) & " " & Chr(34) & strScript & Chr(34)
Else
    ' Use system Python
    cmd = "python " & Chr(34) & strScript & Chr(34)
End If

' Run hidden (0 = hidden window)
WshShell.Run cmd, 0, False

Set WshShell = Nothing
Set fso = Nothing
