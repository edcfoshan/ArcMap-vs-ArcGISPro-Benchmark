Set WShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
ArcGISProPythonW = "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\pythonw.exe"
ArcGISProPython = "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
VenvPython = ScriptDir & "\venv\Scripts\pythonw.exe"
If FSO.FileExists(ArcGISProPythonW) Then
    PythonPath = ArcGISProPythonW
ElseIf FSO.FileExists(ArcGISProPython) Then
    PythonPath = ArcGISProPython
ElseIf FSO.FileExists(VenvPython) Then
    PythonPath = VenvPython
Else
    PythonPath = "pythonw"
End If
Cmd = """" & PythonPath & """ """ & ScriptDir & "\benchmark_gui_modern.py"""
WShell.Run Cmd, 0, False
Set WShell = Nothing
Set FSO = Nothing
