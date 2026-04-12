Set WShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
DesktopPath = WShell.SpecialFolders("Desktop")
Set Shortcut = WShell.CreateShortcut(DesktopPath & "\ArcGIS Benchmark.lnk")
Shortcut.TargetPath = "wscript.exe"
Shortcut.Arguments = """" & ScriptDir & "\ArcGIS基准测试工具.vbs"""
Shortcut.WorkingDirectory = ScriptDir
Shortcut.Description = "ArcGIS Python2、3 与开源库性能对比测试工具"
Shortcut.IconLocation = ScriptDir & "\resources\icon.ico"
Shortcut.Save
MsgBox "桌面快捷方式已创建！", 64, "完成"
Set WShell = Nothing
Set FSO = Nothing
